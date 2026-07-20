"use client";

import { useEffect, useState } from "react";
import type { SVGProps } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslation } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NotificationBell } from "@/components/NotificationBell";

function DashboardIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="3" width="7.5" height="9" rx="1.5" />
      <rect x="13.5" y="3" width="7" height="5.5" rx="1.5" />
      <rect x="13.5" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="15.5" width="7.5" height="5.5" rx="1.5" />
    </svg>
  );
}

function ClientsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M4.5 20c1-4 4-6 7.5-6s6.5 2 7.5 6" />
    </svg>
  );
}

function TeamIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="9" cy="8" r="3" />
      <path d="M2.5 19c0.7-3.2 3.2-5 6.5-5s5.8 1.8 6.5 5" />
      <circle cx="17" cy="8.5" r="2.25" />
      <path d="M16 13.5c2.6 0.2 4.6 1.8 5.2 4.5" />
    </svg>
  );
}

function CasesIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="8" width="18" height="12" rx="2" />
      <path d="M8 8V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M3 13h18" />
    </svg>
  );
}

function ServicesIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 3 3 8l9 5 9-5-9-5Z" />
      <path d="M3 13l9 5 9-5" />
      <path d="M3 18l9 5 9-5" />
    </svg>
  );
}

function FormsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v4h4" />
      <path d="M8.5 12.5h7M8.5 16h5" />
    </svg>
  );
}

function DocumentsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M3 8a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8Z" />
    </svg>
  );
}

function AppointmentsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
      <path d="M8 14h.01M12 14h.01M16 14h.01M8 17.5h.01M12 17.5h.01" />
    </svg>
  );
}

function BillingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M7 9h10M7 13h6" />
      <path d="M15.5 16.5a2 2 0 1 0 0-4h-1.5a1.5 1.5 0 0 1 0-3H16" />
      <path d="M14.5 8.5v1M14.5 16.5v1" />
    </svg>
  );
}

function ReportsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 20V10M12 20V4M20 20v-7" />
      <path d="M3 20h18" />
    </svg>
  );
}

function MenuIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function CloseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}

function LogoutIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
      <path d="M15 16l4-4-4-4M19 12H8" />
    </svg>
  );
}

const NAV = [
  { href: "/", key: "nav.dashboard", Icon: DashboardIcon },
  { href: "/clients", key: "nav.clients", Icon: ClientsIcon },
  { href: "/cases", key: "nav.cases", Icon: CasesIcon },
  { href: "/team", key: "nav.team", Icon: TeamIcon },
  { href: "/services", key: "nav.services", Icon: ServicesIcon },
  { href: "/forms", key: "nav.forms", Icon: FormsIcon },
  { href: "/documents", key: "nav.documents", Icon: DocumentsIcon },
  { href: "/appointments", key: "nav.appointments", Icon: AppointmentsIcon },
  { href: "/billing", key: "nav.billing", Icon: BillingIcon },
  { href: "/stats", key: "nav.stats", Icon: ReportsIcon },
] as const;

function Brand() {
  return (
    <div className="flex items-center gap-2 border-b border-zinc-200 px-5 py-5 dark:border-zinc-800">
      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600 text-sm font-bold text-white">
        M
      </span>
      <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">MigratePro</span>
    </div>
  );
}

function NavLinks({
  pathname,
  t,
  onNavigate,
}: {
  pathname: string;
  t: (key: (typeof NAV)[number]["key"]) => string;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex-1 space-y-0.5 p-3">
      {NAV.map(({ href, key, Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
              active
                ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
            }`}
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
            {t(key)}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { user, status, logout } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login");
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("auth.loading")}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-black">
      {/* Desktop sidebar */}
      <aside className="hidden w-56 shrink-0 flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 md:flex">
        <Brand />
        <NavLinks pathname={pathname} t={t} />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label={t("nav.closeMenu")}
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative flex h-full w-64 max-w-[80vw] flex-col bg-white shadow-xl dark:bg-zinc-950">
            <div className="flex items-center justify-between">
              <Brand />
              <button
                aria-label={t("nav.closeMenu")}
                onClick={() => setMobileOpen(false)}
                className="mr-3 flex h-11 w-11 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
              >
                <CloseIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <NavLinks pathname={pathname} t={t} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950 sm:px-6">
          <button
            aria-label={t("nav.openMenu")}
            onClick={() => setMobileOpen(true)}
            className="flex h-11 w-11 items-center justify-center rounded-lg text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900 md:hidden"
          >
            <MenuIcon className="h-5 w-5" aria-hidden="true" />
          </button>
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 md:hidden">MigratePro</span>
          <div className="ml-auto flex items-center gap-1">
            <NotificationBell />
            <LanguageSwitcher fixed={false} />
            <span className="ml-1 hidden text-sm text-zinc-500 dark:text-zinc-400 sm:inline">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              aria-label={t("nav.logout")}
              title={t("nav.logout")}
              className="flex h-11 w-11 items-center justify-center rounded-lg text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
            >
              <LogoutIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}
