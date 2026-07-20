"use client";

import { useEffect, useState } from "react";
import {
  CASE_STATUSES,
  USER_ROLES,
  type UserWorkload,
  createUser,
  getUserWorkload,
  setUserPassword,
  updateUser,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 w-full ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

const STATUS_BADGE_ORDER = CASE_STATUSES.filter((s) => s !== "closed" && s !== "denied");

export default function TeamPage() {
  const { t } = useTranslation();
  const { user: me } = useAuth();
  const isAdmin = me?.role === "admin";

  const [workload, setWorkload] = useState<UserWorkload[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<string>("paralegal");
  const [barNumber, setBarNumber] = useState("");
  const [firmName, setFirmName] = useState("");
  const [phone, setPhone] = useState("");

  const [passwordTargetId, setPasswordTargetId] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");

  function load() {
    getUserWorkload()
      .then(setWorkload)
      .catch(() => setError(t("team.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createUser({
        full_name: name,
        email,
        role,
        bar_number: barNumber || undefined,
        firm_name: firmName || undefined,
        phone: phone || undefined,
      });
      setName("");
      setEmail("");
      setBarNumber("");
      setFirmName("");
      setPhone("");
      setShowForm(false);
      load();
    } catch {
      setError(t("team.error.create"));
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(userId: string, newRole: string) {
    try {
      await updateUser(userId, { role: newRole });
      load();
    } catch {
      setError(t("team.error.update"));
    }
  }

  async function handleToggleActive(userId: string, isActive: boolean) {
    try {
      await updateUser(userId, { is_active: isActive });
      load();
    } catch {
      setError(t("team.error.update"));
    }
  }

  async function handleSetPassword(userId: string) {
    if (newPassword.length < 8) {
      setError(t("team.error.passwordLength"));
      return;
    }
    try {
      await setUserPassword(userId, newPassword);
      setPasswordTargetId(null);
      setNewPassword("");
    } catch {
      setError(t("team.error.update"));
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              {t("team.title")}
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{t("team.subtitle")}</p>
          </div>
          {isAdmin && (
            <Button onClick={() => setShowForm((s) => !s)} variant={showForm ? "secondary" : "primary"}>
              {showForm ? t("cases.cancel") : t("team.new")}
            </Button>
          )}
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {showForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className={labelClass}>
                {t("cases.staff.name")}
                <input required value={name} onChange={(e) => setName(e.target.value)} className={stackedInputClass} />
              </label>
              <label className={labelClass}>
                {t("cases.staff.email")}
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("cases.staff.role")}
                <select value={role} onChange={(e) => setRole(e.target.value)} className={stackedInputClass}>
                  {USER_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {t(`enum.userRole.${r}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("team.field.barNumber")}
                <input value={barNumber} onChange={(e) => setBarNumber(e.target.value)} className={stackedInputClass} />
              </label>
              <label className={labelClass}>
                {t("team.field.firmName")}
                <input value={firmName} onChange={(e) => setFirmName(e.target.value)} className={stackedInputClass} />
              </label>
              <label className={labelClass}>
                {t("clients.field.phone")}
                <input value={phone} onChange={(e) => setPhone(e.target.value)} className={stackedInputClass} />
              </label>
              <Button type="submit" disabled={saving} className="sm:col-span-3 mt-2">
                {saving ? t("cases.saving") : t("cases.staff.save")}
              </Button>
            </form>
          </Card>
        )}

        {workload.length === 0 && !error && <p className="text-zinc-500 dark:text-zinc-400">{t("team.empty")}</p>}

        <div className="space-y-3">
          {workload.map((w) => (
            <Card key={w.user.id} className="p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-zinc-900 dark:text-zinc-50">{w.user.full_name}</span>
                    {isAdmin ? (
                      <select
                        aria-label={t("cases.staff.role")}
                        value={w.user.role}
                        onChange={(e) => handleRoleChange(w.user.id, e.target.value)}
                        className="rounded-md border border-zinc-300 bg-white px-1.5 py-0.5 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                      >
                        {USER_ROLES.map((r) => (
                          <option key={r} value={r}>
                            {t(`enum.userRole.${r}` as Parameters<typeof t>[0])}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <Badge value={w.user.role} label={t(`enum.userRole.${w.user.role}` as Parameters<typeof t>[0])} />
                    )}
                    {!w.user.is_active && <Badge value="closed" label={t("team.inactive")} />}
                  </div>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{w.user.email}</p>
                </div>

                {isAdmin && (
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      onClick={() => handleToggleActive(w.user.id, !w.user.is_active)}
                      variant="secondary"
                      className="py-1 text-xs"
                    >
                      {w.user.is_active ? t("team.deactivate") : t("team.activate")}
                    </Button>
                    {passwordTargetId === w.user.id ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder={t("team.newPassword")}
                          aria-label={t("team.newPassword")}
                          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                        />
                        <Button onClick={() => handleSetPassword(w.user.id)} variant="secondary" className="py-1 text-xs">
                          {t("team.savePassword")}
                        </Button>
                      </div>
                    ) : (
                      <Button
                        onClick={() => {
                          setPasswordTargetId(w.user.id);
                          setNewPassword("");
                        }}
                        variant="secondary"
                        className="py-1 text-xs"
                      >
                        {t("team.resetPassword")}
                      </Button>
                    )}
                  </div>
                )}
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 font-medium text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300">
                  {w.assigned_case_count} {t("team.cases")}
                </span>
                {STATUS_BADGE_ORDER.filter((s) => w.cases_by_status[s]).map((s) => (
                  <span key={s} className="text-zinc-500 dark:text-zinc-400">
                    {w.cases_by_status[s]} {t(`enum.caseStatus.${s}` as Parameters<typeof t>[0])}
                  </span>
                ))}
                {w.open_rfe_count > 0 && (
                  <span className="rounded-full bg-orange-50 px-2.5 py-1 font-medium text-orange-700 dark:bg-orange-950/50 dark:text-orange-300">
                    {w.open_rfe_count} {t("team.openRfes")}
                  </span>
                )}
                {w.overdue_checklist_count > 0 && (
                  <span className="rounded-full bg-red-50 px-2.5 py-1 font-medium text-red-700 dark:bg-red-950/50 dark:text-red-300">
                    {w.overdue_checklist_count} {t("team.overdueChecklist")}
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
