"use client";

import { memo } from "react";
import type { FieldSchemaEntry } from "@/lib/api";
import { FieldInput } from "@/components/FieldInput";

type Props = {
  field: FieldSchemaEntry;
  value: string;
  label: string;
  onChange: (name: string, value: string) => void;
};

function FieldRowInner({ field, value, label, onChange }: Props) {
  if (field.type === "checkbox") {
    // The whole row is the label so the clickable/tappable area meets the
    // 44px touch target minimum, not just the ~16px checkbox square itself.
    return (
      <label className="flex min-h-11 cursor-pointer items-start gap-3 py-1">
        <span className="flex-1 text-xs leading-snug text-zinc-600 dark:text-zinc-400">{label}</span>
        <FieldInput field={field} value={value} onChange={(v) => onChange(field.name, v)} />
      </label>
    );
  }

  return (
    <div className="grid grid-cols-1 items-start gap-1.5 sm:grid-cols-[1fr_auto] sm:gap-3">
      <label className="text-xs leading-snug text-zinc-600 dark:text-zinc-400">{label}</label>
      <div className="w-full sm:w-48">
        <FieldInput field={field} value={value} onChange={(v) => onChange(field.name, v)} />
      </div>
    </div>
  );
}

// Memoized so typing in one field doesn't re-render the other ~400+ field
// rows on every keystroke -- without this, editing a single field caused a
// full re-render of the whole form and felt like it froze.
export const FieldRow = memo(FieldRowInner);
