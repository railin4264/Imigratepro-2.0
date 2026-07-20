"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "@/lib/i18n";
import { forgotPassword } from "@/lib/api";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await forgotPassword(email);
    } catch {
      // Intentionally ignored: the backend always returns 204 regardless of
      // whether the email exists, so this shouldn't normally fail -- if it
      // does (network issue), showing the same confirmation is still safer
      // than revealing anything about the failure.
    } finally {
      setSubmitting(false);
      setDone(true);
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
        <h1 className="mb-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          {t("forgotPassword.title")}
        </h1>

        {done ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{t("forgotPassword.done")}</p>
        ) : (
          <>
            <p className="mb-5 text-sm text-zinc-500 dark:text-zinc-400">{t("forgotPassword.subtitle")}</p>
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
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? t("forgotPassword.submitting") : t("forgotPassword.submit")}
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
