"use client";

import { useTranslation } from "@/lib/i18n";

export function LanguageSwitcher({ fixed = true }: { fixed?: boolean }) {
  const { lang, setLang, t } = useTranslation();

  return (
    <div
      className={`${
        fixed ? "fixed right-4 top-4 z-50" : ""
      } flex items-center gap-1 rounded-full border border-zinc-200 bg-white p-1 text-xs shadow-sm dark:border-zinc-800 dark:bg-zinc-900`}
    >
      <span className="sr-only">{t("lang.label")}</span>
      {(["es", "en"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`flex min-h-11 min-w-11 items-center justify-center rounded-full px-2.5 font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
            lang === l
              ? "bg-indigo-600 text-white"
              : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
          }`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
