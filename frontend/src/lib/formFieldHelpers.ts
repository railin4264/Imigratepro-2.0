import type { FieldSchemaEntry } from "@/lib/api";

export function getPartLabel(label: string): string {
  const match = label.match(/^Part\s+\d+\.\s*[^.]+\./);
  return match ? match[0].trim() : "Other fields";
}

export function isDateField(field: FieldSchemaEntry): boolean {
  return field.type === "text" && /date/i.test(field.label);
}

export function isFieldVisible(field: FieldSchemaEntry, data: Record<string, string>): boolean {
  if (!field.show_if || field.show_if.length === 0) return true;
  return field.show_if.some((cond) => data[cond.field] === cond.equals);
}

export function toHtmlDate(value: string): string {
  const m = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}-${m[1]}-${m[2]}` : "";
}

export function fromHtmlDate(value: string): string {
  const m = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[2]}/${m[3]}/${m[1]}` : value;
}

export function groupByPart(fields: FieldSchemaEntry[]): [string, FieldSchemaEntry[]][] {
  const grouped = new Map<string, FieldSchemaEntry[]>();
  for (const f of fields) {
    const part = getPartLabel(f.label);
    if (!grouped.has(part)) grouped.set(part, []);
    grouped.get(part)!.push(f);
  }
  return [...grouped.entries()];
}
