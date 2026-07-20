"use client";

import { useEffect, useState } from "react";
import { type GapAnalysis, getCaseGapAnalysis } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { FormRequirementsDetails } from "@/components/FormRequirementsDetails";

const SEVERITY_CLASSES: Record<string, string> = {
  high: "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300",
  medium:
    "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300",
  low: "border-zinc-200 bg-zinc-50 text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400",
};

export function GapAnalysisPanel({ caseId, refreshKey }: { caseId: string; refreshKey?: string | number }) {
  const { t } = useTranslation();
  const [analysis, setAnalysis] = useState<GapAnalysis | null>(null);

  // refreshKey lets the parent force a re-fetch when something gap analysis
  // depends on changes (participants added, service/checklist updated) --
  // without it this only ever fetches once per case, going stale the moment
  // you fix the very thing it flagged.
  useEffect(() => {
    getCaseGapAnalysis(caseId)
      .then(setAnalysis)
      .catch(() => setAnalysis(null));
  }, [caseId, refreshKey]);

  if (!analysis) return null;

  return (
    <div className="mb-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">{t("gapAnalysis.title")}</h3>
      {analysis.gaps.length === 0 ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-400">{t("gapAnalysis.empty")}</p>
      ) : (
        <ul className="space-y-1.5">
          {analysis.gaps.map((gap, idx) => (
            <li
              key={idx}
              className={`rounded-md border px-2.5 py-1.5 text-sm ${SEVERITY_CLASSES[gap.severity] ?? SEVERITY_CLASSES.low}`}
            >
              {gap.message}
            </li>
          ))}
        </ul>
      )}

      {analysis.reference_checklist.length > 0 && (
        <div className="mt-3 space-y-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
          {analysis.reference_checklist.map((ref) => (
            <FormRequirementsDetails key={ref.form_code} requirements={ref} />
          ))}
        </div>
      )}
    </div>
  );
}
