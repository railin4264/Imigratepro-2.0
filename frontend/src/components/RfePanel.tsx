"use client";

import { useEffect, useState } from "react";
import {
  RFE_EVIDENCE_STATUSES,
  RFE_STATUSES,
  type RFE,
  type RFEDetail,
  type RFESuggestion,
  addRfeEvidenceItem,
  createRfe,
  deleteRfe,
  deleteRfeEvidenceItem,
  getCaseRfes,
  getRfe,
  getRfeAiStatus,
  suggestRfeEvidence,
  updateRfe,
  updateRfeEvidenceItem,
} from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";

export function RfePanel({ caseId }: { caseId: string }) {
  const { t } = useTranslation();
  const [rfes, setRfes] = useState<RFE[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RFEDetail | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [receivedDate, setReceivedDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [rawText, setRawText] = useState("");
  const [aiConfigured, setAiConfigured] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestions, setSuggestions] = useState<RFESuggestion[]>([]);
  const [newEvidence, setNewEvidence] = useState("");

  function load() {
    getCaseRfes(caseId)
      .then(setRfes)
      .catch(() => setRfes([]));
  }

  useEffect(() => {
    load();
    getRfeAiStatus()
      .then((s) => setAiConfigured(s.configured))
      .catch(() => setAiConfigured(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load only on caseId change
  }, [caseId]);

  async function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      setSuggestions([]);
      return;
    }
    setExpandedId(id);
    setSuggestions([]);
    try {
      setDetail(await getRfe(id));
    } catch {
      setDetail(null);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!receivedDate) return;
    await createRfe(caseId, {
      received_date: receivedDate,
      response_due_date: dueDate || undefined,
      raw_text: rawText || undefined,
    });
    setReceivedDate("");
    setDueDate("");
    setRawText("");
    setShowForm(false);
    load();
  }

  async function handleDelete(id: string) {
    if (!window.confirm(t("common.confirmDelete"))) return;
    await deleteRfe(id);
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
    }
    load();
  }

  async function handleStatusChange(id: string, status: string) {
    await updateRfe(id, { status });
    load();
    if (expandedId === id) setDetail(await getRfe(id));
  }

  async function handleAddEvidence(rfeId: string) {
    if (!newEvidence.trim()) return;
    await addRfeEvidenceItem(rfeId, newEvidence.trim());
    setNewEvidence("");
    setDetail(await getRfe(rfeId));
    load();
  }

  async function handleToggleEvidence(rfeId: string, itemId: string, status: string) {
    await updateRfeEvidenceItem(rfeId, itemId, { status });
    setDetail(await getRfe(rfeId));
    load();
  }

  async function handleDeleteEvidence(rfeId: string, itemId: string) {
    await deleteRfeEvidenceItem(rfeId, itemId);
    setDetail(await getRfe(rfeId));
    load();
  }

  async function handleSuggest(rfeId: string) {
    setSuggesting(true);
    try {
      const res = await suggestRfeEvidence(rfeId);
      setSuggestions(res.suggestions);
    } catch {
      setSuggestions([]);
    } finally {
      setSuggesting(false);
    }
  }

  async function acceptSuggestion(rfeId: string, description: string) {
    await addRfeEvidenceItem(rfeId, description);
    setSuggestions((prev) => prev.filter((s) => s.description !== description));
    setDetail(await getRfe(rfeId));
    load();
  }

  return (
    <div className="mb-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-500">{t("rfe.title")}</h3>
        <Button onClick={() => setShowForm((s) => !s)} variant="secondary" className="whitespace-nowrap py-1 text-xs">
          {showForm ? t("cases.cancel") : t("rfe.new")}
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <label className="text-xs text-zinc-500">
            {t("rfe.field.receivedDate")}
            <input
              required
              type="date"
              value={receivedDate}
              onChange={(e) => setReceivedDate(e.target.value)}
              className={`mt-1 w-full ${inputClass}`}
            />
          </label>
          <label className="text-xs text-zinc-500">
            {t("rfe.field.dueDate")}
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className={`mt-1 w-full ${inputClass}`}
            />
          </label>
          <label className="text-xs text-zinc-500 sm:col-span-3">
            {t("rfe.field.rawText")}
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={3}
              className={`mt-1 w-full ${inputClass}`}
            />
          </label>
          <Button type="submit" className="py-1.5 text-xs sm:col-span-3">
            {t("rfe.save")}
          </Button>
        </form>
      )}

      {rfes.length === 0 ? (
        <p className="text-sm text-zinc-500">{t("rfe.empty")}</p>
      ) : (
        <ul className="space-y-2">
          {rfes.map((rfe) => (
            <li key={rfe.id} className="rounded-md border border-zinc-100 dark:border-zinc-800">
              <button
                onClick={() => toggleExpand(rfe.id)}
                className="flex w-full items-center justify-between p-2 text-left text-sm"
              >
                <span className="flex flex-wrap items-center gap-2">
                  <Badge value={rfe.status} label={t(`enum.rfeStatus.${rfe.status}` as Parameters<typeof t>[0])} />
                  <span className="text-zinc-600 dark:text-zinc-400">{rfe.received_date}</span>
                  {rfe.response_due_date && (
                    <span className="text-zinc-500">
                      {t("myDay.dueBy")} {rfe.response_due_date}
                    </span>
                  )}
                </span>
                <span className="text-xs text-zinc-500">
                  {rfe.evidence_gathered_count}/{rfe.evidence_count}
                </span>
              </button>

              {expandedId === rfe.id && detail && (
                <div className="border-t border-zinc-100 p-3 dark:border-zinc-800">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <select
                      aria-label={t("rfe.field.status")}
                      value={detail.status}
                      onChange={(e) => handleStatusChange(rfe.id, e.target.value)}
                      className={inputClass}
                    >
                      {RFE_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {t(`enum.rfeStatus.${s}` as Parameters<typeof t>[0])}
                        </option>
                      ))}
                    </select>
                    <Button
                      onClick={() => handleDelete(rfe.id)}
                      variant="secondary"
                      className="py-1 text-xs text-red-600 dark:text-red-400"
                    >
                      {t("rfe.delete")}
                    </Button>
                  </div>

                  {detail.raw_text && (
                    <p className="mb-3 whitespace-pre-wrap rounded-md bg-zinc-50 p-2 text-xs text-zinc-600 dark:bg-zinc-950 dark:text-zinc-400">
                      {detail.raw_text}
                    </p>
                  )}

                  <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">
                    {t("rfe.evidence.title")}
                  </h4>
                  <ul className="mb-2 space-y-1">
                    {detail.evidence_items.map((item) => (
                      <li key={item.id} className="flex flex-wrap items-center gap-2 text-sm">
                        <select
                          aria-label={t("rfe.evidence.status")}
                          value={item.status}
                          onChange={(e) => handleToggleEvidence(rfe.id, item.id, e.target.value)}
                          className="rounded-md border border-zinc-300 bg-white px-1.5 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                        >
                          {RFE_EVIDENCE_STATUSES.map((s) => (
                            <option key={s} value={s}>
                              {t(`enum.rfeEvidenceStatus.${s}` as Parameters<typeof t>[0])}
                            </option>
                          ))}
                        </select>
                        <span
                          className={
                            item.status === "submitted"
                              ? "text-zinc-400 line-through dark:text-zinc-600"
                              : "text-zinc-700 dark:text-zinc-300"
                          }
                        >
                          {item.description}
                        </span>
                        <button
                          onClick={() => handleDeleteEvidence(rfe.id, item.id)}
                          className="text-xs text-red-600 hover:underline dark:text-red-400"
                        >
                          {t("rfe.delete")}
                        </button>
                      </li>
                    ))}
                    {detail.evidence_items.length === 0 && (
                      <li className="text-sm text-zinc-500">{t("rfe.evidence.empty")}</li>
                    )}
                  </ul>

                  <div className="mb-3 flex gap-2">
                    <input
                      value={newEvidence}
                      onChange={(e) => setNewEvidence(e.target.value)}
                      placeholder={t("rfe.evidence.addPlaceholder")}
                      aria-label={t("rfe.evidence.addPlaceholder")}
                      className={`flex-1 ${inputClass}`}
                    />
                    <Button
                      onClick={() => handleAddEvidence(rfe.id)}
                      variant="secondary"
                      className="whitespace-nowrap py-1.5 text-xs"
                    >
                      {t("rfe.evidence.add")}
                    </Button>
                  </div>

                  {aiConfigured && detail.raw_text && (
                    <div className="rounded-md border border-dashed border-indigo-200 p-2 dark:border-indigo-900">
                      <Button
                        onClick={() => handleSuggest(rfe.id)}
                        disabled={suggesting}
                        variant="secondary"
                        className="py-1 text-xs"
                      >
                        {suggesting ? t("rfe.suggest.loading") : t("rfe.suggest.action")}
                      </Button>
                      {suggestions.length > 0 && (
                        <ul className="mt-2 space-y-1.5">
                          {suggestions.map((s) => (
                            <li key={s.description} className="text-sm">
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <p className="text-zinc-700 dark:text-zinc-300">{s.description}</p>
                                  <p className="text-xs text-zinc-500">{s.reason}</p>
                                </div>
                                <button
                                  onClick={() => acceptSuggestion(rfe.id, s.description)}
                                  className="whitespace-nowrap text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                                >
                                  {t("rfe.suggest.accept")}
                                </button>
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
