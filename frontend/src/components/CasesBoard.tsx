"use client";

import { useMemo, useState } from "react";
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

const AVATAR_COLORS = [
  "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300",
  "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",
  "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300",
  "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300",
  "bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300",
  "bg-violet-100 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300",
];

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}

function avatarColor(userId: string): string {
  let hash = 0;
  for (let i = 0; i < userId.length; i++) hash = (hash * 31 + userId.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

export function CasesBoard({
  cases,
  users,
  assignableUsers,
  onStatusChange,
  onOpenCase,
  onAssign,
}: {
  cases: Case[];
  users: User[];
  /** Active staff only -- who can be picked as a *new* assignee. Deactivated
   * staff can stay assigned to existing cases (still resolved via `users`
   * for display) but shouldn't be offered for new work. */
  assignableUsers: User[];
  onStatusChange: (caseId: string, status: string) => void;
  onOpenCase: (caseId: string) => void;
  onAssign: (caseId: string, attorneyId: string) => void;
}) {
  const { t } = useTranslation();
  const [dragOverStatus, setDragOverStatus] = useState<string | null>(null);
  const [assigneeFilter, setAssigneeFilter] = useState<string>("");

  function userName(userId: string | null): string {
    if (!userId) return t("cases.unassigned");
    return users.find((u) => u.id === userId)?.full_name ?? userId;
  }

  const visibleCases = useMemo(() => {
    if (!assigneeFilter) return cases;
    if (assigneeFilter === "unassigned") return cases.filter((c) => !c.assigned_attorney_id);
    return cases.filter((c) => c.assigned_attorney_id === assigneeFilter);
  }, [cases, assigneeFilter]);

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <label className="text-xs font-medium text-zinc-500 dark:text-zinc-400" htmlFor="board-assignee-filter">
          {t("cases.board.filterByAssignee")}
        </label>
        <select
          id="board-assignee-filter"
          value={assigneeFilter}
          onChange={(e) => setAssigneeFilter(e.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
        >
          <option value="">{t("cases.board.filterAll")}</option>
          <option value="unassigned">{t("cases.unassigned")}</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.full_name}
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2">
        {CASE_STATUSES.map((status) => {
          const columnCases = visibleCases.filter((c) => c.status === status);
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
                    className="cursor-grab p-3 text-sm transition hover:shadow-md active:cursor-grabbing"
                  >
                    <button onClick={() => onOpenCase(c.id)} className="block w-full text-left">
                      <p className="font-medium text-zinc-900 dark:text-zinc-50">{c.case_number}</p>
                      <p className="mt-0.5 text-xs text-zinc-500">
                        {t(`enum.caseType.${c.case_type}` as Parameters<typeof t>[0])}
                      </p>
                    </button>
                    <div className="mt-2 flex items-center gap-1.5">
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold ${
                          c.assigned_attorney_id
                            ? avatarColor(c.assigned_attorney_id)
                            : "bg-zinc-200 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-500"
                        }`}
                        title={userName(c.assigned_attorney_id)}
                      >
                        {c.assigned_attorney_id ? initials(userName(c.assigned_attorney_id)) : "—"}
                      </span>
                      <select
                        aria-label={t("cases.assignedTo")}
                        value={c.assigned_attorney_id ?? ""}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => onAssign(c.id, e.target.value)}
                        className="min-w-0 flex-1 truncate rounded-md border-0 bg-transparent py-0.5 text-xs text-zinc-500 outline-none hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                      >
                        <option value="">{t("cases.unassigned")}</option>
                        {c.assigned_attorney_id && !assignableUsers.some((u) => u.id === c.assigned_attorney_id) && (
                          <option value={c.assigned_attorney_id}>{userName(c.assigned_attorney_id)}</option>
                        )}
                        {assignableUsers.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
