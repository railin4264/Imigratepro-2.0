"use client";

import { useEffect, useState } from "react";
import {
  APPOINTMENT_TYPES,
  type Appointment,
  type Case,
  createAppointment,
  deleteAppointment,
  getAppointments,
  getCases,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function AppointmentsPage() {
  const { t, lang } = useTranslation();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [caseId, setCaseId] = useState("");
  const [appointmentType, setAppointmentType] = useState<string>("consultation");
  const [scheduledAt, setScheduledAt] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [nowMs, setNowMs] = useState(0);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Date.now() can't be read during render (impure); sync it after mount instead
    setNowMs(Date.now());
    const interval = setInterval(() => setNowMs(Date.now()), 60000);
    return () => clearInterval(interval);
  }, []);

  function load() {
    Promise.all([getAppointments(), getCases()])
      .then(([appts, caseList]) => {
        setAppointments(appts);
        setCases(caseList);
      })
      .catch(() => setError(t("appointments.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!caseId || !scheduledAt) return;
    setCreating(true);
    setError(null);
    try {
      await createAppointment(caseId, {
        appointment_type: appointmentType,
        scheduled_at: new Date(scheduledAt).toISOString(),
        location: location || undefined,
        notes: notes || undefined,
      });
      setScheduledAt("");
      setLocation("");
      setNotes("");
      load();
    } catch {
      setError(t("appointments.error.create"));
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm(t("common.confirmDelete"))) return;
    setBusyId(id);
    try {
      await deleteAppointment(id);
      setAppointments((prev) => prev.filter((a) => a.id !== id));
    } catch {
      setError(t("appointments.error.connect"));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("appointments.title")}
        </h1>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Card className="mb-6 p-5">
          <h2 className="mb-3 font-medium text-zinc-900 dark:text-zinc-50">{t("appointments.new")}</h2>
          {cases.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("appointments.noCases")}</p>
          ) : (
            <form onSubmit={handleCreate} className="space-y-3">
              <label className={labelClass}>
                {t("appointments.field.case")}
                <select
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  className={stackedInputClass}
                  required
                >
                  <option value="">{t("appointments.field.case.select")}</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("appointments.field.type")}
                <select
                  value={appointmentType}
                  onChange={(e) => setAppointmentType(e.target.value)}
                  className={stackedInputClass}
                >
                  {APPOINTMENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {t(`enum.appointmentType.${type}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("appointments.field.date")}
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  className={stackedInputClass}
                  required
                />
              </label>
              <label className={labelClass}>
                {t("appointments.field.location")}
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("appointments.field.notes")}
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <Button type="submit" disabled={creating}>
                {creating ? t("appointments.creating") : t("appointments.create")}
              </Button>
            </form>
          )}
        </Card>

        {appointments.length === 0 && !error && (
          <p className="text-zinc-500 dark:text-zinc-400">{t("appointments.empty")}</p>
        )}

        <div className="space-y-3">
          {appointments.map((a) => {
            const isPast = new Date(a.scheduled_at).getTime() < nowMs;
            return (
              <Card key={a.id} className="p-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">
                      {t(`enum.appointmentType.${a.appointment_type}` as Parameters<typeof t>[0])}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {a.case_number ?? "—"} · {new Date(a.scheduled_at).toLocaleString(lang)}
                      {a.location ? ` · ${a.location}` : ""}
                    </p>
                    {a.notes && <p className="mt-1 text-xs text-zinc-500">{a.notes}</p>}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge value={isPast ? "closed" : "filed"} label={t(isPast ? "appointments.past" : "appointments.upcoming")} />
                    {a.reminder_sent && (
                      <Badge value="extracted" label={t("appointments.reminderSent")} />
                    )}
                  </div>
                </div>
                <div className="mt-3 flex justify-end">
                  <Button variant="secondary" disabled={busyId === a.id} onClick={() => handleDelete(a.id)}>
                    {t("appointments.delete")}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
