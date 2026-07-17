const COLOR_MAP: Record<string, string> = {
  // case status
  intake: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  preparing: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  filed: "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",
  rfe: "bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300",
  approved: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  denied: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
  closed: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
  // generated form status
  draft: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  generated: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  // document status
  uploaded: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  processing: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  extracted: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  failed: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
};

const DEFAULT_COLOR = "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300";

export function Badge({ value, label }: { value: string; label?: string }) {
  const color = COLOR_MAP[value] ?? DEFAULT_COLOR;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {label ?? value}
    </span>
  );
}
