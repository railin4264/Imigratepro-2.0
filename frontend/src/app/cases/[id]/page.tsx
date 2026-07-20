"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  CHECKLIST_PRIORITIES,
  PARTICIPANT_ROLES,
  type Appointment,
  type Case,
  type CaseServiceView,
  type CaseTimeline as CaseTimelineData,
  type Client,
  type GeneratedForm,
  type Invoice,
  type Participant,
  type Service,
  type User,
  addParticipant,
  advanceStage,
  applyServiceToCase,
  deleteCase,
  getCase,
  getCaseAppointments,
  getCaseService,
  getCaseTimeline,
  getClients,
  getGeneratedForms,
  getInvoices,
  getParticipants,
  getServices,
  getUsers,
  toggleChecklistItem,
  updateCase,
  updateChecklistItem,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CaseTimeline } from "@/components/CaseTimeline";
import { GapAnalysisPanel } from "@/components/GapAnalysisPanel";
import { RfePanel } from "@/components/RfePanel";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";

const PRIORITY_CLASSES: Record<string, string> = {
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  medium: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  high: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
};

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const { user } = useAuth();
  const canManage = user?.role === "admin" || user?.role === "attorney";

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [status, setStatus] = useState<"loading" | "idle" | "notFound" | "error">("loading");
  const [clients, setClients] = useState<Client[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const activeUsers = users.filter((u) => u.is_active);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [participants, setParticipants] = useState<Participant[]>([]);
  const [newParticipantClientId, setNewParticipantClientId] = useState("");
  const [newParticipantRole, setNewParticipantRole] = useState<string>(PARTICIPANT_ROLES[0]);

  const [services, setServices] = useState<Service[]>([]);
  const [caseService, setCaseService] = useState<CaseServiceView | null>(null);
  const [caseForms, setCaseForms] = useState<GeneratedForm[]>([]);
  const [caseAppointments, setCaseAppointments] = useState<Appointment[]>([]);
  const [caseInvoices, setCaseInvoices] = useState<Invoice[]>([]);
  const [caseTimeline, setCaseTimeline] = useState<CaseTimelineData | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const c = await getCase(params.id);
        setCaseData(c);
        setStatus("idle");
      } catch (e) {
        setStatus(e instanceof Error && e.message.includes("404") ? "notFound" : "error");
        return;
      }

      const [clientList, userList, serviceList] = await Promise.all([getClients(), getUsers(), getServices()]);
      setClients(clientList);
      setUsers(userList);
      setServices(serviceList);
      if (clientList.length > 0) setNewParticipantClientId(clientList[0].id);
      if (serviceList.length > 0) setSelectedServiceId(serviceList[0].id);

      try {
        setParticipants(await getParticipants(params.id));
      } catch {
        setParticipants([]);
      }
      try {
        setCaseService(await getCaseService(params.id));
      } catch {
        setCaseService(null);
      }
      try {
        setCaseForms(await getGeneratedForms(params.id));
      } catch {
        setCaseForms([]);
      }
      try {
        setCaseAppointments(await getCaseAppointments(params.id));
      } catch {
        setCaseAppointments([]);
      }
      try {
        setCaseInvoices(await getInvoices(params.id));
      } catch {
        setCaseInvoices([]);
      }
      try {
        setCaseTimeline(await getCaseTimeline(params.id));
      } catch {
        setCaseTimeline(null);
      }
    }
    load();
  }, [params.id]);

  function userName(userId: string | null): string {
    if (!userId) return t("cases.unassigned");
    const u = users.find((usr) => usr.id === userId);
    return u ? u.full_name : userId;
  }

  function clientName(clientId: string): string {
    const c = clients.find((cl) => cl.id === clientId);
    return c ? `${c.first_name} ${c.last_name}` : clientId;
  }

  async function handleAssign(attorneyId: string) {
    if (!caseData) return;
    try {
      setCaseData(await updateCase(caseData.id, { assigned_attorney_id: attorneyId || null }));
    } catch {
      setError(t("cases.error.assign"));
    }
  }

  async function handleAddParticipant() {
    if (!caseData || !newParticipantClientId) return;
    try {
      await addParticipant(caseData.id, newParticipantClientId, newParticipantRole);
      setParticipants(await getParticipants(caseData.id));
    } catch {
      setError(t("cases.error.participant"));
    }
  }

  async function handleApplyService() {
    if (!caseData || !selectedServiceId) return;
    try {
      setCaseService(await applyServiceToCase(caseData.id, selectedServiceId));
      setCaseForms(await getGeneratedForms(caseData.id));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleToggleChecklist(itemId: string, done: boolean) {
    if (!caseData) return;
    try {
      await toggleChecklistItem(caseData.id, itemId, done);
      setCaseService(await getCaseService(caseData.id));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleUpdateChecklistItem(
    itemId: string,
    payload: Partial<{ assigned_to_id: string | null; due_date: string | null; priority: string }>,
  ) {
    if (!caseData) return;
    try {
      await updateChecklistItem(caseData.id, itemId, payload);
      setCaseService(await getCaseService(caseData.id));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleAdvanceStage() {
    if (!caseData) return;
    try {
      setCaseService(await advanceStage(caseData.id));
    } catch {
      setError(t("cases.service.error.apply"));
    }
  }

  async function handleDelete() {
    if (!caseData) return;
    if (!window.confirm(t("caseDetail.confirmDelete"))) return;
    setDeleting(true);
    try {
      await deleteCase(caseData.id);
      router.push("/cases");
    } catch {
      setError(t("caseDetail.error.delete"));
      setDeleting(false);
    }
  }

  if (status === "loading") {
    return (
      <AppShell>
        <div className="text-zinc-500 dark:text-zinc-400">{t("caseDetail.loading")}</div>
      </AppShell>
    );
  }

  if (status === "notFound") {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl">
          <p className="mb-4 text-zinc-700 dark:text-zinc-300">{t("caseDetail.notFound")}</p>
          <Link href="/cases" className="text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
            {t("nav.back")}
          </Link>
        </div>
      </AppShell>
    );
  }

  if (status === "error" || !caseData) {
    return (
      <AppShell>
        <div className="text-red-700 dark:text-red-300">{t("cases.error.connect")}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              {caseData.case_number}
              <Badge
                value={caseData.status}
                label={t(`enum.caseStatus.${caseData.status}` as Parameters<typeof t>[0])}
              />
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {t(`enum.caseType.${caseData.case_type}` as Parameters<typeof t>[0])}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {canManage && (
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="text-sm font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
              >
                {deleting ? t("caseDetail.deleting") : t("caseDetail.delete")}
              </button>
            )}
            <Link href="/cases" className="text-sm text-zinc-500 hover:underline dark:text-zinc-400">
              {t("nav.back")}
            </Link>
          </div>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Card className="mb-4 p-4">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              {t("cases.assignedTo")}
            </label>
            <select
              aria-label={t("cases.assignedTo")}
              value={caseData.assigned_attorney_id ?? ""}
              onChange={(e) => handleAssign(e.target.value)}
              className={inputClass}
            >
              <option value="">{t("cases.unassigned")}</option>
              {caseData.assigned_attorney_id && !activeUsers.some((u) => u.id === caseData.assigned_attorney_id) && (
                <option value={caseData.assigned_attorney_id}>
                  {userName(caseData.assigned_attorney_id)} ({t("team.inactive")})
                </option>
              )}
              {activeUsers.map((usr) => (
                <option key={usr.id} value={usr.id}>
                  {usr.full_name} ({t(`enum.userRole.${usr.role}` as Parameters<typeof t>[0])})
                </option>
              ))}
            </select>
          </div>
        </Card>

        {caseTimeline && (
          <Card className="mb-4 overflow-x-auto p-3">
            <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
              {t("client.timeline.title")}
            </h3>
            <CaseTimeline timeline={caseTimeline} />
          </Card>
        )}

        <GapAnalysisPanel
          caseId={caseData.id}
          refreshKey={`${participants.length}-${caseService?.current_stage_index ?? -1}-${
            caseService?.checklist.filter((i) => i.done).length ?? 0
          }`}
        />
        <RfePanel caseId={caseData.id} />

        <Card className="mb-4 p-4">
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
                onClick={handleApplyService}
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
                <Button onClick={handleAdvanceStage} variant="secondary" className="whitespace-nowrap py-1 text-xs">
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
                        onChange={(e) => handleToggleChecklist(item.id, e.target.checked)}
                        className="h-4 w-4 shrink-0"
                      />
                      <span
                        className={
                          item.done ? "text-zinc-400 line-through dark:text-zinc-600" : "text-zinc-700 dark:text-zinc-300"
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
                          handleUpdateChecklistItem(item.id, { assigned_to_id: e.target.value || null })
                        }
                        className="rounded-md border border-zinc-300 bg-white px-1.5 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                      >
                        <option value="">{t("cases.unassigned")}</option>
                        {item.assigned_to_id && !activeUsers.some((u) => u.id === item.assigned_to_id) && (
                          <option value={item.assigned_to_id}>
                            {users.find((u) => u.id === item.assigned_to_id)?.full_name ?? item.assigned_to_id}
                          </option>
                        )}
                        {activeUsers.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.full_name}
                          </option>
                        ))}
                      </select>
                      <input
                        type="date"
                        aria-label={t("cases.checklist.dueDate")}
                        value={item.due_date ?? ""}
                        onChange={(e) => handleUpdateChecklistItem(item.id, { due_date: e.target.value || null })}
                        className="rounded-md border border-zinc-300 bg-white px-1.5 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                      />
                      <select
                        aria-label={t("cases.checklist.priority")}
                        value={item.priority}
                        onChange={(e) => handleUpdateChecklistItem(item.id, { priority: e.target.value })}
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
                          {f.form_code} — {t(`enum.formStatus.${f.status}` as Parameters<typeof t>[0])}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}
        </Card>

        <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Card className="p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
              {t("cases.appointments.title")}
            </h3>
            {caseAppointments.length === 0 ? (
              <p className="text-sm text-zinc-500">{t("cases.appointments.empty")}</p>
            ) : (
              <ul className="space-y-1">
                {caseAppointments.map((a) => (
                  <li key={a.id} className="text-sm text-zinc-700 dark:text-zinc-300">
                    {t(`enum.appointmentType.${a.appointment_type}` as Parameters<typeof t>[0])} —{" "}
                    <span className="text-zinc-500">{new Date(a.scheduled_at).toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            )}
            <Link
              href="/appointments"
              className="mt-1 inline-block text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              {t("cases.goToAppointments")}
            </Link>
          </Card>

          <Card className="p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
              {t("cases.invoices.title")}
            </h3>
            {caseInvoices.length === 0 ? (
              <p className="text-sm text-zinc-500">{t("cases.invoices.empty")}</p>
            ) : (
              <ul className="space-y-1">
                {caseInvoices.map((inv) => (
                  <li key={inv.id} className="text-sm text-zinc-700 dark:text-zinc-300">
                    {inv.invoice_number} —{" "}
                    <span className="text-zinc-500">
                      {(inv.amount - inv.amount_paid).toFixed(2)} {t("billing.balance").toLowerCase()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <Link
              href="/billing"
              className="mt-1 inline-block text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              {t("cases.goToBilling")}
            </Link>
          </Card>
        </div>

        <Card className="p-4">
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
              <Button onClick={handleAddParticipant} variant="secondary" className="py-1.5">
                {t("cases.participants.add")}
              </Button>
            </div>
          )}
          <div className="mt-2 flex justify-end">
            <Link
              href={`/forms?case_id=${caseData.id}`}
              className="text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              {t("cases.goToForms")}
            </Link>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
