"use client";

import type { FieldSchemaEntry } from "@/lib/api";
import { fromHtmlDate, isDateField, toHtmlDate } from "@/lib/formFieldHelpers";

export function FieldInput({
  field,
  value,
  onChange,
  id,
  required,
}: {
  field: FieldSchemaEntry;
  value: string;
  onChange: (value: string) => void;
  id?: string;
  required?: boolean;
}) {
  if (field.type === "checkbox") {
    return (
      <input
        type="checkbox"
        id={id}
        checked={value === field.on_value}
        onChange={(e) => onChange(e.target.checked ? field.on_value ?? "X" : "")}
        className="mt-1 h-5 w-5 shrink-0"
      />
    );
  }

  if (field.type === "choice") {
    return (
      <select
        id={id}
        value={value}
        required={required}
        aria-required={required}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-zinc-300 bg-white p-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
      >
        {[...new Set(field.options ?? [])].map((opt) => (
          <option key={opt} value={opt}>
            {opt.trim() === "" ? "—" : opt}
          </option>
        ))}
      </select>
    );
  }

  if (isDateField(field)) {
    return (
      <input
        type="date"
        id={id}
        value={toHtmlDate(value)}
        required={required}
        aria-required={required}
        onChange={(e) => onChange(fromHtmlDate(e.target.value))}
        className="w-full rounded-md border border-zinc-300 bg-white p-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
      />
    );
  }

  return (
    <input
      type="text"
      id={id}
      value={value}
      required={required}
      aria-required={required}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-md border border-zinc-300 bg-white p-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
    />
  );
}
