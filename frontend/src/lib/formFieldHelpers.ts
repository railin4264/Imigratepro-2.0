import type { FieldSchemaEntry } from "@/lib/api";

// Matches up to the first period that isn't tucked inside a "(...)" aside --
// without the parenthetical alternative, a title like "Relationship (You are
// the Petitioner. Your relative is the Beneficiary)." truncates at the
// period *inside* the parens, cutting the heading off mid-sentence.
export function getPartLabel(label: string): string {
  const match = label.match(/^Part\s+\d+\.\s*(?:\([^)]*\)|[^.(])+\./);
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

const PART_NUMBER = /^Part\s+(\d+)\./;

/** Groups fields by their "Part N. Title" heading, numerically sorted -- NOT in field-array
 * order. USCIS's own PDFs frequently list AcroForm fields in an internal order that doesn't
 * match the form's visual Part 1/2/3 layout (e.g. on I-130, "Part 2" fields appear before "Part
 * 1" fields in the raw extraction), so array order can't be trusted for anything that presents
 * parts as a sequence (the step wizard, the editor accordion). Also collapses same-numbered
 * parts that got extracted with slightly different trailing title text (the tooltip text isn't
 * always identical across every field within one part) under a single canonical title -- the
 * first one seen -- rather than showing e.g. "Part 8" as two separate back-to-back groups. */
export function groupByPart(fields: FieldSchemaEntry[]): [string, FieldSchemaEntry[]][] {
  const byNumber = new Map<number, { title: string; fields: FieldSchemaEntry[] }>();
  const other: FieldSchemaEntry[] = [];

  for (const field of fields) {
    const numberMatch = field.label.match(PART_NUMBER);
    if (!numberMatch) {
      other.push(field);
      continue;
    }
    const number = Number(numberMatch[1]);
    if (!byNumber.has(number)) {
      byNumber.set(number, { title: getPartLabel(field.label), fields: [] });
    }
    byNumber.get(number)!.fields.push(field);
  }

  const result: [string, FieldSchemaEntry[]][] = [...byNumber.entries()]
    .sort(([a], [b]) => a - b)
    .map(([, group]) => [group.title, group.fields]);
  if (other.length > 0) result.push(["Other fields", other]);
  return result;
}

/** Strips the "Part N. Title." prefix that getPartLabel/groupByPart already show once as a
 * section heading -- repeating it on every single field inside that section (as the raw
 * extracted USCIS tooltip does) makes each row start with an identical multi-line sentence,
 * which is exactly the "the checkbox labels are hard to read" problem this file exists to fix.
 * Falls back to the original label when there's no Part prefix to strip (e.g. "Other fields"). */
export function stripPartPrefix(label: string): string {
  const partTitle = getPartLabel(label);
  if (partTitle === "Other fields" || !label.startsWith(partTitle)) return label;
  return label.slice(partTitle.length).trim();
}

// USCIS labels for a "pick one of these boxes" cluster all end the same way:
// a shared question ("...I am filing this petition for my (Select only one
// box).") followed by a per-checkbox "Select <option>." clause. The greedy
// `(.*)` finds the *last* "Select " in the label, so it isn't thrown off by
// periods inside the option text itself (e.g. "Select U.S. Citizen.").
const TRAILING_SELECT_CLAUSE = /^(.*)\bSelect\s+(.+?)\.?\s*$/i;
const MULTI_SELECT_HINT = /all applicable|select all|check all/i;
const ONLY_ONE_HINT = /only one/i;
// Binary pairs that are exclusive by definition even when the label doesn't
// spell out "(select only one box)" -- unlike "Select all applicable boxes"
// (race, languages, etc.), nothing in a real USCIS form lets you be both.
const KNOWN_EXCLUSIVE_PAIRS: ReadonlySet<string>[] = [new Set(["male", "female"]), new Set(["yes", "no"])];

/** The last dotted path segment, e.g. "form1[0].#subform[0].Pt1Line1_Spouse[0]" -> "Pt1Line1_Spouse[0]". */
function leafFieldName(name: string): string {
  const parts = name.split(".");
  return parts[parts.length - 1];
}

/** Strips the trailing PDF array index, e.g. "Pt1Line1_Spouse[0]" -> "Pt1Line1_Spouse". Two
 * checkboxes sharing this exact base name are the *same* underlying AcroForm field exposed with
 * different export values (a true PDF radio group) -- structurally guaranteed exclusive,
 * independent of label text. */
function baseFieldName(name: string): string {
  return leafFieldName(name).replace(/\[\d+\]$/, "");
}

/** One level coarser than baseFieldName -- drops the last underscore segment too, e.g.
 * "Pt1Line1_Spouse" -> "Pt1Line1". Used only as an extra guard on the label-based fallback
 * below, so a repeated-child/repeated-entry block (four kids each asked the same yes/no
 * question, but as four *differently named* fields) can't collide just because their tooltip
 * text happens to be identical -- see the regression test for the real case that caught this. */
function fieldNamePrefix(name: string): string {
  return baseFieldName(name).replace(/_[^_]*$/, "");
}

/** Maps each checkbox field name to the sibling field names it should uncheck when it gets
 * checked -- e.g. "Select Male."/"Select Female." on the same line, or an explicit "(Select
 * only one box)" cluster. Deliberately conservative in two ways: it only groups fields when the
 * shared question text says so (or the option set is an unambiguous binary pair) -- never
 * "select all applicable" style groups (race, languages spoken, etc.), which are genuinely
 * multi-select -- and it prefers grouping by the real PDF field name over label text, since
 * USCIS's own extracted tooltips aren't always unique per repeated field (see fieldNamePrefix). */
export function buildExclusiveCheckboxGroups(fields: FieldSchemaEntry[]): Map<string, string[]> {
  const checkboxes = fields.filter((f) => f.type === "checkbox");
  const groups = new Map<string, string[]>();
  const claimed = new Set<string>();

  function claim(members: string[]) {
    for (const name of members) {
      groups.set(
        name,
        members.filter((n) => n !== name)
      );
      claimed.add(name);
    }
  }

  // Tier 1: same underlying PDF field name (radio-style export values) -- always exclusive.
  const byBaseName = new Map<string, string[]>();
  for (const field of checkboxes) {
    const base = baseFieldName(field.name);
    if (!byBaseName.has(base)) byBaseName.set(base, []);
    byBaseName.get(base)!.push(field.name);
  }
  for (const members of byBaseName.values()) {
    if (members.length >= 2) claim(members);
  }

  // Tier 2: distinct field names, but the shared question text says "pick one" -- only among
  // fields tier 1 didn't already resolve, and only within the same name-prefix family.
  const byStem = new Map<string, { name: string; option: string }[]>();
  for (const field of checkboxes) {
    if (claimed.has(field.name)) continue;
    const match = field.label.match(TRAILING_SELECT_CLAUSE);
    if (!match) continue;
    const key = `${fieldNamePrefix(field.name)}||${match[1].trim()}`;
    if (!byStem.has(key)) byStem.set(key, []);
    byStem.get(key)!.push({ name: field.name, option: match[2].trim().toLowerCase() });
  }
  for (const [key, members] of byStem) {
    const stem = key.slice(key.indexOf("||") + 2);
    if (members.length < 2 || MULTI_SELECT_HINT.test(stem)) continue;

    const optionSet = new Set(members.map((m) => m.option));
    const isKnownPair = KNOWN_EXCLUSIVE_PAIRS.some(
      (pair) => pair.size === optionSet.size && [...pair].every((o) => optionSet.has(o))
    );
    if (!ONLY_ONE_HINT.test(stem) && !isKnownPair) continue;

    claim(members.map((m) => m.name));
  }

  return groups;
}

export type FieldDisplayItem =
  | { kind: "field"; field: FieldSchemaEntry }
  | { kind: "checkbox-group"; question: string; options: { field: FieldSchemaEntry; optionClause: string }[] };

/** Strips a leading "Select "/"Seleccione " and trailing period so a translated "Seleccione
 * Cónyuge." clause can be shown as just "Cónyuge" on a compact pill -- run *after*
 * translateLabel, not before, since the phrase dictionary is keyed on the full "Select X."
 * clause (translateLabel(question) already relies on that for the group heading itself). */
export function stripSelectPrefix(text: string): string {
  return text.replace(/^(Select|Seleccione)\s+/i, "").replace(/\.$/, "");
}

/** Lays fields out for display: consecutive checkboxes that share a "pick from these boxes"
 * question -- exclusive ones like relationship type, and "select all applicable" ones like race
 * alike -- collapse into one group with the question shown once and each checkbox showing just
 * its short option text ("Spouse", "Child", ...), instead of the entire question repeated
 * verbatim on every single row. A group is only formed for 2+ related checkboxes; a standalone
 * checkbox with no sibling (an attestation like "I understood everything as interpreted") still
 * renders with its full label like any other field, exactly as before. Order-preserving: each
 * group appears where its first member field would have. `optionClause` is left as the full
 * "Select X." sentence (not shortened) so callers can run it through translateLabel -- the
 * phrase dictionary is keyed on that full form -- before shortening with stripSelectPrefix. */
export function buildDisplayItems(fields: FieldSchemaEntry[]): FieldDisplayItem[] {
  type Cluster = { stem: string; members: { name: string; optionClause: string }[] };
  const clusters = new Map<string, Cluster>();
  const clusterKeyOf = new Map<string, string>();

  for (const field of fields) {
    if (field.type !== "checkbox") continue;
    const match = field.label.match(TRAILING_SELECT_CLAUSE);
    if (!match) continue;
    const key = `${fieldNamePrefix(field.name)}||${match[1].trim()}`;
    if (!clusters.has(key)) clusters.set(key, { stem: match[1].trim(), members: [] });
    const option = match[2].trim();
    clusters.get(key)!.members.push({ name: field.name, optionClause: `Select ${option}${option.endsWith(".") ? "" : "."}` });
    clusterKeyOf.set(field.name, key);
  }
  for (const [key, cluster] of clusters) {
    if (cluster.members.length < 2) clusters.delete(key);
  }

  const fieldsByName = new Map(fields.map((f) => [f.name, f]));
  const emitted = new Set<string>();
  const items: FieldDisplayItem[] = [];

  for (const field of fields) {
    const key = clusterKeyOf.get(field.name);
    if (key && clusters.has(key)) {
      if (emitted.has(key)) continue;
      emitted.add(key);
      const cluster = clusters.get(key)!;
      const question = cluster.stem.endsWith(".") ? cluster.stem : `${cluster.stem}.`;
      items.push({
        kind: "checkbox-group",
        question: stripPartPrefix(question),
        options: cluster.members.map((m) => ({ field: fieldsByName.get(m.name)!, optionClause: m.optionClause })),
      });
      continue;
    }
    items.push({ kind: "field", field });
  }

  return items;
}
