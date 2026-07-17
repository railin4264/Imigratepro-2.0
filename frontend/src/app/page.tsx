"use client";

import Link from "next/link";
import { useTranslation } from "@/lib/i18n";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";

export default function Home() {
  const { t } = useTranslation();

  const modules = [
    { href: "/clients", label: t("home.clients"), description: t("home.clients.desc"), icon: "◒" },
    { href: "/cases", label: t("home.cases"), description: t("home.cases.desc"), icon: "▤" },
    { href: "/services", label: t("home.services"), description: t("home.services.desc"), icon: "◈" },
    { href: "/forms", label: t("home.forms"), description: t("home.forms.desc"), icon: "▥" },
    { href: "/documents", label: t("home.documents"), description: t("home.documents.desc"), icon: "▦" },
  ];

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-1 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {t("home.title")}
        </h1>
        <p className="mb-8 text-zinc-500 dark:text-zinc-400">{t("home.subtitle")}</p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((mod) => (
            <Link key={mod.href} href={mod.href}>
              <Card className="h-full p-5 transition hover:border-indigo-300 hover:shadow-md dark:hover:border-indigo-800">
                <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-lg text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
                  {mod.icon}
                </span>
                <h2 className="font-medium text-zinc-900 dark:text-zinc-50">{mod.label}</h2>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{mod.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
