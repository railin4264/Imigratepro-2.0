"use client";

import { memo } from "react";
import type { FieldSchemaEntry } from "@/lib/api";

type Option = {
  field: FieldSchemaEntry;
  label: string;
  checked: boolean;
};

type Props = {
  question: string;
  options: Option[];
  onChange: (name: string, value: string) => void;
};

// Renders a "pick from these boxes" cluster (relationship type, race, eye
// color, ...) as the shared question once, followed by short toggle pills --
// see buildDisplayItems in formFieldHelpers.ts for how these get grouped.
// Each pill is a real checkbox (visually hidden, not display:none, so it
// stays in the tab order) wrapped in its own label for a large touch target.
function CheckboxGroupFieldInner({ question, options, onChange }: Props) {
  return (
    <div className="py-1">
      <p className="mb-2 text-xs leading-snug text-zinc-600 dark:text-zinc-400">{question}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <label
            key={opt.field.name}
            className={`inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition focus-within:ring-2 focus-within:ring-indigo-400 ${
              opt.checked
                ? "border-indigo-600 bg-indigo-600 text-white"
                : "border-zinc-300 bg-white text-zinc-700 hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:border-zinc-600"
            }`}
          >
            <input
              type="checkbox"
              checked={opt.checked}
              onChange={(e) => onChange(opt.field.name, e.target.checked ? (opt.field.on_value ?? "X") : "")}
              className="sr-only"
            />
            {opt.checked && (
              <span aria-hidden="true">
                ✓
              </span>
            )}
            {opt.label}
          </label>
        ))}
      </div>
    </div>
  );
}

// Memoized for the same reason as FieldRow -- checking one option in a form
// with hundreds of fields shouldn't re-render every other group.
export const CheckboxGroupField = memo(CheckboxGroupFieldInner);
