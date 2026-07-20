import type { CaseTimeline as CaseTimelineData } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

const STATUS_STYLES: Record<string, string> = {
  done: "border-green-600 bg-green-600 text-white",
  current: "border-amber-500 bg-amber-500 text-white animate-pulse",
  pending: "border-zinc-300 bg-white text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900",
};

export function CaseTimeline({ timeline }: { timeline: CaseTimelineData }) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-wrap gap-x-1 gap-y-3">
      {timeline.steps.map((step, idx) => (
        <div key={step.key} className="flex items-center">
          <div className="flex flex-col items-center gap-1 px-1 text-center">
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold ${STATUS_STYLES[step.status] ?? STATUS_STYLES.pending}`}
              aria-hidden="true"
            >
              {step.status === "done" ? "✓" : idx + 1}
            </span>
            <span
              className={`max-w-[5.5rem] text-[11px] leading-tight ${
                step.status === "pending"
                  ? "text-zinc-400 dark:text-zinc-600"
                  : "font-medium text-zinc-700 dark:text-zinc-300"
              }`}
            >
              {t(`timeline.step.${step.key}` as Parameters<typeof t>[0])}
              {/* The circle's checkmark/number and its color are aria-hidden
                  (purely decorative) -- without this, a screen reader user
                  gets the list of step names with no indication of progress. */}
              <span className="sr-only">
                {" "}
                ({t(`timeline.status.${step.status}` as Parameters<typeof t>[0])})
              </span>
            </span>
          </div>
          {idx < timeline.steps.length - 1 && (
            <span
              className={`mb-4 h-0.5 w-4 shrink-0 sm:w-6 ${
                step.status === "done" ? "bg-green-600" : "bg-zinc-200 dark:bg-zinc-800"
              }`}
              aria-hidden="true"
            />
          )}
        </div>
      ))}
    </div>
  );
}
