"use client";

import { memo, useId } from "react";
import type { FieldSchemaEntry } from "@/lib/api";
import { FieldInput } from "@/components/FieldInput";

type Props = {
  field: FieldSchemaEntry;
  value: string;
  label: string;
  onChange: (name: string, value: string) => void;
  required?: boolean;
};

function FieldRowInner({ field, value, label, onChange, required = false }: Props) {
  const id = useId();

  if (field.type === "checkbox") {
    // The whole label is the touch target (min-h-11 = 44px) and implicitly
    // associates with the checkbox inside -- no htmlFor needed.
    return (
      <label className="flex min-h-11 cursor-pointer items-start gap-3 py-1">
        <span className="flex-1 text-sm leading-snug text-zinc-600 dark:text-zinc-400">{label}</span>
        <FieldInput field={field} value={value} onChange={(v) => onChange(field.name, v)} id={id} />
      </label>
    );
  }

  return (
    <div className="grid grid-cols-1 items-start gap-1.5 sm:grid-cols-[1fr_auto] sm:gap-3">
      <label htmlFor={id} className="text-sm leading-snug text-zinc-600 dark:text-zinc-400">
        {label}
        {required && (
          <span aria-hidden="true" className="ml-0.5 text-red-500">*</span>
        )}
      </label>
      <div className="w-full sm:w-48">
        <FieldInput
          field={field}
          value={value}
          onChange={(v) => onChange(field.name, v)}
          id={id}
          required={required}
        />
      </div>
    </div>
  );
}

// Memoized so typing in one field doesn't re-render the other ~400+ field
// rows on every keystroke -- without this, editing a single field caused a
// full re-render of the whole form and felt like it froze.
export const FieldRow = memo(FieldRowInner);
