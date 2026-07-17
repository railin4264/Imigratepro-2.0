"use client";

import { useEffect, useRef, useState } from "react";
import {
  type Case,
  type Client,
  type DocumentDetail,
  type UploadedDocument,
  DOCUMENT_TYPES,
  applyDocumentToClient,
  deleteDocument,
  extractDocument,
  getAiStatus,
  getCases,
  getClients,
  getDocument,
  getDocuments,
  uploadCaseDocument,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

const APPLICABLE_FIELDS = [
  "first_name",
  "last_name",
  "date_of_birth",
  "country_of_birth",
  "nationality",
  "passport_number",
  "a_number",
];

export default function DocumentsPage() {
  const { t } = useTranslation();
  const [cases, setCases] = useState<Case[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [aiConfigured, setAiConfigured] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [caseId, setCaseId] = useState("");
  const [clientId, setClientId] = useState("");
  const [documentType, setDocumentType] = useState<string>("other");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, DocumentDetail>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [appliedId, setAppliedId] = useState<string | null>(null);

  function load() {
    Promise.all([getCases(), getClients(), getAiStatus(), getDocuments()])
      .then(([caseList, clientList, aiStatus, docList]) => {
        setCases(caseList);
        setClients(clientList);
        setAiConfigured(aiStatus.configured);
        setDocuments(docList);
      })
      .catch(() => setError(t("documents.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  const casesById = Object.fromEntries(cases.map((c) => [c.id, c]));
  const clientsById = Object.fromEntries(clients.map((c) => [c.id, c]));

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!caseId || !file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadCaseDocument(caseId, file, {
        clientId: clientId || undefined,
        documentType,
      });
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      load();
    } catch {
      setError(t("documents.error.upload"));
    } finally {
      setUploading(false);
    }
  }

  async function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!details[id]) {
      try {
        const detail = await getDocument(id);
        setDetails((prev) => ({ ...prev, [id]: detail }));
      } catch {
        setError(t("documents.error.connect"));
      }
    }
  }

  async function handleExtract(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const detail = await extractDocument(id);
      setDetails((prev) => ({ ...prev, [id]: detail }));
      setDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, status: detail.status } : d)));
    } catch {
      setError(t("documents.error.extract"));
    } finally {
      setBusyId(null);
    }
  }

  async function handleApply(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const detail = await applyDocumentToClient(id, APPLICABLE_FIELDS);
      setDetails((prev) => ({ ...prev, [id]: detail }));
      setAppliedId(id);
      setTimeout(() => setAppliedId((cur) => (cur === id ? null : cur)), 2500);
    } catch {
      setError(t("documents.error.apply"));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(id: string) {
    setBusyId(id);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setError(t("documents.error.connect"));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("documents.title")}
        </h1>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {!aiConfigured && (
          <p className="mb-4 rounded-lg bg-amber-50 p-4 text-sm text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
            {t("documents.aiOffline")}
          </p>
        )}

        <Card className="mb-6 p-5">
          <h2 className="mb-3 font-medium text-zinc-900 dark:text-zinc-50">{t("documents.upload.title")}</h2>
          {cases.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("documents.noCases")}</p>
          ) : (
            <form onSubmit={handleUpload} className="space-y-3">
              <label className={labelClass}>
                {t("documents.field.case")}
                <select
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  className={stackedInputClass}
                  required
                >
                  <option value="">{t("documents.field.case.select")}</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("documents.field.client")}
                <select value={clientId} onChange={(e) => setClientId(e.target.value)} className={stackedInputClass}>
                  <option value="">{t("documents.field.client.select")}</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.first_name} {c.last_name}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("documents.field.type")}
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className={stackedInputClass}
                >
                  {DOCUMENT_TYPES.map((dt) => (
                    <option key={dt} value={dt}>
                      {t(`enum.documentType.${dt}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("documents.field.file")}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className={stackedInputClass}
                  required
                />
              </label>
              <Button type="submit" disabled={uploading || !file}>
                {uploading ? t("documents.uploading") : t("documents.uploadButton")}
              </Button>
            </form>
          )}
        </Card>

        {documents.length === 0 && !error && <p className="text-zinc-500 dark:text-zinc-400">{t("documents.empty")}</p>}

        <div className="space-y-3">
          {documents.map((doc) => {
            const caseNumber = doc.case_id ? casesById[doc.case_id]?.case_number : null;
            const client = doc.client_id ? clientsById[doc.client_id] : null;
            const detail = details[doc.id];
            const extracted = detail?.extracted_data;
            const isBusy = busyId === doc.id;

            return (
              <Card key={doc.id} className="p-5">
                <div className="flex items-center justify-between gap-3">
                  <button
                    onClick={() => toggleExpand(doc.id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <p className="truncate font-medium text-zinc-900 dark:text-zinc-50">{doc.original_filename}</p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {caseNumber ?? "—"}
                      {client ? ` · ${client.first_name} ${client.last_name}` : ""} ·{" "}
                      {t(`enum.documentType.${doc.document_type}` as Parameters<typeof t>[0])}
                    </p>
                  </button>
                  <Badge
                    value={doc.status}
                    label={t(`documents.status.${doc.status}` as Parameters<typeof t>[0])}
                  />
                </div>

                {expandedId === doc.id && (
                  <div className="mt-4 space-y-3 border-t border-zinc-100 pt-4 dark:border-zinc-800">
                    <div className="flex flex-wrap gap-2">
                      {aiConfigured && (
                        <Button variant="secondary" disabled={isBusy} onClick={() => handleExtract(doc.id)}>
                          {isBusy ? t("documents.extracting") : t("documents.extract")}
                        </Button>
                      )}
                      {extracted && !extracted.error && (
                        <Button
                          variant="secondary"
                          disabled={isBusy || !doc.client_id}
                          onClick={() => handleApply(doc.id)}
                          title={!doc.client_id ? t("documents.noClientLinked") : undefined}
                        >
                          {appliedId === doc.id
                            ? t("documents.applied")
                            : isBusy
                              ? t("documents.applying")
                              : t("documents.applyToClient")}
                        </Button>
                      )}
                      <Button variant="secondary" disabled={isBusy} onClick={() => handleDelete(doc.id)}>
                        {t("documents.delete")}
                      </Button>
                    </div>

                    {extracted && !extracted.error && (
                      <div className="rounded-lg bg-zinc-50 p-3 text-sm dark:bg-zinc-800/50">
                        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                          {t("documents.extractedData")}
                        </p>
                        <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                          {[
                            ["documents.field.firstName", extracted.first_name],
                            ["documents.field.lastName", extracted.last_name],
                            ["documents.field.dob", extracted.date_of_birth],
                            ["documents.field.countryOfBirth", extracted.country_of_birth],
                            ["documents.field.nationality", extracted.nationality],
                            ["documents.field.passportNumber", extracted.passport_number],
                            ["documents.field.aNumber", extracted.a_number],
                            ["documents.field.expirationDate", extracted.expiration_date],
                          ]
                            .filter(([, value]) => value)
                            .map(([key, value]) => (
                              <div key={key}>
                                <dt className="text-xs text-zinc-500">{t(key as Parameters<typeof t>[0])}</dt>
                                <dd className="text-zinc-900 dark:text-zinc-50">{value}</dd>
                              </div>
                            ))}
                        </dl>
                        {extracted.confidence_notes && (
                          <p className="mt-2 text-xs italic text-zinc-500">{extracted.confidence_notes}</p>
                        )}
                        {!doc.client_id && (
                          <p className="mt-2 text-xs text-amber-700 dark:text-amber-400">
                            {t("documents.noClientLinked")}
                          </p>
                        )}
                      </div>
                    )}

                    {extracted?.error && (
                      <p className="rounded-lg bg-red-50 p-3 text-xs text-red-700 dark:bg-red-950 dark:text-red-300">
                        {extracted.error}
                      </p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
