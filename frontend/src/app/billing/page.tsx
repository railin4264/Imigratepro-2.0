"use client";

import { useEffect, useState } from "react";
import {
  type Case,
  type Invoice,
  type InvoiceDetail,
  PAYMENT_METHODS,
  addPayment,
  createInvoice,
  deleteInvoice,
  deletePayment,
  getCases,
  getInvoice,
  getInvoices,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { formatMoney as money } from "@/lib/format";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const stackedInputClass = `mt-1 ${inputClass}`;
const labelClass = "block text-xs font-medium text-zinc-600 dark:text-zinc-400";

export default function BillingPage() {
  const { t, lang } = useTranslation();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [caseId, setCaseId] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [creating, setCreating] = useState(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, InvoiceDetail>>({});
  const [busyId, setBusyId] = useState<string | null>(null);

  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<string>("card");
  const [paymentNotes, setPaymentNotes] = useState("");
  const [recordingPayment, setRecordingPayment] = useState(false);

  function load() {
    Promise.all([getInvoices(), getCases()])
      .then(([invoiceList, caseList]) => {
        setInvoices(invoiceList);
        setCases(caseList);
      })
      .catch(() => setError(t("billing.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!caseId || !amount) return;
    setCreating(true);
    setError(null);
    try {
      await createInvoice(caseId, {
        description: description || undefined,
        amount: parseFloat(amount),
        due_date: dueDate || undefined,
      });
      setDescription("");
      setAmount("");
      setDueDate("");
      load();
    } catch {
      setError(t("billing.error.create"));
    } finally {
      setCreating(false);
    }
  }

  async function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!details[id]) {
      try {
        const detail = await getInvoice(id);
        setDetails((prev) => ({ ...prev, [id]: detail }));
      } catch {
        setError(t("billing.error.connect"));
      }
    }
  }

  async function handleDeleteInvoice(id: string) {
    if (!window.confirm(t("common.confirmDelete"))) return;
    setBusyId(id);
    try {
      await deleteInvoice(id);
      setInvoices((prev) => prev.filter((i) => i.id !== id));
    } catch {
      setError(t("billing.error.connect"));
    } finally {
      setBusyId(null);
    }
  }

  async function handleAddPayment(e: React.FormEvent, invoiceId: string) {
    e.preventDefault();
    if (!paymentAmount) return;
    setRecordingPayment(true);
    try {
      const detail = await addPayment(invoiceId, {
        amount: parseFloat(paymentAmount),
        method: paymentMethod,
        notes: paymentNotes || undefined,
      });
      setDetails((prev) => ({ ...prev, [invoiceId]: detail }));
      setInvoices((prev) => prev.map((i) => (i.id === invoiceId ? detail : i)));
      setPaymentAmount("");
      setPaymentNotes("");
    } catch {
      setError(t("billing.error.connect"));
    } finally {
      setRecordingPayment(false);
    }
  }

  async function handleDeletePayment(invoiceId: string, paymentId: string) {
    if (!window.confirm(t("common.confirmDelete"))) return;
    setBusyId(paymentId);
    try {
      const detail = await deletePayment(invoiceId, paymentId);
      setDetails((prev) => ({ ...prev, [invoiceId]: detail }));
      setInvoices((prev) => prev.map((i) => (i.id === invoiceId ? detail : i)));
    } catch {
      setError(t("billing.error.connect"));
    } finally {
      setBusyId(null);
    }
  }

  const casesById = Object.fromEntries(cases.map((c) => [c.id, c]));

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("billing.title")}
        </h1>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Card className="mb-6 p-5">
          <h2 className="mb-3 font-medium text-zinc-900 dark:text-zinc-50">{t("billing.new")}</h2>
          {cases.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("billing.noCases")}</p>
          ) : (
            <form onSubmit={handleCreate} className="space-y-3">
              <label className={labelClass}>
                {t("billing.field.case")}
                <select
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  className={stackedInputClass}
                  required
                >
                  <option value="">{t("billing.field.case.select")}</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                {t("billing.field.description")}
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <label className={labelClass}>
                {t("billing.field.amount")}
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className={stackedInputClass}
                  required
                />
              </label>
              <label className={labelClass}>
                {t("billing.field.dueDate")}
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className={stackedInputClass}
                />
              </label>
              <Button type="submit" disabled={creating}>
                {creating ? t("billing.creating") : t("billing.create")}
              </Button>
            </form>
          )}
        </Card>

        {invoices.length === 0 && !error && <p className="text-zinc-500 dark:text-zinc-400">{t("billing.empty")}</p>}

        <div className="space-y-3">
          {invoices.map((inv) => {
            const detail = details[inv.id];
            const balance = inv.amount - inv.amount_paid;
            const caseNumber = casesById[inv.case_id]?.case_number ?? inv.case_number;

            return (
              <Card key={inv.id} className="p-5">
                <button onClick={() => toggleExpand(inv.id)} className="flex w-full items-center justify-between gap-3 text-left">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">
                      {inv.invoice_number} · {caseNumber ?? "—"}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {inv.description || "—"}
                      {inv.due_date ? ` · ${t("billing.field.dueDate")}: ${inv.due_date}` : ""}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                      {money(inv.amount)} · {t("billing.balance")} {money(balance)}
                    </p>
                    <div className="mt-1 flex justify-end">
                      <Badge value={inv.status} label={t(`enum.invoiceStatus.${inv.status}` as Parameters<typeof t>[0])} />
                    </div>
                  </div>
                </button>

                {expandedId === inv.id && (
                  <div className="mt-4 space-y-4 border-t border-zinc-100 pt-4 dark:border-zinc-800">
                    <div>
                      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                        {t("billing.payments")}
                      </p>
                      {!detail || detail.payments.length === 0 ? (
                        <p className="text-sm text-zinc-500">{t("billing.noPayments")}</p>
                      ) : (
                        <ul className="space-y-1.5">
                          {detail.payments.map((p) => (
                            <li
                              key={p.id}
                              className="flex items-center justify-between rounded-lg bg-zinc-50 px-3 py-2 text-sm dark:bg-zinc-800/50"
                            >
                              <span>
                                {money(p.amount)} · {t(`enum.paymentMethod.${p.method}` as Parameters<typeof t>[0])} ·{" "}
                                {new Date(p.paid_at).toLocaleDateString(lang)}
                                {p.notes ? ` · ${p.notes}` : ""}
                              </span>
                              <button
                                disabled={busyId === p.id}
                                onClick={() => handleDeletePayment(inv.id, p.id)}
                                className="text-xs font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                              >
                                {t("billing.delete")}
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <form onSubmit={(e) => handleAddPayment(e, inv.id)} className="flex flex-wrap items-end gap-2">
                      <label className={labelClass}>
                        {t("billing.field.paymentAmount")}
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={paymentAmount}
                          onChange={(e) => setPaymentAmount(e.target.value)}
                          className={`${stackedInputClass} w-28`}
                          required
                        />
                      </label>
                      <label className={labelClass}>
                        {t("billing.field.paymentMethod")}
                        <select
                          value={paymentMethod}
                          onChange={(e) => setPaymentMethod(e.target.value)}
                          className={`${stackedInputClass} w-36`}
                        >
                          {PAYMENT_METHODS.map((m) => (
                            <option key={m} value={m}>
                              {t(`enum.paymentMethod.${m}` as Parameters<typeof t>[0])}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className={labelClass}>
                        {t("billing.field.paymentNotes")}
                        <input
                          type="text"
                          value={paymentNotes}
                          onChange={(e) => setPaymentNotes(e.target.value)}
                          className={`${stackedInputClass} w-40`}
                        />
                      </label>
                      <Button type="submit" variant="secondary" disabled={recordingPayment}>
                        {recordingPayment ? t("billing.recording") : t("billing.recordPayment")}
                      </Button>
                    </form>

                    <div className="flex justify-end">
                      <Button variant="secondary" disabled={busyId === inv.id} onClick={() => handleDeleteInvoice(inv.id)}>
                        {t("billing.delete")}
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
