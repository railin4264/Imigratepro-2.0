"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "@/lib/i18n";
import { resetPassword } from "@/lib/api";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function ResetPasswordPage() {
  const params = useParams<{ token: string }>();
  const { t } = useTranslation();
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError(t("resetPassword.mismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("resetPassword.tooShort"));
      return;
    }
    setSubmitting(true);
    try {
      await resetPassword(params.token, password);
      setDone(true);
      setTimeout(() => router.replace("/login"), 2000);
    } catch {
      setError(t("resetPassword.error"));
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
        <h1 className="mb-5 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{t("resetPassword.title")}</h1>

        {done ? (
          <p className="text-sm text-emerald-700 dark:text-emerald-400">{t("resetPassword.done")}</p>
        ) : (
          <>
            {error && (
              <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                {error}
              </p>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <label className={labelClass}>
                {t("resetPassword.newPassword")}
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
                  autoComplete="new-password"
                  required
                  minLength={8}
                />
              </label>
              <label className={labelClass}>
                {t("resetPassword.confirmPassword")}
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className={inputClass}
                  autoComplete="new-password"
                  required
                  minLength={8}
                />
              </label>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? t("resetPassword.submitting") : t("resetPassword.submit")}
              </Button>
            </form>
          </>
        )}

        <Link
          href="/login"
          className="mt-4 block text-center text-sm text-indigo-600 hover:underline dark:text-indigo-400"
        >
          {t("nav.back")}
        </Link>
      </Card>
    </div>
  );
}
