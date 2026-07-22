"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/lib/i18n";
import { useClientAuth } from "@/lib/clientAuth";
import { getMyCases, type ClientCaseSummary } from "@/lib/api";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const statusBadgeClass =
  "inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";

export default function ClientDashboardPage() {
  const { t } = useTranslation();
  const { client, status, logout } = useClientAuth();
  const router = useRouter();

  const [cases, setCases] = useState<ClientCaseSummary[] | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/client/login");
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated") return;
    getMyCases()
      .then(setCases)
      .catch(() => setLoadError(true));
  }, [status]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("clientDashboard.loading")}</p>
      </div>
    );
  }

  if (status !== "authenticated") return null;

  return (
    <div className="min-h-screen bg-zinc-50 px-4 py-8 dark:bg-black">
      <div className="fixed right-4 top-4 z-50 flex items-center gap-2">
        <ThemeToggle />
        <LanguageSwitcher fixed={false} />
      </div>
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{t("clientDashboard.title")}</h1>
            {client && (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                {client.first_name} {client.last_name}
              </p>
            )}
          </div>
          <Button
            variant="secondary"
            onClick={() => {
              logout();
              router.replace("/client/login");
            }}
          >
            {t("clientDashboard.logout")}
          </Button>
        </div>

        {loadError && (
          <Card className="p-4 text-sm text-red-700 dark:text-red-300">{t("clientDashboard.error")}</Card>
        )}

        {!loadError && cases === null && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("clientDashboard.loading")}</p>
        )}

        {cases !== null && cases.length === 0 && (
          <Card className="p-4 text-sm text-zinc-500 dark:text-zinc-400">{t("clientDashboard.noCases")}</Card>
        )}

        <div className="space-y-4">
          {cases?.map((c) => (
            <Card key={c.id} className="p-5">
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-50">{c.case_number}</p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {t(`clientDashboard.role.${c.my_role}` as never)}
                  </p>
                </div>
                <span className={statusBadgeClass}>{t(`enum.caseStatus.${c.status}` as never)}</span>
              </div>

              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-400 dark:text-zinc-500">
                {t("clientDashboard.forms")}
              </p>
              {c.forms.length === 0 ? (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("clientDashboard.noForms")}</p>
              ) : (
                <ul className="space-y-2">
                  {c.forms.map((f) => (
                    <li
                      key={f.id}
                      className="flex items-center justify-between rounded-lg border border-zinc-200 p-3 dark:border-zinc-800"
                    >
                      <div>
                        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                          {f.form_code} — {f.form_name}
                        </p>
                        <span className={statusBadgeClass}>
                          {t(`clientDashboard.status.${f.status}` as never)}
                        </span>
                      </div>
                      <Link href={`/client/forms/${f.access_token}`}>
                        <Button variant="secondary">{t("clientDashboard.openForm")}</Button>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
