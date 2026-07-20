export default function RootLoading() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-8" aria-busy="true" aria-label="Cargando">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-black dark:border-zinc-700 dark:border-t-zinc-50" />
    </div>
  );
}
