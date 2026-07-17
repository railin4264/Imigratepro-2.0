"use client";

import { useState } from "react";
import { CASE_STATUSES, type Case, type User } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { Card } from "@/components/ui/Card";

const COLUMN_ACCENT: Record<string, string> = {
  intake: "border-t-zinc-400",
  preparing: "border-t-amber-400",
  filed: "border-t-blue-400",
  rfe: "border-t-orange-400",
  approved: "border-t-emerald-400",
  denied: "border-t-red-400",
  closed: "border-t-zinc-300",
};

export function CasesBoard({
  cases,
  users,
  onStatusChange,
  onOpenCase,
}: {
  cases: Case[];
  users: User[];
  onStatusChange: (caseId: string, status: string) => void;
  onOpenCase: (caseId: string) => void;
}) {
  const { t } = useTranslation();
  const [dragOverStatus, setDragOverStatus] = useState<string | null>(null);

  function userName(userId: string | null): string {
    if (!userId) return t("cases.unassigned");
    return users.find((u) => u.id === userId)?.full_name ?? userId;
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {CASE_STATUSES.map((status) => {
        const columnCases = cases.filter((c) => c.status === status);
        return (
          <div
            key={status}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOverStatus(status);
            }}
            onDragLeave={() => setDragOverStatus((s) => (s === status ? null : s))}
            onDrop={(e) => {
              e.preventDefault();
              setDragOverStatus(null);
              const caseId = e.dataTransfer.getData("text/plain");
              if (caseId) onStatusChange(caseId, status);
            }}
            className={`w-64 shrink-0 rounded-xl border-t-4 bg-zinc-50 p-2 dark:bg-zinc-900/40 ${
              COLUMN_ACCENT[status] ?? "border-t-zinc-400"
            } ${dragOverStatus === status ? "ring-2 ring-indigo-400" : ""}`}
          >
            <div className="mb-2 flex items-center justify-between px-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                {t(`enum.caseStatus.${status}` as Parameters<typeof t>[0])}
              </span>
              <span className="text-xs text-zinc-400">{columnCases.length}</span>
            </div>
            <div className="min-h-16 space-y-2">
              {columnCases.map((c) => (
                <Card
                  key={c.id}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/plain", c.id);
                    e.dataTransfer.effectAllowed = "move";
                  }}
                  onClick={() => onOpenCase(c.id)}
                  className="cursor-grab p-3 text-sm transition hover:shadow-md active:cursor-grabbing"
                >
                  <p className="font-medium text-zinc-900 dark:text-zinc-50">{c.case_number}</p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {t(`enum.caseType.${c.case_type}` as Parameters<typeof t>[0])}
                  </p>
                  <p className="mt-1 text-xs text-zinc-400">{userName(c.assigned_attorney_id)}</p>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
