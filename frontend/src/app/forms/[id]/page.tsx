"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  type FieldSchemaEntry,
  type GeneratedFormDetail,
  checkUscisStatus,
  clientLinkUrl,
  downloadGeneratedForm,
  getAiStatus,
  getFormTemplateSchema,
  getGeneratedForm,
  getUscisApiStatus,
  reviewGeneratedForm,
  setReceiptNumber,
  updateGeneratedForm,
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
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const SEVERITY_CLASSES: Record<string, string> = {
  high: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
  medium: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
};

export default function GeneratedFormEditPage() {
  const params = useParams<{ id: string }>();
  const { t, lang } = useTranslation();
  const [detail, setDetail] = useState<GeneratedFormDetail | null>(null);
  const [fields, setFields] = useState<FieldSchemaEntry[]>([]);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"idle" | "loading" | "saving" | "saved" | "error">("loading");
  const [isDirty, setIsDirty] = useState(false);
  const [openParts, setOpenParts] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [showTranslation, setShowTranslation] = useState(lang === "es");
  const [linkCopied, setLinkCopied] = useState(false);
  const [aiConfigured, setAiConfigured] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [reviewError, setReviewError] = useState(false);
  const [uscisConfigured, setUscisConfigured] = useState(false);
  const [receiptInput, setReceiptInput] = useState("");
  const [savingReceipt, setSavingReceipt] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [uscisError, setUscisError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(false);

  useEffect(() => {
    getGeneratedForm(params.id)
      .then(async (d) => {
        setDetail(d);
        setFormData(d.data);
        setReceiptInput(d.uscis_receipt_number ?? "");
        const schema = await getFormTemplateSchema(d.form_code);
        setFields(schema.fields);
        if (schema.fields.length > 0) {
          setOpenParts(new Set(groupByPart(schema.fields).slice(0, 1).map(([p]) => p)));
        }
        setStatus("idle");
      })
      .catch(() => setStatus("error"));
    getAiStatus()
      .then((s) => setAiConfigured(s.configured))
      .catch(() => setAiConfigured(false));
    getUscisApiStatus()
      .then((s) => setUscisConfigured(s.configured))
      .catch(() => setUscisConfigured(false));
  }, [params.id]);

  function displayLabel(label: string): string {
    return showTranslation ? translateLabel(label) : label;
  }

  const visibleFieldsAll = useMemo(
    () => fields.filter((f) => isFieldVisible(f, formData)),
    [fields, formData]
  );

  const parts = useMemo(() => groupByPart(visibleFieldsAll), [visibleFieldsAll]);

  // "Select only one box" clusters (relationship type, sex, eye color, ...) --
  // checking one should uncheck its siblings, otherwise the PDF can end up
  // with two mutually exclusive boxes both checked. See formFieldHelpers.ts.
  const exclusiveCheckboxGroups = useMemo(() => buildExclusiveCheckboxGroups(fields), [fields]);

  const progress = useMemo(() => {
    const fillable = visibleFieldsAll.filter((f) => f.type !== "checkbox");
    const filled = fillable.filter((f) => (formData[f.name] ?? "") !== "").length;
    return { filled, total: fillable.length };
  }, [visibleFieldsAll, formData]);

  const query = search.trim().toLowerCase();
  const isSearching = query.length > 0;

  function togglePart(part: string) {
    setOpenParts((prev) => {
      const next = new Set(prev);
      if (next.has(part)) next.delete(part);
      else next.add(part);
      return next;
    });
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
    },
    [exclusiveCheckboxGroups]
  );

  // Covers tab close, refresh, and typing a new URL -- the one case this
  // can't cover is Next.js client-side navigation (the "Volver" link),
  // which is guarded separately below since beforeunload doesn't fire for it.
  useEffect(() => {
    if (!isDirty) return;
    function handler(e: BeforeUnloadEvent) {
      e.preventDefault();
    }
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  const isSavingRef = useRef(false);

  async function handleSave() {
    if (isSavingRef.current) return;
    isSavingRef.current = true;
    setStatus("saving");
    try {
      // Clear answers for fields that are currently hidden by a show_if
      // condition, so changing your mind (e.g. unchecking "Child") doesn't
      // leave a stale, contradictory answer baked into the PDF.
      const sanitized = { ...formData };
      for (const field of fields) {
        if (!isFieldVisible(field, formData)) {
          sanitized[field.name] = "";
        }
      }
      await updateGeneratedForm(params.id, sanitized);
      setFormData(sanitized);
      setIsDirty(false);
      setStatus("saved");
    } catch {
      setStatus("error");
    } finally {
      isSavingRef.current = false;
    }
  }

  // Autosave, debounced -- mirrors the client portal's save-per-step, but
  // this editor is one continuous form rather than a wizard, so it saves
  // shortly after the user stops typing instead of on a "next" click. This
  // is what actually closes the "no autosave in the internal editor" gap:
  // by the time anyone could navigate away, the save has usually already
  // gone out, so the beforeunload/Volver guards above are a backstop for
  // the ~1.5s window, not the primary defense.
  useEffect(() => {
    if (!isDirty) return;
    const timer = setTimeout(() => {
      handleSave();
    }, 1500);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleSave closes over formData/fields, already covered by this effect's own deps
  }, [formData, isDirty]);

  function handleBackClick(e: React.MouseEvent) {
    if (isDirty && !window.confirm(t("editor.confirmLeave"))) {
      e.preventDefault();
    }
  }

  async function handleReview() {
    setReviewing(true);
    setReviewError(false);
    try {
      const updated = await reviewGeneratedForm(params.id);
      setDetail(updated);
    } catch {
      setReviewError(true);
    } finally {
      setReviewing(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setDownloadError(false);
    try {
      await downloadGeneratedForm(params.id, `${detail?.form_code ?? "form"}.pdf`);
    } catch {
      setDownloadError(true);
    } finally {
      setDownloading(false);
    }
  }

  async function handleCopyLink() {
    if (!detail) return;
    await navigator.clipboard.writeText(clientLinkUrl(detail.access_token));
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  }

  async function handleSaveReceipt() {
    setSavingReceipt(true);
    setUscisError(null);
    try {
      const updated = await setReceiptNumber(params.id, receiptInput.trim() || null);
      setDetail((prev) => (prev ? { ...prev, ...updated, uscis_status_raw: null } : prev));
      setReceiptInput(updated.uscis_receipt_number ?? "");
    } catch {
      setUscisError(t("uscis.error.save"));
    } finally {
      setSavingReceipt(false);
    }
  }

  async function handleCheckStatus() {
    setCheckingStatus(true);
    setUscisError(null);
    try {
      const updated = await checkUscisStatus(params.id);
      setDetail(updated);
    } catch {
      setUscisError(t("uscis.error.check"));
    } finally {
      setCheckingStatus(false);
    }
  }

  if (status === "loading") {
    return (
      <AppShell>
        <div className="text-zinc-500 dark:text-zinc-400">{t("editor.loading")}</div>
      </AppShell>
    );
  }

  if (status === "error" && !detail) {
    return (
      <AppShell>
        <div className="text-red-700 dark:text-red-300">{t("editor.error.load")}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              {detail?.form_code} — {t("editor.title")}
            </h1>
            <p className="text-sm text-zinc-500">
              {progress.filled} / {progress.total} {t("editor.progress")}
            </p>
          </div>
          <Link
            href="/forms"
            onClick={handleBackClick}
            className="text-sm text-zinc-500 hover:underline dark:text-zinc-400"
          >
            {t("nav.back")}
          </Link>
        </div>

        <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className="h-full rounded-full bg-indigo-600 transition-all"
            style={{ width: `${progress.total > 0 ? (progress.filled / progress.total) * 100 : 0}%` }}
          />
        </div>

        <Card className="mb-6 flex items-center gap-3 p-4">
          <Button onClick={handleSave} disabled={status === "saving"}>
            {status === "saving" ? t("editor.saving") : t("editor.save")}
          </Button>
          {status === "saved" && !isDirty && (
            <span className="text-sm text-emerald-700 dark:text-emerald-400">{t("editor.saved")}</span>
          )}
          {isDirty && status !== "saving" && (
            <span className="flex items-center gap-1.5 text-sm text-amber-700 dark:text-amber-400">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" aria-hidden="true" />
              {t("editor.unsaved")}
            </span>
          )}
          {status === "error" && detail && (
            <span className="text-sm text-red-700 dark:text-red-300">{t("editor.error.save")}</span>
          )}
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="ml-auto text-sm font-medium text-indigo-600 hover:underline disabled:opacity-50 dark:text-indigo-400"
          >
            {downloading ? t("editor.downloading") : t("editor.download")}
          </button>
        </Card>
        {downloadError && (
          <p className="-mt-4 mb-6 text-sm text-red-700 dark:text-red-300">{t("editor.error.download")}</p>
        )}

        {detail && (
          <Card className="mb-6 p-4">
            <h2 className="mb-1 text-sm font-medium text-zinc-800 dark:text-zinc-200">
              {t("editor.clientLink")}
            </h2>
            <p className="mb-2 text-xs text-zinc-500">{t("editor.clientLinkHint")}</p>
            <div className="flex items-center gap-2">
              <input
                readOnly
                value={clientLinkUrl(detail.access_token)}
                onFocus={(e) => e.currentTarget.select()}
                className="w-full rounded-lg border border-zinc-300 bg-zinc-50 p-2 text-xs text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400"
              />
              <Button onClick={handleCopyLink} variant="secondary" className="whitespace-nowrap py-2 text-xs">
                {linkCopied ? t("editor.linkCopied") : t("editor.copyLink")}
              </Button>
            </div>
          </Card>
        )}

        {detail && (
          <Card className="mb-6 p-4">
            <h2 className="mb-1 text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("uscis.title")}</h2>
            {!uscisConfigured && <p className="mb-2 text-xs text-zinc-500">{t("uscis.offline")}</p>}
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <label htmlFor="uscis-receipt" className="sr-only">
                {t("uscis.receiptLabel")}
              </label>
              <input
                id="uscis-receipt"
                type="text"
                placeholder={t("uscis.receiptPlaceholder")}
                value={receiptInput}
                onChange={(e) => setReceiptInput(e.target.value)}
                maxLength={20}
                className="w-48 rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950"
              />
              <Button
                onClick={handleSaveReceipt}
                disabled={savingReceipt || receiptInput.trim() === (detail.uscis_receipt_number ?? "")}
                variant="secondary"
                className="text-xs"
              >
                {savingReceipt ? t("uscis.saving") : t("uscis.save")}
              </Button>
              {uscisConfigured && (
                <Button
                  onClick={handleCheckStatus}
                  disabled={checkingStatus || !detail.uscis_receipt_number}
                  className="text-xs"
                >
                  {checkingStatus ? t("uscis.checking") : t("uscis.checkStatus")}
                </Button>
              )}
            </div>
            {uscisError && <p className="mb-2 text-xs text-red-700 dark:text-red-300">{uscisError}</p>}
            {detail.uscis_status_raw && (
              <div className="rounded-lg bg-zinc-50 p-3 text-sm dark:bg-zinc-800/50">
                <p className="font-medium text-zinc-800 dark:text-zinc-200">
                  {lang === "es"
                    ? detail.uscis_status_raw.case_status.current_case_status_text_es
                    : detail.uscis_status_raw.case_status.current_case_status_text_en}
                </p>
                <p className="mt-1 text-zinc-600 dark:text-zinc-400">
                  {lang === "es"
                    ? detail.uscis_status_raw.case_status.current_case_status_desc_es
                    : detail.uscis_status_raw.case_status.current_case_status_desc_en}
                </p>
                {(detail.uscis_status_raw.case_status.hist_case_status?.length ?? 0) > 0 && (
                  <ul className="mt-3 space-y-1 border-t border-zinc-200 pt-2 text-xs text-zinc-500 dark:border-zinc-700">
                    {detail.uscis_status_raw.case_status.hist_case_status!.map((h, i) => (
                      <li key={i}>
                        {h.date} — {lang === "es" ? h.completed_text_es : h.completed_text_en}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            {detail.uscis_status_checked_at && (
              <p className="mt-2 text-xs text-zinc-400">
                {t("uscis.lastChecked")}: {new Date(detail.uscis_status_checked_at).toLocaleString()}
              </p>
            )}
          </Card>
        )}

        <Card className="mb-6 p-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <h2 className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("editor.review.title")}</h2>
            {aiConfigured && (
              <Button onClick={handleReview} disabled={reviewing} variant="secondary" className="text-xs">
                {reviewing ? t("editor.reviewing") : t("editor.review")}
              </Button>
            )}
          </div>
          {!aiConfigured && <p className="text-xs text-zinc-500">{t("editor.review.offline")}</p>}
          {reviewError && (
            <p className="mb-2 text-xs text-red-700 dark:text-red-300">{t("editor.review.error")}</p>
          )}
          {detail?.ai_review && (
            <div>
              <p className="mb-1 text-xs italic text-zinc-500">{t("editor.review.disclaimer")}</p>
              <p className="mb-3 text-sm text-zinc-700 dark:text-zinc-300">{detail.ai_review.overall_assessment}</p>
              {detail.ai_review.findings.length === 0 ? (
                <p className="text-sm text-zinc-500">{t("editor.review.empty")}</p>
              ) : (
                <ul className="space-y-2">
                  {detail.ai_review.findings.map((finding, i) => (
                    <li key={i} className="rounded-lg bg-zinc-50 p-3 text-sm dark:bg-zinc-800/50">
                      <div className="mb-1 flex items-center gap-2">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_CLASSES[finding.severity] ?? SEVERITY_CLASSES.low}`}
                        >
                          {t(`editor.review.severity.${finding.severity}` as Parameters<typeof t>[0])}
                        </span>
                        <span className="font-medium text-zinc-800 dark:text-zinc-200">{finding.field_label}</span>
                      </div>
                      <p className="text-zinc-600 dark:text-zinc-400">{finding.issue}</p>
                    </li>
                  ))}
                </ul>
              )}
              {detail.ai_reviewed_at && (
                <p className="mt-2 text-xs text-zinc-400">
                  {t("editor.review.lastRun")}: {new Date(detail.ai_reviewed_at).toLocaleString()}
                </p>
              )}
            </div>
          )}
        </Card>

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <input
            type="text"
            aria-label={t("editor.search")}
            placeholder={t("editor.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="min-w-0 flex-1 rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950"
          />
          <Button onClick={() => setShowTranslation((s) => !s)} variant="secondary" className="whitespace-nowrap text-xs">
            {showTranslation ? t("editor.showEnglish") : t("editor.showSpanish")}
          </Button>
        </div>

        {showTranslation && (
          <p className="mb-4 rounded-lg bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-300">
            {t("editor.translationNotice")}
          </p>
        )}

        <div className="space-y-2">
          {parts.map(([partLabel, partFields]) => {
            const visibleFields = isSearching
              ? partFields.filter((f) => f.label.toLowerCase().includes(query))
              : partFields;
            if (isSearching && visibleFields.length === 0) return null;

            const isOpen = isSearching || openParts.has(partLabel);

            return (
              <details
                key={partLabel}
                open={isOpen}
                onToggle={(e) => {
                  if (!isSearching && e.currentTarget.open !== openParts.has(partLabel)) {
                    togglePart(partLabel);
                  }
                }}
                className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
              >
                <summary className="cursor-pointer select-none p-3 text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  {displayLabel(partLabel)} ({visibleFields.length}
                  {isSearching && visibleFields.length !== partFields.length ? ` ${t("editor.of")} ${partFields.length}` : ""}{" "}
                  {t("editor.fields")})
                </summary>
                <div className="space-y-3 border-t border-zinc-100 p-4 dark:border-zinc-800">
                  {buildDisplayItems(visibleFields).map((item) =>
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
                      />
                    )
                  )}
                </div>
              </details>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
