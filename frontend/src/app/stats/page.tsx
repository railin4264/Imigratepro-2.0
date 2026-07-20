"use client";

import { useEffect, useState } from "react";
import { type CountByKey, type RevenuePoint, type StatsOverview, getRevenueByMonth, getStatsOverview } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { formatMoney as money } from "@/lib/format";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";

const STATUS_BAR_COLOR: Record<string, string> = {
  intake: "bg-zinc-400",
  preparing: "bg-amber-400",
  filed: "bg-blue-400",
  rfe: "bg-orange-400",
  approved: "bg-emerald-400",
  denied: "bg-red-400",
  closed: "bg-zinc-300",
};

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{value}</p>
    </Card>
  );
}

function BarList({
  items,
  colorFor,
  labelFor,
}: {
  items: CountByKey[];
  colorFor: (key: string) => string;
  labelFor: (key: string) => string;
}) {
  const max = Math.max(1, ...items.map((i) => i.count));
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.key} className="flex items-center gap-3">
          <span
            title={labelFor(item.key)}
            className="w-32 shrink-0 truncate text-sm text-zinc-600 dark:text-zinc-400"
          >
            {labelFor(item.key)}
          </span>
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className={`h-full rounded-full ${colorFor(item.key)}`}
              style={{ width: `${Math.max(4, (item.count / max) * 100)}%` }}
            />
          </div>
          <span className="w-6 shrink-0 text-right text-sm font-medium text-zinc-900 dark:text-zinc-50">
            {item.count}
          </span>
        </li>
      ))}
    </ul>
  );
}

function RevenueChart({ points }: { points: RevenuePoint[] }) {
  const { t } = useTranslation();
  const max = Math.max(1, ...points.flatMap((p) => [p.invoiced, p.collected]));

  return (
    <div>
      <div className="mb-3 flex items-center gap-4 text-xs text-zinc-600 dark:text-zinc-400">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-indigo-600" /> {t("stats.invoiced")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> {t("stats.collected")}
        </span>
      </div>
      <div className="flex items-end gap-4">
        {points.map((p) => (
          <div key={p.month} className="flex flex-1 flex-col items-center gap-1">
            <div className="flex h-32 items-end gap-1">
              <div
                className="w-4 rounded-t bg-indigo-600"
                style={{ height: `${Math.max(2, (p.invoiced / max) * 100)}%` }}
                title={`${t("stats.invoiced")}: ${money(p.invoiced)}`}
              />
              <div
                className="w-4 rounded-t bg-emerald-500"
                style={{ height: `${Math.max(2, (p.collected / max) * 100)}%` }}
                title={`${t("stats.collected")}: ${money(p.collected)}`}
              />
            </div>
            <span className="text-xs text-zinc-500">{p.month}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function StatsPage() {
  const { t } = useTranslation();
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [revenue, setRevenue] = useState<RevenuePoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getStatsOverview(), getRevenueByMonth(6)])
      .then(([o, r]) => {
        setOverview(o);
        setRevenue(r);
      })
      .catch(() => setError(t("stats.error.connect")));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  }, []);

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("stats.title")}
        </h1>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {overview && (
          <>
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              <StatTile label={t("stats.totalClients")} value={overview.total_clients} />
              <StatTile label={t("stats.totalCases")} value={overview.total_cases} />
              <StatTile label={t("stats.openCases")} value={overview.open_cases} />
              <StatTile label={t("stats.totalDocuments")} value={overview.total_documents} />
              <StatTile label={t("stats.upcomingAppointments")} value={overview.upcoming_appointments_7d} />
              <StatTile label={t("stats.overdueAppointments")} value={overview.overdue_appointments} />
              <StatTile label={t("stats.overdueInvoices")} value={overview.overdue_invoice_count} />
            </div>

            <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatTile label={t("stats.totalInvoiced")} value={money(overview.total_invoiced)} />
              <StatTile label={t("stats.totalCollected")} value={money(overview.total_collected)} />
              <StatTile label={t("stats.totalOutstanding")} value={money(overview.total_outstanding)} />
            </div>

            <Card className="mb-4 p-5">
              <h2 className="mb-4 font-medium text-zinc-900 dark:text-zinc-50">{t("stats.revenue")}</h2>
              {revenue.length > 0 && <RevenueChart points={revenue} />}
            </Card>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Card className="p-5">
                <h2 className="mb-4 font-medium text-zinc-900 dark:text-zinc-50">{t("stats.casesByStatus")}</h2>
                <BarList
                  items={overview.cases_by_status}
                  colorFor={(k) => STATUS_BAR_COLOR[k] ?? "bg-indigo-500"}
                  labelFor={(k) => t(`enum.caseStatus.${k}` as Parameters<typeof t>[0])}
                />
              </Card>
              <Card className="p-5">
                <h2 className="mb-4 font-medium text-zinc-900 dark:text-zinc-50">{t("stats.casesByType")}</h2>
                <BarList
                  items={overview.cases_by_type}
                  colorFor={() => "bg-indigo-500"}
                  labelFor={(k) => t(`enum.caseType.${k}` as Parameters<typeof t>[0])}
                />
              </Card>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
