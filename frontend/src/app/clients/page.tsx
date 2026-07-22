"use client";

import { useEffect, useState } from "react";
import {
  MARITAL_STATUS_OPTIONS,
  SEX_OPTIONS,
  type Client,
  type NewClient,
  activateClientPortal,
  createClient,
  deleteClient,
  getClients,
  updateClient,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
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

function clientToForm(client: Client): NewClient {
  return {
    first_name: client.first_name,
    last_name: client.last_name,
    email: client.email ?? "",
    phone: client.phone ?? "",
    mobile_phone: client.mobile_phone ?? "",
    date_of_birth: client.date_of_birth ?? "",
    country_of_birth: client.country_of_birth ?? "",
    nationality: client.nationality ?? "",
    a_number: client.a_number ?? "",
    ssn: client.ssn ?? "",
    sex: client.sex ?? "",
    marital_status: client.marital_status ?? "",
    address_line: client.address_line ?? "",
    city: client.city ?? "",
    state: client.state ?? "",
    zip_code: client.zip_code ?? "",
    country: client.country ?? "",
  };
}

function ClientFormFields({
  form,
  setForm,
  t,
}: {
  form: NewClient;
  setForm: (form: NewClient) => void;
  t: ReturnType<typeof useTranslation>["t"];
}) {
  return (
    <>
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
        <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className={inputClass} />
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
        <select value={form.sex} onChange={(e) => setForm({ ...form, sex: e.target.value })} className={inputClass}>
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
        <input value={form.ssn} onChange={(e) => setForm({ ...form, ssn: e.target.value })} className={inputClass} />
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
        <input value={form.a_number} onChange={(e) => setForm({ ...form, a_number: e.target.value })} className={inputClass} />
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
        <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className={inputClass} />
      </label>
      <label className={labelClass}>
        {t("clients.field.state")}
        <input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} className={inputClass} />
      </label>
      <label className={labelClass}>
        {t("clients.field.zip")}
        <input value={form.zip_code} onChange={(e) => setForm({ ...form, zip_code: e.target.value })} className={inputClass} />
      </label>
      <label className={labelClass}>
        {t("clients.field.country")}
        <input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} className={inputClass} />
      </label>
    </>
  );
}

