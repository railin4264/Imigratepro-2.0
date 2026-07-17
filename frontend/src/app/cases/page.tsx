"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CASE_STATUSES,
  CASE_TYPES,
  CHECKLIST_PRIORITIES,
  PARTICIPANT_ROLES,
  USER_ROLES,
  type Case,
  type CaseServiceView,
  type Client,
  type GeneratedForm,
  type Participant,
  type Service,
  type User,
  addParticipant,
  advanceStage,
  applyServiceToCase,
  createCase,
  createUser,
  getCaseService,
  getCases,
  getClients,
  getGeneratedForms,
  getParticipants,
  getServices,
  getUsers,
  toggleChecklistItem,
  updateCase,
  updateChecklistItem,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CasesBoard } from "@/components/CasesBoard";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 w-full ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

const PRIORITY_CLASSES: Record<string, string> = {
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  medium: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  high: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
};

export default function CasesPage() {
  const { t } = useTranslation();
  const [cases, setCases] = useState<Case[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [caseNumber, setCaseNumber] = useState("");
  const [caseType, setCaseType] = useState<string>(CASE_TYPES[0]);
  const [status, setStatus] = useState<string>(CASE_STATUSES[0]);

  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [newParticipantClientId, setNewParticipantClientId] = useState("");
  const [newParticipantRole, setNewParticipantRole] = useState<string>(PARTICIPANT_ROLES[0]);

  const [showStaffForm, setShowStaffForm] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [staffRole, setStaffRole] = useState<string>("attorney");

  const [services, setServices] = useState<Service[]>([]);
  const [caseService, setCaseService] = useState<CaseServiceView | null>(null);
  const [caseForms, setCaseForms] = useState<GeneratedForm[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState("");

  const [view, setView] = useState<"list" | "board">("list");

  function load() {
    Promise.all([getCases(), getClients(), getUsers(), getServices()])
      .then(([caseList, clientList, userList, serviceList]) => {
        setCases(caseList);
        setClients(clientList);
        setUsers(userList);
        setServices(serviceList);
        if (clientList.length > 0) setNewParticipantClientId(clientList[0].id);
        if (serviceList.length > 0) setSelectedServiceId(serviceList[0].id);
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

  function handleOpenFromBoard(caseId: string) {
    setView("list");
    if (expandedCaseId !== caseId) toggleExpand(caseId);
  }

  function userName(userId: string | null): string {
    if (!userId) return t("cases.unassigned");
    const u = users.find((usr) => usr.id === userId);
    return u ? u.full_name : userId;
  }

  async function handleCreateStaff(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await createUser({ full_name: staffName, email: staffEmail, role: staffRole });
      setUsers((prev) => [...prev, created]);
      setStaffName("");
      setStaffEmail("");
      setShowStaffForm(false);
    } catch {
      setError(t("cases.error.assign"));
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleCreateCase(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createCase({ case_number: caseNumber, case_type: caseType, status });
      setCaseNumber("");
      setShowForm(false);
      load();
    } catch {
      setError(t("cases.error.create"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleExpand(caseId: string) {
    if (expandedCaseId === caseId) {
      setExpandedCaseId(null);
      return;
    }
    setExpandedCaseId(caseId);
    try {
      setParticipants(await getParticipants(caseId));
    } catch {
      setParticipants([]);
    }
    try {
      setCaseService(await getCaseService(caseId));
    } catch {
      setCaseService(null);
    }
    try {
      setCaseForms(await getGeneratedForms(caseId));
    } catch {
      setCaseForms([]);
    }
  }

  async function handleAddParticipant(caseId: string) {
    if (!newParticipantClientId) return;
    try {
      await addParticipant(caseId, newParticipantClientId, newParticipantRole);
      setParticipants(await getParticipants(caseId));
    } catch {
      setError(t("cases.error.participant"));
    }
  }

  async function handleApplyService(caseId: string) {
    if (!selectedServiceId) return;
    try {
      setCaseService(await applyServiceToCase(caseId, selectedServiceId));
      setCaseForms(await getGeneratedForms(caseId));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleToggleChecklist(caseId: string, itemId: string, done: boolean) {
    try {
      await toggleChecklistItem(caseId, itemId, done);
      setCaseService(await getCaseService(caseId));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleUpdateChecklistItem(
    caseId: string,
    itemId: string,
    payload: Partial<{ assigned_to_id: string | null; due_date: string | null; priority: string }>,
  ) {
    try {
      await updateChecklistItem(caseId, itemId, payload);
      setCaseService(await getCaseService(caseId));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleAdvanceStage(caseId: string) {
    try {
      setCaseService(await advanceStage(caseId));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  function clientName(clientId: string): string {
    const c = clients.find((cl) => cl.id === clientId);
    return c ? `${c.first_name} ${c.last_name}` : clientId;
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
            <Button onClick={() => setShowStaffForm((s) => !s)} variant="secondary">
              {showStaffForm ? t("cases.cancel") : t("cases.staff.new")}
            </Button>
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

        {showStaffForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleCreateStaff} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className={labelClass}>
                {t("cases.staff.name")}
                <input
                  required
                  value={staffName}
                  onChange={(e) => setStaffName(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("cases.staff.email")}
                <input
                  required
                  type="email"
                  value={staffEmail}
                  onChange={(e) => setStaffEmail(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("cases.staff.role")}
                <select value={staffRole} onChange={(e) => setStaffRole(e.target.value)} className={stackedInputClass}>
                  {USER_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {t(`enum.userRole.${r}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <Button type="submit" className="sm:col-span-3 mt-2">
                {t("cases.staff.save")}
              </Button>
            </form>
          </Card>
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
            onStatusChange={handleBoardStatusChange}
            onOpenCase={handleOpenFromBoard}
          />
        )}

        {view === "list" && (
        <div className="space-y-2">
          {cases.map((c) => (
            <Card key={c.id}>
              <button
                onClick={() => toggleExpand(c.id)}
                className="flex w-full items-center justify-between p-4 text-left text-sm"
              >
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{c.case_number}</span>
                <span className="flex flex-wrap items-center gap-2 text-zinc-500 dark:text-zinc-400">
                  <Badge value={c.status} label={t(`enum.caseStatus.${c.status}` as Parameters<typeof t>[0])} />
                  <span>{t(`enum.caseType.${c.case_type}` as Parameters<typeof t>[0])}</span>
                  <span>·</span>
                  <span>{userName(c.assigned_attorney_id)}</span>
                </span>
              </button>

              {expandedCaseId === c.id && (
                <div className="border-t border-zinc-100 p-4 dark:border-zinc-800">
                  <div className="mb-4 flex items-center gap-2">
                    <label className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                      {t("cases.assignedTo")}
                    </label>
                    <select
                      aria-label={t("cases.assignedTo")}
                      value={c.assigned_attorney_id ?? ""}
                      onChange={(e) => handleAssign(c.id, e.target.value)}
                      className={inputClass}
                    >
                      <option value="">{t("cases.unassigned")}</option>
                      {users.map((usr) => (
                        <option key={usr.id} value={usr.id}>
                          {usr.full_name} ({t(`enum.userRole.${usr.role}` as Parameters<typeof t>[0])})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
                    <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                      {t("cases.service.title")}
                    </h3>
                    {!caseService?.service ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          aria-label={t("cases.service.title")}
                          value={selectedServiceId}
                          onChange={(e) => setSelectedServiceId(e.target.value)}
                          className={inputClass}
                        >
                          <option value="">{t("cases.service.select")}</option>
                          {services.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name}
                            </option>
                          ))}
                        </select>
                        <Button
                          onClick={() => handleApplyService(c.id)}
                          disabled={!selectedServiceId}
                          variant="secondary"
                          className="whitespace-nowrap py-1.5"
                        >
                          {t("cases.service.apply")}
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                            {caseService.service.name}
                          </span>
                          <Button
                            onClick={() => handleAdvanceStage(c.id)}
                            variant="secondary"
                            className="whitespace-nowrap py-1 text-xs"
                          >
                            {t("cases.stage.next")}
                          </Button>
                        </div>

                        <div className="mb-3 flex flex-wrap gap-1">
                          {caseService.stages.map((stageName, idx) => (
                            <span
                              key={stageName}
                              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                idx === caseService.current_stage_index
                                  ? "bg-indigo-600 text-white"
                                  : idx < (caseService.current_stage_index ?? -1)
                                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
                                    : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                              }`}
                            >
                              {stageName}
                            </span>
                          ))}
                        </div>

                        <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">
                          {t("cases.checklist.title")}
                        </h4>
                        <ul className="mb-3 space-y-1">
                          {caseService.checklist.map((item) => (
                            <li key={item.id} className="text-sm">
                              <label className="flex min-h-11 cursor-pointer items-center gap-2 py-1">
                                <input
                                  type="checkbox"
                                  checked={item.done}
                                  onChange={(e) => handleToggleChecklist(c.id, item.id, e.target.checked)}
                                  className="h-4 w-4 shrink-0"
                                />
                                <span
                                  className={
                                    item.done
                                      ? "text-zinc-400 line-through dark:text-zinc-600"
                                      : "text-zinc-700 dark:text-zinc-300"
                                  }
                                >
                                  {item.label}
                                </span>
                              </label>
                              <div className="ml-6 flex flex-wrap items-center gap-2 pb-2">
                                <select
                                  aria-label={t("cases.checklist.assignee")}
                                  value={item.assigned_to_id ?? ""}
                                  onChange={(e) =>
                                    handleUpdateChecklistItem(c.id, item.id, {
                                      assigned_to_id: e.target.value || null,
                                    })
                                  }
                                  className="rounded-md border border-zinc-300 bg-white px-1.5 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                                >
                                  <option value="">{t("cases.unassigned")}</option>
                                  {users.map((u) => (
                                    <option key={u.id} value={u.id}>
                                      {u.full_name}
                                    </option>
                                  ))}
                                </select>
                                <input
                                  type="date"
                                  aria-label={t("cases.checklist.dueDate")}
                                  value={item.due_date ?? ""}
                                  onChange={(e) =>
                                    handleUpdateChecklistItem(c.id, item.id, {
                                      due_date: e.target.value || null,
                                    })
                                  }
                                  className="rounded-md border border-zinc-300 bg-white px-1.5 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                                />
                                <select
                                  aria-label={t("cases.checklist.priority")}
                                  value={item.priority}
                                  onChange={(e) =>
                                    handleUpdateChecklistItem(c.id, item.id, { priority: e.target.value })
                                  }
                                  className={`rounded-full border-0 px-2 py-1 text-xs font-medium ${
                                    PRIORITY_CLASSES[item.priority] ?? PRIORITY_CLASSES.medium
                                  }`}
                                >
                                  {CHECKLIST_PRIORITIES.map((p) => (
                                    <option key={p} value={p}>
                                      {t(`enum.priority.${p}` as Parameters<typeof t>[0])}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            </li>
                          ))}
                        </ul>

                        {caseForms.length > 0 && (
                          <>
                            <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">
                              {t("cases.generatedForms.title")}
                            </h4>
                            <ul className="space-y-1">
                              {caseForms.map((f) => (
                                <li key={f.id}>
                                  <Link
                                    href={`/forms/${f.id}`}
                                    className="text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                                  >
                                    {f.id.slice(0, 8)} — {f.status}
                                  </Link>
                                </li>
                              ))}
                            </ul>
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                    {t("cases.participants")}
                  </h3>
                  {participants.length === 0 && (
                    <p className="mb-3 text-sm text-zinc-500">{t("cases.participants.empty")}</p>
                  )}
                  <ul className="mb-3 space-y-1">
                    {participants.map((p) => (
                      <li key={p.id} className="text-sm text-zinc-700 dark:text-zinc-300">
                        {clientName(p.client_id)} —{" "}
                        <span className="text-zinc-500">
                          {t(`enum.participantRole.${p.role}` as Parameters<typeof t>[0])}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {clients.length === 0 ? (
                    <p className="mb-3 text-sm text-zinc-500">{t("cases.participants.noClients")}</p>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      <select
                        aria-label={t("cases.participants.selectClient")}
                        value={newParticipantClientId}
                        onChange={(e) => setNewParticipantClientId(e.target.value)}
                        className={inputClass}
                      >
                        {clients.map((cl) => (
                          <option key={cl.id} value={cl.id}>
                            {cl.first_name} {cl.last_name}
                          </option>
                        ))}
                      </select>
                      <select
                        aria-label={t("cases.participants.selectRole")}
                        value={newParticipantRole}
                        onChange={(e) => setNewParticipantRole(e.target.value)}
                        className={inputClass}
                      >
                        {PARTICIPANT_ROLES.map((r) => (
                          <option key={r} value={r}>
                            {t(`enum.participantRole.${r}` as Parameters<typeof t>[0])}
                          </option>
                        ))}
                      </select>
                      <Button onClick={() => handleAddParticipant(c.id)} variant="secondary" className="py-1.5">
                        {t("cases.participants.add")}
                      </Button>
                    </div>
                  )}
                  <div className="mt-2 flex justify-end">
                    <Link
                      href="/forms"
                      className="text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      {t("cases.goToForms")}
                    </Link>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
        )}
      </div>
    </AppShell>
  );
}
