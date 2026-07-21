"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  PARTICIPANT_ROLES,
  type CaseTimeline as CaseTimelineData,
  type FieldSchemaEntry,
  type PublicFormView,
  type UploadedDocument,
  getPublicCaseTimeline,
  getPublicForm,
  listPublicDocuments,
  updatePublicForm,
  uploadPublicDocument,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { translateLabel } from "@/lib/formLabelTranslations";
import {
  buildDisplayItems,
  buildExclusiveCheckboxGroups,
  groupByPart,
  isFieldVisible,
  stripPartPrefix,
  stripSelectPrefix,
} from "@/lib/formFieldHelpers";
import { FieldRow } from "@/components/FieldRow";
import { CheckboxGroupField } from "@/components/CheckboxGroupField";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { CaseTimeline } from "@/components/CaseTimeline";

export default function ClientFormPage() {
  const params = useParams<{ token: string }>();
  const { t, lang } = useTranslation();

  const [view, setView] = useState<PublicFormView | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"loading" | "idle" | "saving" | "saved" | "error">("loading");
  const [isDirty, setIsDirty] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [resumed, setResumed] = useState(false);

  const [submitted, setSubmitted] = useState(false);
  const [timeline, setTimeline] = useState<CaseTimelineData | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [uploadRole, setUploadRole] = useState<string>(PARTICIPANT_ROLES[0]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    getPublicForm(params.token)
      .then((v) => {
        setView(v);
        setFormData(v.data);
        // The server remembers exactly which part the client was on (saved
        // on every Next/Previous) -- clamp only for safety in case the form
        // schema changed (fewer parts now) since they last saved.
        const partCount = groupByPart(v.fields.filter((f) => isFieldVisible(f, v.data))).length;
        const resumeAt = Math.max(0, Math.min(v.client_wizard_step, partCount - 1));
        setStepIndex(resumeAt);
        setResumed(resumeAt > 0);
        setStatus("idle");
      })
      .catch(() => setStatus("error"));

    listPublicDocuments(params.token)
      .then(setDocuments)
      .catch(() => setDocuments([]));

    getPublicCaseTimeline(params.token)
      .then(setTimeline)
      .catch(() => setTimeline(null));
  }, [params.token]);

  const visibleFieldsAll = useMemo(
    () => (view ? view.fields.filter((f: FieldSchemaEntry) => isFieldVisible(f, formData)) : []),
    [view, formData]
  );
  const parts = useMemo(() => groupByPart(visibleFieldsAll), [visibleFieldsAll]);
  const exclusiveCheckboxGroups = useMemo(() => (view ? buildExclusiveCheckboxGroups(view.fields) : new Map()), [view]);

  // A part can vanish (a show_if condition hid all its fields) between
  // renders -- clamp at render time instead of a blank page or an effect
  // that just re-triggers another render to fix the same thing.
  const currentStepIndex = parts.length > 0 ? Math.min(stepIndex, parts.length - 1) : 0;

  const progress = useMemo(() => {
    const fillable = visibleFieldsAll.filter((f) => f.type !== "checkbox");
    const filled = fillable.filter((f) => (formData[f.name] ?? "") !== "").length;
    return { filled, total: fillable.length };
  }, [visibleFieldsAll, formData]);

  function displayLabel(label: string): string {
    return lang === "es" ? translateLabel(label) : label;
  }

  const setFieldValue = useCallback(
    (name: string, value: string) => {
      setFormData((prev) => {
        const next = { ...prev, [name]: value };
        if (value !== "") {
          for (const sibling of exclusiveCheckboxGroups.get(name) ?? []) {
            next[sibling] = "";
          }
        }
        return next;
      });
      setIsDirty(true);
      setResumed(false);
    },
    [exclusiveCheckboxGroups]
  );

  // Nothing here can intercept a Next.js client-side nav (there isn't one on
  // this page), but it does cover tab close, refresh, and typing a new URL --
  // the same cases as the internal editor at forms/[id]/page.tsx.
  useEffect(() => {
    if (!isDirty) return;
    function handler(e: BeforeUnloadEvent) {
      e.preventDefault();
    }
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  // Shared by the manual Guardar button and the auto-save that fires when
  // moving between parts -- returns whether it succeeded so callers can
  // decide whether it's safe to advance the step. `stepToPersist` is saved
  // alongside the data so a client who closes the tab right after Next/
  // Previous resumes at the part they landed on, not the one they left.
  async function saveData(stepToPersist: number = currentStepIndex): Promise<boolean> {
    if (!view) return false;
    setStatus("saving");
    try {
      const sanitized = { ...formData };
      for (const field of view.fields) {
        if (!isFieldVisible(field, formData)) sanitized[field.name] = "";
      }
      const updated = await updatePublicForm(params.token, sanitized, stepToPersist);
      setFormData(updated.data);
      setIsDirty(false);
      setStatus("saved");
      return true;
    } catch {
      setStatus("error");
      return false;
    }
  }

  async function handleNext() {
    const nextStep = Math.min(currentStepIndex + 1, parts.length - 1);
    const ok = await saveData(nextStep);
    if (ok) {
      setStepIndex(nextStep);
      setResumed(false);
    }
  }

  async function handlePrevious() {
    // Save on the way back too -- otherwise a client who fills a field, then
    // goes back to check something earlier, and closes the tab loses that edit.
    const prevStep = Math.max(currentStepIndex - 1, 0);
    await saveData(prevStep);
    setStepIndex(prevStep);
    setResumed(false);
  }

  const ALLOWED_MIME = ["application/pdf", "image/jpeg", "image/png"];
  const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // 10 MB

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = e.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError(t("client.documents.error.size"));
      return;
    }
    if (!ALLOWED_MIME.includes(file.type)) {
      setUploadError(t("client.documents.error.type"));
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const doc = await uploadPublicDocument(params.token, file, uploadRole);
      setDocuments((prev) => [doc, ...prev]);
      input.value = "";
    } catch {
      setUploadError(t("client.documents.error"));
    } finally {
      setUploading(false);
    }
  }

  function handleRemoveDocument(id: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  async function handleFinalize() {
    // Deliberately not gated on every visible field being filled: this
    // app's field_schema has no real "required" flag (whether a USCIS field
    // applies depends on the applicant's own situation), so a blanket
    // "every field must be non-empty" check ends up requiring things like
    // attorney-only fields (already silently stripped server-side) and
    // "use this space for extra explanation if needed" continuation
    // fields that almost never apply -- which made every multi-part form
    // impossible to finish from the client's side. The attorney/paralegal
    // reviews the filled form before it's ever filed, same as everywhere
    // else in this app.
    const ok = await saveData();
    if (ok) setSubmitted(true);
  }

  if (status === "loading") {
    return <div className="p-8 text-center text-zinc-600 dark:text-zinc-400">{t("client.loading")}</div>;
  }

  if (status === "error" && !view) {
    return <div className="p-8 text-center text-red-700 dark:text-red-300">{t("client.error.load")}</div>;
  }

  if (!view) return null;

  // Submitted confirmation screen
  if (submitted) {
    return (
      <div className="min-h-screen bg-zinc-50 p-6 dark:bg-black">
        <LanguageSwitcher />
        <div className="mx-auto flex max-w-md flex-col items-center gap-4 pt-24 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-950">
            <svg className="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">{t("client.submitted.title")}</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{t("client.submitted.subtitle")}</p>
        </div>
      </div>
    );
  }

  const [currentPartLabel, currentPartFields] = parts[currentStepIndex] ?? ["", []];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === parts.length - 1;

  return (
    <div className="min-h-screen bg-zinc-50 p-6 dark:bg-black">
      <LanguageSwitcher />
      <div className="mx-auto max-w-2xl">
        <h1 className="text-xl font-semibold text-black dark:text-zinc-50">
          {view.form_code} — {view.form_name}
        </h1>
        <p className="mb-1 text-sm text-zinc-500">{view.case_number}</p>
        <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">{t("client.subtitle")}</p>

        {timeline && (
          <div className="mb-6 overflow-x-auto rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="mb-3 text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("client.timeline.title")}</h2>
            <CaseTimeline timeline={timeline} />
          </div>
        )}

        <div className="mb-6 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="mb-3 flex items-center justify-between gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              {t("client.step.part")} {currentStepIndex + 1} {t("editor.of")} {parts.length}
            </span>
            <span className="text-xs text-zinc-500">
              {progress.filled} / {progress.total} {t("editor.progress")}
            </span>
          </div>
          <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <div
              className="h-full rounded-full bg-black transition-all dark:bg-zinc-50"
              style={{ width: `${progress.total > 0 ? (progress.filled / progress.total) * 100 : 0}%` }}
            />
          </div>

          {resumed && (
            <p className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-300">
              {t("client.step.resumed")}
            </p>
          )}

          <h3 className="mb-3 text-base font-semibold text-zinc-900 dark:text-zinc-50">
            {displayLabel(currentPartLabel)}
          </h3>
          <div className="space-y-3">
            {buildDisplayItems(currentPartFields).map((item) =>
              item.kind === "checkbox-group" ? (
                <CheckboxGroupField
                  key={item.options[0].field.name}
                  question={displayLabel(item.question)}
                  options={item.options.map((opt) => ({
                    field: opt.field,
                    label: stripSelectPrefix(displayLabel(opt.optionClause)),
                    checked: (formData[opt.field.name] ?? "") !== "",
                  }))}
                  onChange={setFieldValue}
                />
              ) : (
                <FieldRow
                  key={item.field.name}
                  field={item.field}
                  value={formData[item.field.name] ?? ""}
                  label={displayLabel(stripPartPrefix(item.field.label))}
                  onChange={setFieldValue}
                  // Not marked required -- see handleFinalize for why: this
                  // app has no way to know which fields actually apply to a
                  // given applicant, so a blanket asterisk here would be
                  // misleading (e.g. attorney-only fields, or "use this
                  // space if you need it" continuation fields).
                />
              )
            )}
          </div>

          <div className="mt-5 flex items-center gap-3 border-t border-zinc-100 pt-4 dark:border-zinc-800">
            <button
              type="button"
              onClick={handlePrevious}
              disabled={isFirstStep || status === "saving"}
              className="min-h-11 rounded-md border border-zinc-300 px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              {t("client.step.previous")}
            </button>
            {isLastStep ? (
              <button
                type="button"
                onClick={handleFinalize}
                disabled={status === "saving"}
                className="ml-auto min-h-11 rounded-md bg-black px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
              >
                {status === "saving" ? t("client.saving") : t("client.step.finish")}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleNext}
                disabled={status === "saving"}
                className="ml-auto min-h-11 rounded-md bg-black px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
              >
                {status === "saving" ? t("client.saving") : t("client.step.next")}
              </button>
            )}
          </div>
        </div>

        {status === "saved" && !isDirty && (
          <p className="mb-6 -mt-4 text-center text-sm text-green-700 dark:text-green-400">{t("client.saved")}</p>
        )}
        {isDirty && status !== "saving" && (
          <p className="mb-6 -mt-4 flex items-center justify-center gap-1.5 text-center text-sm text-amber-700 dark:text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" aria-hidden="true" />
            {t("editor.unsaved")}
          </p>
        )}
        {status === "error" && (
          <p className="mb-6 -mt-4 text-center text-sm text-red-700 dark:text-red-300">{t("client.error.save")}</p>
        )}

        {/* Step dots -- jumping directly to an already-visited part is handy
            for double-checking an earlier answer without paging back one at
            a time. Only past/current steps are clickable; future ones are
            reached by actually going through Next so nothing gets skipped. */}
        <div className="mb-6 flex flex-wrap justify-center gap-1.5" role="tablist" aria-label={t("client.step.part")}>
          {parts.map(([partLabel], idx) => (
            <button
              key={partLabel}
              type="button"
              role="tab"
              aria-selected={idx === currentStepIndex}
              aria-label={`${t("client.step.part")} ${idx + 1}`}
              disabled={idx > currentStepIndex}
              onClick={() => {
                setStepIndex(idx);
                setResumed(false);
                void saveData(idx);
              }}
              className="flex min-h-11 min-w-11 items-center justify-center rounded-full transition disabled:cursor-not-allowed"
            >
              <span
                className={`block h-2.5 w-2.5 rounded-full ${
                  idx === currentStepIndex
                    ? "bg-black dark:bg-zinc-50"
                    : idx < currentStepIndex
                      ? "bg-zinc-400 hover:bg-zinc-500 dark:bg-zinc-600"
                      : "bg-zinc-200 dark:bg-zinc-800"
                }`}
              />
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-1 text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("client.documents")}</h2>
          <p className="mb-3 text-xs text-zinc-500">{t("client.documents.hint")}</p>

          <form onSubmit={handleUpload} className="mb-4 space-y-2">
            <div className="flex flex-wrap gap-2">
              <label className="flex flex-col text-sm text-zinc-500 dark:text-zinc-400">
                {t("client.documents.role")}
                <select
                  value={uploadRole}
                  onChange={(e) => setUploadRole(e.target.value)}
                  className="mt-1 min-h-11 rounded-md border border-zinc-300 bg-white p-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                >
                  {PARTICIPANT_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {t(`enum.participantRole.${r}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex min-w-0 flex-1 flex-col text-sm text-zinc-500 dark:text-zinc-400">
                {t("documents.field.file")}
                <input
                  name="file"
                  type="file"
                  required
                  accept=".pdf,.jpg,.jpeg,.png"
                  aria-describedby="upload-formats-hint"
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white p-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                />
              </label>
            </div>
            <p id="upload-formats-hint" className="text-xs text-zinc-400 dark:text-zinc-500">
              {t("client.documents.allowedFormats")}
            </p>
            <button
              type="submit"
              disabled={uploading}
              className="min-h-11 rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              {uploading ? t("client.documents.uploading") : t("client.documents.upload")}
            </button>
            {uploadError && (
              <p role="alert" className="text-sm text-red-700 dark:text-red-300">{uploadError}</p>
            )}
          </form>

          {documents.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("client.documents.empty")}</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-2">
                  <span className="min-w-0 truncate text-sm text-zinc-700 dark:text-zinc-300">{d.original_filename}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveDocument(d.id)}
                    aria-label={`${t("client.documents.remove")}: ${d.original_filename}`}
                    className="shrink-0 rounded p-1 text-xs text-zinc-400 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 dark:hover:text-red-400"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