export default function ClientsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canDelete = user?.role === "admin" || user?.role === "attorney";
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState<NewClient>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<NewClient>(emptyForm);
  const [editSaving, setEditSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [portalClientId, setPortalClientId] = useState<string | null>(null);
  const [portalPassword, setPortalPassword] = useState("");
  const [portalSaving, setPortalSaving] = useState(false);
  const [portalError, setPortalError] = useState<string | null>(null);
  const [portalActivatedFor, setPortalActivatedFor] = useState<string | null>(null);

  function load() {
    getClients()
      .then(setClients)
      .catch(() => setError(t("clients.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  function withoutBlankFields(source: NewClient): NewClient {
    return Object.fromEntries(Object.entries(source).filter(([, v]) => v !== "")) as NewClient;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createClient(withoutBlankFields(form));
      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch {
      setError(t("clients.error.create"));
    } finally {
      setSaving(false);
    }
  }

  function handleStartEdit(client: Client) {
    setEditingId(client.id);
    setEditForm(clientToForm(client));
    setShowForm(false);
  }

  async function handleUpdateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    setEditSaving(true);
    setError(null);
    try {
      await updateClient(editingId, withoutBlankFields(editForm));
      setEditingId(null);
      load();
    } catch {
      setError(t("clients.error.update"));
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(client: Client) {
    if (!window.confirm(t("clients.confirmDelete"))) return;
    setDeletingId(client.id);
    setError(null);
    try {
      await deleteClient(client.id);
      load();
    } catch {
      setError(t("clients.error.delete"));
    } finally {
      setDeletingId(null);
    }
  }

  function generatePassword(): string {
    // Not for cryptographic use elsewhere -- just a readable one-time
    // credential to hand the client, who resets it via "forgot password"
    // the first time they actually want to use the portal themselves.
    const bytes = new Uint8Array(9);
    window.crypto.getRandomValues(bytes);
    return btoa(String.fromCharCode(...bytes)).replace(/[+/=]/g, "").slice(0, 12);
  }

  function handleStartPortal(client: Client) {
    setPortalClientId(client.id);
    setPortalPassword(generatePassword());
    setPortalError(null);
    setPortalActivatedFor(null);
  }

  async function handleActivatePortal(client: Client) {
    if (!client.email) return;
    setPortalSaving(true);
    setPortalError(null);
    try {
      await activateClientPortal(client.email, portalPassword);
      setPortalActivatedFor(client.id);
    } catch {
      setPortalError(t("clients.portal.error"));
    } finally {
      setPortalSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {t("clients.title")}
          </h1>
          <Button
            onClick={() => {
              setEditingId(null);
              setShowForm((s) => !s);
            }}
            variant={showForm ? "secondary" : "primary"}
          >
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
              <ClientFormFields form={form} setForm={setForm} t={t} />
              <Button type="submit" disabled={saving} className="sm:col-span-2 mt-2">
                {saving ? t("clients.saving") : t("clients.save")}
              </Button>
            </form>
          </Card>
        )}

        {editingId && (
          <Card className="mb-6 p-5">
            <h2 className="mb-3 text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("clients.editTitle")}</h2>
            <form onSubmit={handleUpdateSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <ClientFormFields form={editForm} setForm={setEditForm} t={t} />
              <div className="flex gap-2 sm:col-span-2 mt-2">
                <Button type="submit" disabled={editSaving}>
                  {editSaving ? t("clients.saving") : t("clients.save")}
                </Button>
                <Button type="button" variant="secondary" onClick={() => setEditingId(null)}>
                  {t("clients.cancel")}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {portalClientId &&
          (() => {
            const portalClient = clients.find((c) => c.id === portalClientId);
            if (!portalClient) return null;
            const activated = portalActivatedFor === portalClient.id;
            return (
              <Card className="mb-6 p-5">
                <h2 className="mb-1 text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  {t("clients.portal.title")}
                </h2>
                <p className="mb-3 text-xs text-zinc-500 dark:text-zinc-400">
                  {portalClient.first_name} {portalClient.last_name} — {portalClient.email}
                </p>

                {activated ? (
                  <div className="space-y-3">
                    <p className="text-sm text-emerald-700 dark:text-emerald-400">{t("clients.portal.success")}</p>
                    <p className="rounded-lg bg-zinc-100 p-3 font-mono text-sm dark:bg-zinc-800">{portalPassword}</p>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">{t("clients.portal.shareNote")}</p>
                    <Button type="button" variant="secondary" onClick={() => setPortalClientId(null)}>
                      {t("clients.cancel")}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {portalError && (
                      <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                        {portalError}
                      </p>
                    )}
                    <label className={labelClass}>
                      {t("clients.portal.password")}
                      <input
                        type="text"
                        value={portalPassword}
                        onChange={(e) => setPortalPassword(e.target.value)}
                        className={`${inputClass} font-mono`}
                        minLength={8}
                        required
                      />
                    </label>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        disabled={portalSaving || portalPassword.length < 8}
                        onClick={() => handleActivatePortal(portalClient)}
                      >
                        {portalSaving ? t("clients.portal.saving") : t("clients.portal.activate")}
                      </Button>
                      <Button type="button" variant="secondary" onClick={() => setPortalClientId(null)}>
                        {t("clients.cancel")}
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            );
          })()}

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
                    <th className="p-3 font-medium text-zinc-500 dark:text-zinc-400">{t("clients.col.actions")}</th>
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
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => handleStartEdit(client)}
                            className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                          >
                            {t("clients.edit")}
                          </button>
                          {client.email && (
                            <button
                              type="button"
                              onClick={() => handleStartPortal(client)}
                              className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                            >
                              {t("clients.portal")}
                            </button>
                          )}
                          {canDelete && (
                            <button
                              type="button"
                              onClick={() => handleDelete(client)}
                              disabled={deletingId === client.id}
                              className="font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                            >
                              {deletingId === client.id ? t("clients.deleting") : t("clients.delete")}
                            </button>
                          )}
                        </div>
                      </td>
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
