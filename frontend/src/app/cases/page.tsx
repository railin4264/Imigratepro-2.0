"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  CASE_STATUSES,
  CASE_TYPES,
  type Case,
  type User,
  createCase,
  getCases,
  getUsers,
  updateCase,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CasesBoard } from "@/components/CasesBoard";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 w-full ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function CasesPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  const isAdmin = user?.role === "admin";
  const [cases, setCases] = useState<Case[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  // Deactivated staff can stay assigned to whatever they already had, but
  // shouldn't be offered as a target for *new* assignments.
  const activeUsers = users.filter((u) => u.is_active);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [caseNumber, setCaseNumber] = useState("");
  const [caseType, setCaseType] = useState<string>(CASE_TYPES[0]);
  const [status, setStatus] = useState<string>(CASE_STATUSES[0]);

  const [view, setView] = useState<"list" | "board">("list");

  function load() {
    Promise.all([getCases(), getUsers()])
      .then(([caseList, userList]) => {
        setCases(caseList);
        setUsers(userList);
      })
      .catch(() => setError(t("cases.error.connect")));
  }

  async function handleAssign(caseId: string, attorneyId: string) {
    try {
      const updated = await updateCase(caseId, { assigned_attorney_id: attorneyId || null });
      setCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));
    } catch {
      setError(t("cases.error.assign"));
    }
  }

  async function handleBoardStatusChange(caseId: string, status: string) {
    try {
      const updated = await updateCase(caseId, { status });
      setCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));
    } catch {
      setError(t("cases.error.assign"));
    }
  }

  function userName(userId: string | null): string {
    if (!userId) return t("cases.unassigned");
    const u = users.find((usr) => usr.id === userId);
    return u ? u.full_name : userId;
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleCreateCase(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createCase({ case_number: caseNumber, case_type: caseType, status });
      setCaseNumber("");
      setShowForm(false);
      load();
      router.push(`/cases/${created.id}`);
    } catch {
      setError(t("cases.error.create"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className={`mx-auto ${view === "board" ? "max-w-full" : "max-w-4xl"}`}>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {t("cases.title")}
          </h1>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setShowForm((s) => !s)} variant={showForm ? "secondary" : "primary"}>
              {showForm ? t("cases.cancel") : t("cases.new")}
            </Button>
            {isAdmin && (
              <Link
                href="/team"
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                {t("cases.staff.new")}
              </Link>
            )}
          </div>
        </div>

        <div className="mb-4 inline-flex rounded-lg border border-zinc-200 bg-white p-0.5 text-sm dark:border-zinc-800 dark:bg-zinc-900">
          <button
            onClick={() => setView("list")}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              view === "list"
                ? "bg-indigo-600 text-white"
                : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
          >
            {t("cases.view.list")}
          </button>
          <button
            onClick={() => setView("board")}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              view === "board"
                ? "bg-indigo-600 text-white"
                : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
          >
            {t("cases.view.board")}
          </button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {showForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleCreateCase} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className={labelClass}>
                {t("cases.field.caseNumber")}
                <input
                  required
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("cases.field.caseType")}
                <select value={caseType} onChange={(e) => setCaseType(e.target.value)} className={stackedInputClass}>
                  {CASE_TYPES.map((ct) => (
                    <option key={ct} value={ct}>
                      {t(`enum.caseType.${ct}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("cases.field.status")}
                <select value={status} onChange={(e) => setStatus(e.target.value)} className={stackedInputClass}>
                  {CASE_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {t(`enum.caseStatus.${s}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <Button type="submit" disabled={saving} className="sm:col-span-3 mt-2">
                {saving ? t("cases.saving") : t("cases.save")}
              </Button>
            </form>
          </Card>
        )}

        {cases.length === 0 && !error && (
          <p className="text-zinc-500 dark:text-zinc-400">{t("cases.empty")}</p>
        )}

        {view === "board" && (
          <CasesBoard
            cases={cases}
            users={users}
            assignableUsers={activeUsers}
            onStatusChange={handleBoardStatusChange}
            onOpenCase={(caseId) => router.push(`/cases/${caseId}`)}
            onAssign={handleAssign}
          />
        )}

        {view === "list" && (
          <div className="space-y-2">
            {cases.map((c) => (
              <Link key={c.id} href={`/cases/${c.id}`} className="block">
                <Card className="transition hover:border-indigo-300 dark:hover:border-indigo-700">
                  <div className="flex w-full items-center justify-between p-4 text-left text-sm">
                    <span className="font-medium text-zinc-900 dark:text-zinc-50">{c.case_number}</span>
                    <span className="flex flex-wrap items-center gap-2 text-zinc-500 dark:text-zinc-400">
                      <Badge value={c.status} label={t(`enum.caseStatus.${c.status}` as Parameters<typeof t>[0])} />
                      <span>{t(`enum.caseType.${c.case_type}` as Parameters<typeof t>[0])}</span>
                      <span>·</span>
                      <span>{userName(c.assigned_attorney_id)}</span>
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
