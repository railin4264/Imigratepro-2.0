"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  PARTICIPANT_ROLES,
  type FieldSchemaEntry,
  type PublicFormView,
  type UploadedDocument,
  getPublicForm,
  listPublicDocuments,
  updatePublicForm,
  uploadPublicDocument,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { translateLabel } from "@/lib/formLabelTranslations";
import { groupByPart, isFieldVisible } from "@/lib/formFieldHelpers";
import { FieldRow } from "@/components/FieldRow";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function ClientFormPage() {
  const params = useParams<{ token: string }>();
  const { t, lang } = useTranslation();

  const [view, setView] = useState<PublicFormView | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"loading" | "idle" | "saving" | "saved" | "error">("loading");
  const [openParts, setOpenParts] = useState<Set<string>>(new Set());

  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [uploadRole, setUploadRole] = useState<string>(PARTICIPANT_ROLES[0]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    getPublicForm(params.token)
      .then((v) => {
        setView(v);
        setFormData(v.data);
        if (v.fields.length > 0) {
          setOpenParts(new Set(groupByPart(v.fields).slice(0, 1).map(([p]) => p)));
        }
        setStatus("idle");
      })
      .catch(() => setStatus("error"));

    listPublicDocuments(params.token)
      .then(setDocuments)
      .catch(() => setDocuments([]));
  }, [params.token]);

  const visibleFieldsAll = useMemo(
    () => (view ? view.fields.filter((f: FieldSchemaEntry) => isFieldVisible(f, formData)) : []),
    [view, formData]
  );
  const parts = useMemo(() => groupByPart(visibleFieldsAll), [visibleFieldsAll]);

  function displayLabel(label: string): string {
    return lang === "es" ? translateLabel(label) : label;
  }

  function togglePart(part: string) {
    setOpenParts((prev) => {
      const next = new Set(prev);
      if (next.has(part)) next.delete(part);
      else next.add(part);
      return next;
    });
  }

  const setFieldValue = useCallback((name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  }, []);

  async function handleSave() {
    if (!view) return;
    setStatus("saving");
    try {
      const sanitized = { ...formData };
      for (const field of view.fields) {
        if (!isFieldVisible(field, formData)) sanitized[field.name] = "";
      }
      const updated = await updatePublicForm(params.token, sanitized);
      setFormData(updated.data);
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = e.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

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

  if (status === "loading") {
    return <div className="p-8 text-center text-zinc-600 dark:text-zinc-400">{t("client.loading")}</div>;
  }

  if (status === "error" && !view) {
    return <div className="p-8 text-center text-red-700 dark:text-red-300">{t("client.error.load")}</div>;
  }

  if (!view) return null;

  return (
    <div className="min-h-screen bg-zinc-50 p-6 dark:bg-black">
      <LanguageSwitcher />
      <div className="mx-auto max-w-2xl">
        <h1 className="text-xl font-semibold text-black dark:text-zinc-50">
          {view.form_code} — {view.form_name}
        </h1>
        <p className="mb-1 text-sm text-zinc-500">{view.case_number}</p>
        <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">{t("client.subtitle")}</p>

        <div className="mb-6 space-y-2">
          {parts.map(([partLabel, partFields]) => {
            const isOpen = openParts.has(partLabel);
            return (
              <details
                key={partLabel}
                open={isOpen}
                onToggle={(e) => {
                  if (e.currentTarget.open !== openParts.has(partLabel)) togglePart(partLabel);
                }}
                className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
              >
                <summary className="cursor-pointer select-none p-3 text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  {displayLabel(partLabel)}
                </summary>
                <div className="space-y-3 border-t border-zinc-100 p-4 dark:border-zinc-800">
                  {partFields.map((field) => (
                    <FieldRow
                      key={field.name}
                      field={field}
                      value={formData[field.name] ?? ""}
                      label={displayLabel(field.label)}
                      onChange={setFieldValue}
                    />
                  ))}
                </div>
              </details>
            );
          })}
        </div>

        <div className="mb-6 flex items-center gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <button
            onClick={handleSave}
            disabled={status === "saving"}
            className="w-full rounded-md bg-black px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
          >
            {status === "saving" ? t("client.saving") : t("client.save")}
          </button>
        </div>
        {status === "saved" && (
          <p className="mb-6 -mt-4 text-center text-sm text-green-700 dark:text-green-400">{t("client.saved")}</p>
        )}
        {status === "error" && (
          <p className="mb-6 -mt-4 text-center text-sm text-red-700 dark:text-red-300">{t("client.error.save")}</p>
        )}

        <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-1 text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("client.documents")}</h2>
          <p className="mb-3 text-xs text-zinc-500">{t("client.documents.hint")}</p>

          <form onSubmit={handleUpload} className="mb-4 space-y-2">
            <div className="flex flex-wrap gap-2">
              <label className="flex flex-col text-xs text-zinc-500 dark:text-zinc-400">
                {t("client.documents.role")}
                <select
                  value={uploadRole}
                  onChange={(e) => setUploadRole(e.target.value)}
                  className="mt-1 rounded-md border border-zinc-300 bg-white p-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                >
                  {PARTICIPANT_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {t(`enum.participantRole.${r}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex min-w-0 flex-1 flex-col text-xs text-zinc-500 dark:text-zinc-400">
                {t("documents.field.file")}
                <input
                  name="file"
                  type="file"
                  required
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white p-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={uploading}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              {uploading ? t("client.documents.uploading") : t("client.documents.upload")}
            </button>
            {uploadError && <p className="text-xs text-red-700 dark:text-red-300">{uploadError}</p>}
          </form>

          {documents.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("client.documents.empty")}</p>
          ) : (
            <ul className="space-y-1">
              {documents.map((d) => (
                <li key={d.id} className="text-sm text-zinc-700 dark:text-zinc-300">
                  {d.original_filename}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
