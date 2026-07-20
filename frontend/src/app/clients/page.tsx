"use client";

import { useEffect, useState } from "react";
import {
  MARITAL_STATUS_OPTIONS,
  SEX_OPTIONS,
  type Client,
  type NewClient,
  createClient,
  getClients,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

const emptyForm: NewClient = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  mobile_phone: "",
  date_of_birth: "",
  country_of_birth: "",
  nationality: "",
  a_number: "",
  ssn: "",
  sex: "",
  marital_status: "",
  address_line: "",
  city: "",
  state: "",
  zip_code: "",
  country: "",
};

export default function ClientsPage() {
  const { t } = useTranslation();
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState<NewClient>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  function load() {
    getClients()
      .then(setClients)
      .catch(() => setError(t("clients.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(form).filter(([, v]) => v !== "")
      ) as NewClient;
      await createClient(payload);
      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch {
      setError(t("clients.error.create"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {t("clients.title")}
          </h1>
          <Button onClick={() => setShowForm((s) => !s)} variant={showForm ? "secondary" : "primary"}>
            {showForm ? t("clients.cancel") : t("clients.new")}
          </Button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {showForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className={labelClass}>
                {t("clients.field.firstName")}
                <input
                  required
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.lastName")}
                <input
                  required
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.email")}
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.phone")}
                <input
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.mobile")}
                <input
                  value={form.mobile_phone}
                  onChange={(e) => setForm({ ...form, mobile_phone: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.sex")}
                <select
                  value={form.sex}
                  onChange={(e) => setForm({ ...form, sex: e.target.value })}
                  className={inputClass}
                >
                  <option value="">{t("common.select")}</option>
                  {SEX_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s === "male" ? t("clients.field.sex.male") : t("clients.field.sex.female")}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("clients.field.maritalStatus")}
                <select
                  value={form.marital_status}
                  onChange={(e) => setForm({ ...form, marital_status: e.target.value })}
                  className={inputClass}
                >
                  <option value="">{t("common.select")}</option>
                  {MARITAL_STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {t(`enum.maritalStatus.${s}` as Parameters<typeof t>[0])}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("clients.field.ssn")}
                <input
                  value={form.ssn}
                  onChange={(e) => setForm({ ...form, ssn: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.dob")}
                <input
                  type="date"
                  value={form.date_of_birth}
                  onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.countryOfBirth")}
                <input
                  value={form.country_of_birth}
                  onChange={(e) => setForm({ ...form, country_of_birth: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.nationality")}
                <input
                  value={form.nationality}
                  onChange={(e) => setForm({ ...form, nationality: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.aNumber")}
                <input
                  value={form.a_number}
                  onChange={(e) => setForm({ ...form, a_number: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.address")}
                <input
                  value={form.address_line}
                  onChange={(e) => setForm({ ...form, address_line: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.city")}
                <input
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.state")}
                <input
                  value={form.state}
                  onChange={(e) => setForm({ ...form, state: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.zip")}
                <input
                  value={form.zip_code}
                  onChange={(e) => setForm({ ...form, zip_code: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("clients.field.country")}
                <input
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  className={inputClass}
                />
              </label>
              <Button type="submit" disabled={saving} className="sm:col-span-2 mt-2">
                {saving ? t("clients.saving") : t("clients.save")}
              </Button>
            </form>
          </Card>
        )}

        {clients.length === 0 && !error && (
          <p className="text-zinc-500 dark:text-zinc-400">{t("clients.empty")}</p>
        )}

        {clients.length > 0 && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-140 border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-800">
                    <th className="p-3 font-medium text-zinc-500 dark:text-zinc-400">{t("clients.col.name")}</th>
                    <th className="p-3 font-medium text-zinc-500 dark:text-zinc-400">{t("clients.col.email")}</th>
                    <th className="p-3 font-medium text-zinc-500 dark:text-zinc-400">{t("clients.col.phone")}</th>
                    <th className="p-3 font-medium text-zinc-500 dark:text-zinc-400">
                      {t("clients.col.nationality")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((client) => (
                    <tr key={client.id} className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
                      <td className="p-3 text-zinc-900 dark:text-zinc-50">
                        {client.first_name} {client.last_name}
                      </td>
                      <td className="p-3 text-zinc-600 dark:text-zinc-300">{client.email ?? "—"}</td>
                      <td className="p-3 text-zinc-600 dark:text-zinc-300">{client.phone ?? "—"}</td>
                      <td className="p-3 text-zinc-600 dark:text-zinc-300">{client.nationality ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
