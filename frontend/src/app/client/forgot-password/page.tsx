"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "@/lib/i18n";
import { clientForgotPassword } from "@/lib/api";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function ClientForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await clientForgotPassword(email);
    } catch {
      // Same reasoning as the staff forgot-password page: the backend
      // always returns 204 whether or not the email exists, so showing the
      // same confirmation regardless of outcome doesn't leak anything.
    } finally {
      setSubmitting(false);
      setDone(true);
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
        <h1 className="mb-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          {t("clientForgotPassword.title")}
        </h1>

        {done ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{t("clientForgotPassword.sent")}</p>
        ) : (
          <>
            <p className="mb-5 text-sm text-zinc-500 dark:text-zinc-400">{t("clientForgotPassword.subtitle")}</p>
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
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? t("clientForgotPassword.submitting") : t("clientForgotPassword.submit")}
              </Button>
            </form>
          </>
        )}

        <Link
          href="/client/login"
          className="mt-4 block text-center text-sm text-indigo-600 hover:underline dark:text-indigo-400"
        >
          {t("clientForgotPassword.backToLogin")}
        </Link>
      </Card>
    </div>
  );
}
