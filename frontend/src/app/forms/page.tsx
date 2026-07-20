"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  type Case,
  type FormRequirements,
  type FormTemplate,
  type GeneratedForm,
  downloadGeneratedForm,
  generateForm,
  getCases,
  getFormRequirements,
  getFormTemplates,
  getGeneratedForms,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FormRequirementsDetails } from "@/components/FormRequirementsDetails";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";

export default function FormsPage() {
  // useSearchParams needs a Suspense boundary above it (Next.js bails the
  // whole page to client-only rendering otherwise) -- the actual page body
  // lives in FormsPageContent so that requirement doesn't leak into it.
  return (
    <Suspense fallback={null}>
      <FormsPageContent />
    </Suspense>
  );
}

function FormsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams.get("case_id");
  const { t } = useTranslation();
  const [cases, setCases] = useState<Case[]>([]);
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [selectedFormCode, setSelectedFormCode] = useState("");
  const [generatedForms, setGeneratedForms] = useState<GeneratedForm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<FormRequirements | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getCases(), getFormTemplates()])
      .then(([caseList, templateList]) => {
        setCases(caseList);
        setTemplates(templateList);
        // A case link from the case detail page ("Generar formulario →")
        // arrives with ?case_id=... -- prefer that over just defaulting to
        // the first case in the list, so the attorney doesn't have to
        // re-find the case they were already looking at.
        if (preselectedCaseId && caseList.some((c) => c.id === preselectedCaseId)) {
          setSelectedCaseId(preselectedCaseId);
        } else if (caseList.length > 0) {
          setSelectedCaseId(caseList[0].id);
        }
        if (templateList.length > 0) setSelectedFormCode(templateList[0].code);
      })
      .catch(() => setError(t("forms.error.connect")));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  }, []);

  useEffect(() => {
    if (!selectedCaseId) return;
    getGeneratedForms(selectedCaseId)
      .then(setGeneratedForms)
      .catch(() => setGeneratedForms([]));
  }, [selectedCaseId]);

  useEffect(() => {
    if (!selectedFormCode) return;
    getFormRequirements(selectedFormCode)
      .then(setRequirements)
      .catch(() => setRequirements(null));
  }, [selectedFormCode]);

  async function handleGenerate() {
    if (!selectedCaseId || !selectedFormCode) return;
    setLoading(true);
    setError(null);
    try {
      const created = await generateForm(selectedCaseId, selectedFormCode);
      router.push(`/forms/${created.id}`);
    } catch {
      setError(t("forms.error.generate"));
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(form: GeneratedForm) {
    setDownloadingId(form.id);
    setError(null);
    try {
      await downloadGeneratedForm(form.id, `${form.form_code}.pdf`);
    } catch {
      setError(t("forms.error.download"));
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("forms.title")}
        </h1>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Card className="mb-6 space-y-4 p-5">
          <div>
            <label htmlFor="forms-case-select" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {t("forms.case")}
            </label>
            <select
              id="forms-case-select"
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className={inputClass}
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.case_number} ({t(`enum.caseType.${c.case_type}` as Parameters<typeof t>[0])})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="forms-code-select" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {t("forms.form")}
            </label>
            <select
              id="forms-code-select"
              value={selectedFormCode}
              onChange={(e) => setSelectedFormCode(e.target.value)}
              className={inputClass}
            >
              {templates.map((tpl) => (
                <option key={tpl.code} value={tpl.code}>
                  {tpl.code} — {tpl.name}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={handleGenerate} disabled={loading || !selectedCaseId || !selectedFormCode}>
            {loading ? t("forms.generating") : t("forms.generate")}
          </Button>
          <p className="text-xs text-zinc-500">{t("forms.generateHint")}</p>

          {requirements && <FormRequirementsDetails requirements={requirements} />}
        </Card>

        <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {t("forms.generatedForCase")}
        </h2>
        {generatedForms.length === 0 && <p className="text-sm text-zinc-500">{t("forms.empty")}</p>}
        <div className="space-y-2">
          {generatedForms.map((f) => (
            <Card key={f.id} className="flex items-center justify-between p-3 text-sm">
              <span className="flex items-center gap-2 text-zinc-600 dark:text-zinc-300">
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{f.form_code}</span>
                <Badge value={f.status} label={t(`enum.formStatus.${f.status}` as Parameters<typeof t>[0])} />
                {new Date(f.created_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-3">
                <Link
                  href={`/forms/${f.id}`}
                  className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  {t("forms.open")}
                </Link>
                <button
                  type="button"
                  onClick={() => handleDownload(f)}
                  disabled={downloadingId === f.id}
                  className="font-medium text-indigo-600 hover:underline disabled:opacity-50 dark:text-indigo-400"
                >
                  {downloadingId === f.id ? t("forms.downloading") : t("forms.download")}
                </button>
              </span>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
