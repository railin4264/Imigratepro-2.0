"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/lib/i18n";
import { useClientAuth } from "@/lib/clientAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function ClientLoginPage() {
  const { t } = useTranslation();
  const { login, status } = useClientAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/client/dashboard");
  }, [status, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      router.replace("/client/dashboard");
    } catch (err) {
      const httpStatus = err instanceof Error ? err.message.match(/failed: (\d+)/)?.[1] : undefined;
      if (httpStatus === "423") setError(t("clientLogin.error.locked"));
      else if (httpStatus === "429") setError(t("clientLogin.error.rateLimited"));
      else if (httpStatus === "401") setError(t("clientLogin.error"));
      else setError(t("clientLogin.error.connection"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-black">
      <div className="fixed right-4 top-4 z-50 flex items-center gap-2">
        <ThemeToggle />
        <LanguageSwitcher fixed={false} />
      </div>
      <Card className="w-full max-w-sm p-6">
        <div className="mb-6 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 text-sm font-bold text-white">
            M
          </span>
          <span className="text-base font-semibold text-zinc-900 dark:text-zinc-50">MigratePro</span>
        </div>
        <h1 className="mb-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{t("clientLogin.title")}</h1>
        <p className="mb-5 text-sm text-zinc-500 dark:text-zinc-400">{t("clientLogin.subtitle")}</p>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className={labelClass}>
            {t("clientLogin.email")}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              autoComplete="username"
              required
            />
          </label>
          <label className={labelClass}>
            {t("clientLogin.password")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              autoComplete="current-password"
              required
            />
          </label>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? t("clientLogin.submitting") : t("clientLogin.submit")}
          </Button>
        </form>
        <Link
          href="/client/forgot-password"
          className="mt-4 block text-center text-sm text-indigo-600 hover:underline dark:text-indigo-400"
        >
          {t("clientLogin.forgotPassword")}
        </Link>
        <p className="mt-4 text-center text-xs text-zinc-400 dark:text-zinc-500">{t("clientLogin.noAccount")}</p>
      </Card>
    </div>
  );
}
