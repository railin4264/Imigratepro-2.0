import type { FormRequirements } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

export function FormRequirementsDetails({ requirements, open }: { requirements: FormRequirements; open?: boolean }) {
  const { t } = useTranslation();

  return (
    <details open={open} className="rounded-md border border-zinc-100 dark:border-zinc-800">
      <summary className="cursor-pointer select-none px-2.5 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-400">
        {t("gapAnalysis.officialChecklist")} — {requirements.form_code}
      </summary>
      <div className="space-y-2 border-t border-zinc-100 p-2.5 dark:border-zinc-800">
        {requirements.categories.map((cat) => (
          <div key={cat.title}>
            <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">{cat.title}</p>
            <ul className="ml-4 list-disc text-xs text-zinc-500 dark:text-zinc-400">
              {cat.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
        <p className="text-[11px] text-zinc-400 dark:text-zinc-600">
          {t("gapAnalysis.source")}:{" "}
          <a
            href={requirements.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:underline dark:text-indigo-400"
          >
            {requirements.source_label}
          </a>{" "}
          ({t("gapAnalysis.verifiedOn")} {requirements.verified_on}). {t("gapAnalysis.disclaimer")}
        </p>
      </div>
    </details>
  );
}
