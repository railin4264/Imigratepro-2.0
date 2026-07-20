"use client";

import { useEffect, useState } from "react";
import { type FormTemplate, type Service, createService, getFormTemplates, getServices } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { formatMoney } from "@/lib/format";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white p-2 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:focus:ring-indigo-950";
const labelClass = "mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500";

export default function ServicesPage() {
  const { t } = useTranslation();
  const [services, setServices] = useState<Service[]>([]);
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [estimatedDays, setEstimatedDays] = useState("");
  const [selectedForms, setSelectedForms] = useState<string[]>([]);
  const [checklistText, setChecklistText] = useState("");
  const [stagesText, setStagesText] = useState("");

  function load() {
    Promise.all([getServices(), getFormTemplates()])
      .then(([serviceList, templateList]) => {
        setServices(serviceList);
        setTemplates(templateList);
      })
      .catch(() => setError(t("services.error.connect")));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps -- load only once on mount
  useEffect(load, []);

  function toggleFormCode(code: string) {
    setSelectedForms((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createService({
        name,
        description: description || undefined,
        price: price ? Number(price) : undefined,
        estimated_days: estimatedDays ? Number(estimatedDays) : undefined,
        form_template_codes: selectedForms,
        checklist_items: checklistText.split("\n").map((s) => s.trim()).filter(Boolean),
        stages: stagesText.split("\n").map((s) => s.trim()).filter(Boolean),
      });
      setName("");
      setDescription("");
      setPrice("");
      setEstimatedDays("");
      setSelectedForms([]);
      setChecklistText("");
      setStagesText("");
      setShowForm(false);
      load();
    } catch {
      setError(t("services.error.create"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {t("services.title")}
          </h1>
          <Button onClick={() => setShowForm((s) => !s)} variant={showForm ? "secondary" : "primary"}>
            {showForm ? t("services.cancel") : t("services.new")}
          </Button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {showForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleSubmit} className="space-y-3">
              <label className={labelClass}>
                {t("services.field.name")}
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClass}
                />
              </label>
              <label className={labelClass}>
                {t("services.field.description")}
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={inputClass}
                  rows={2}
                />
              </label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label className={labelClass}>
                  {t("services.field.price")}
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className={inputClass}
                  />
                </label>
                <label className={labelClass}>
                  {t("services.field.estimatedDays")}
                  <input
                    type="number"
                    value={estimatedDays}
                    onChange={(e) => setEstimatedDays(e.target.value)}
                    className={inputClass}
                  />
                </label>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {t("services.field.forms")}
                </label>
                <div className="flex flex-wrap gap-2">
                  {templates.map((tpl) => (
                    <label
                      key={tpl.code}
                      className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition ${
                        selectedForms.includes(tpl.code)
                          ? "border-indigo-300 bg-indigo-50 text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-300"
                          : "border-zinc-300 text-zinc-600 dark:border-zinc-700 dark:text-zinc-400"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedForms.includes(tpl.code)}
                        onChange={() => toggleFormCode(tpl.code)}
                        className="mr-1.5 hidden"
                      />
                      {tpl.code}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {t("services.field.checklist")}
                </label>
                <textarea
                  value={checklistText}
                  onChange={(e) => setChecklistText(e.target.value)}
                  className={inputClass}
                  rows={5}
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {t("services.field.stages")}
                </label>
                <textarea
                  value={stagesText}
                  onChange={(e) => setStagesText(e.target.value)}
                  className={inputClass}
                  rows={5}
                />
              </div>

              <Button type="submit" disabled={saving}>
                {saving ? t("services.saving") : t("services.save")}
              </Button>
            </form>
          </Card>
        )}

        {services.length === 0 && !error && (
          <p className="text-zinc-500 dark:text-zinc-400">{t("services.empty")}</p>
        )}

        <div className="space-y-3">
          {services.map((s) => (
            <Card key={s.id} className="p-5">
              <div className="mb-1 flex items-center justify-between">
                <h2 className="font-medium text-zinc-900 dark:text-zinc-50">{s.name}</h2>
                {s.price != null && (
                  <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
                    {formatMoney(s.price)}
                  </span>
                )}
              </div>
              {s.description && <p className="mb-2 text-sm text-zinc-500">{s.description}</p>}
              <div className="flex flex-wrap gap-1.5">
                {s.form_codes.map((code) => (
                  <span
                    key={code}
                    className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {code}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                {s.checklist_items.length} {t("services.checklistCount")} · {s.stages.length}{" "}
                {t("services.stagesCount")}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
