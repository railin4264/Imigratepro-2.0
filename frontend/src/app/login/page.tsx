"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function LoginPage() {
  const { t } = useTranslation();
  const { login, status } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      router.replace("/");
    } catch (err) {
      // fetchJson throws "Request to X failed: <status>" for a reached-but-
      // rejected request, and a plain network-layer error (unreachable
      // backend, DNS, CORS) for anything else -- distinguishing them here
      // avoids "wrong password" reading as truth when it's actually "the
      // backend isn't there" (see README/session notes on this exact bug).
      const status = err instanceof Error ? err.message.match(/failed: (\d+)/)?.[1] : undefined;
      if (status === "423") setError(t("login.error.locked"));
      else if (status === "403") setError(t("login.error.inactive"));
      else if (status === "429") setError(t("login.error.rateLimited"));
      else if (status === "401") setError(t("login.error"));
      else setError(t("login.error.connection"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-black">
      <LanguageSwitcher />
      <Card className="w-full max-w-sm p-6">
        <div className="mb-6 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 text-sm font-bold text-white">
            M
          </span>
          <span className="text-base font-semibold text-zinc-900 dark:text-zinc-50">MigratePro</span>
        </div>
        <h1 className="mb-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{t("login.title")}</h1>
        <p className="mb-5 text-sm text-zinc-500 dark:text-zinc-400">{t("login.subtitle")}</p>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className={labelClass}>
            {t("login.email")}
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
            {t("login.password")}
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
            {submitting ? t("login.submitting") : t("login.submit")}
          </Button>
        </form>
        <Link
          href="/forgot-password"
          className="mt-4 block text-center text-sm text-indigo-600 hover:underline dark:text-indigo-400"
        >
          {t("login.forgotPassword")}
        </Link>
      </Card>
    </div>
  );
}
