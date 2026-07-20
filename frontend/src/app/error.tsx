"use client";

import { useTranslation } from "@/lib/i18n";

export default function GlobalError({
  error: _error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-center">
      <p className="text-xl font-semibold text-zinc-800 dark:text-zinc-100">{t("error.title")}</p>
      <p className="max-w-sm text-sm text-zinc-500 dark:text-zinc-400">{t("error.message")}</p>
      <button
        onClick={reset}
        className="min-h-11 rounded-lg bg-black px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
      >
        {t("error.retry")}
      </button>
    </div>
  );
}
