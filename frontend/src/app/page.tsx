"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { type MyDay, getMyDay } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const PRIORITY_CLASSES: Record<string, string> = {
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  medium: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  high: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
};

function MyDayStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{value}</p>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
    </div>
  );
}

function MyDaySection() {
  const { t } = useTranslation();
  const [myDay, setMyDay] = useState<MyDay | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getMyDay()
      .then(setMyDay)
      .catch(() => setError(true));
  }, []);

  if (error || !myDay) return null;

  const hasActivity =
    myDay.checklist_due.length > 0 || myDay.open_rfes.length > 0 || myDay.cases_ready_for_review.length > 0;

  return (
    <div className="mb-8">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {t("myDay.title")}
      </h2>
      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MyDayStat label={t("myDay.assignedCases")} value={myDay.assigned_case_count} />
        <MyDayStat label={t("myDay.appointmentsToday")} value={myDay.appointments_today.length} />
        <MyDayStat label={t("myDay.readyForReview")} value={myDay.cases_ready_for_review.length} />
        <MyDayStat label={t("myDay.openRfes")} value={myDay.open_rfes.length} />
      </div>

      {hasActivity && (
        <Card className="p-5">
          {myDay.checklist_due.length > 0 && (
            <div className="mb-4">
              <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                {t("myDay.checklistDue")}
              </h3>
              <ul className="space-y-1.5">
                {myDay.checklist_due.map((item) => (
                  <li key={item.id} className="flex flex-wrap items-center gap-2 text-sm">
                    <Link
                      href="/cases"
                      className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      {item.case_number}
                    </Link>
                    <span className="text-zinc-600 dark:text-zinc-400">{item.label}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        PRIORITY_CLASSES[item.priority] ?? PRIORITY_CLASSES.medium
                      }`}
                    >
                      {t(`enum.priority.${item.priority}` as Parameters<typeof t>[0])}
                    </span>
                    {item.overdue && (
                      <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-300">
                        {t("myDay.overdue")}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {myDay.open_rfes.length > 0 && (
            <div className="mb-4">
              <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                {t("myDay.openRfes")}
              </h3>
              <ul className="space-y-1.5">
                {myDay.open_rfes.map((rfe) => (
                  <li key={rfe.id} className="flex flex-wrap items-center gap-2 text-sm">
                    <Link href="/cases" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                      {rfe.case_number}
                    </Link>
                    {rfe.response_due_date && (
                      <span className="text-zinc-500 dark:text-zinc-400">
                        {t("myDay.dueBy")} {rfe.response_due_date}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {myDay.cases_ready_for_review.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                {t("myDay.readyForReview")}
              </h3>
              <ul className="space-y-1.5">
                {myDay.cases_ready_for_review.map((c) => (
                  <li key={c.id} className="flex items-center gap-2 text-sm">
                    <Link href="/cases" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                      {c.case_number}
                    </Link>
                    <Badge value={c.status} label={t(`enum.caseStatus.${c.status}` as Parameters<typeof t>[0])} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

export default function Home() {
  const { t } = useTranslation();

  const modules = [
    { href: "/clients", label: t("home.clients"), description: t("home.clients.desc"), icon: "◒" },
    { href: "/cases", label: t("home.cases"), description: t("home.cases.desc"), icon: "▤" },
    { href: "/team", label: t("home.team"), description: t("home.team.desc"), icon: "◕" },
    { href: "/services", label: t("home.services"), description: t("home.services.desc"), icon: "◈" },
    { href: "/forms", label: t("home.forms"), description: t("home.forms.desc"), icon: "▥" },
    { href: "/documents", label: t("home.documents"), description: t("home.documents.desc"), icon: "▦" },
    { href: "/appointments", label: t("home.appointments"), description: t("home.appointments.desc"), icon: "◷" },
    { href: "/billing", label: t("home.billing"), description: t("home.billing.desc"), icon: "◎" },
    { href: "/stats", label: t("home.stats"), description: t("home.stats.desc"), icon: "▲" },
  ];

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-1 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("home.title")}
        </h1>
        <p className="mb-8 text-zinc-500 dark:text-zinc-400">{t("home.subtitle")}</p>

        <MyDaySection />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((mod) => (
            <Link key={mod.href} href={mod.href}>
              <Card className="h-full p-5 transition hover:border-indigo-300 hover:shadow-md dark:hover:border-indigo-800">
                <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-lg text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
                  {mod.icon}
                </span>
                <h2 className="font-medium text-zinc-900 dark:text-zinc-50">{mod.label}</h2>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{mod.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
