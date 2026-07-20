"use client";

import { useEffect, useRef, useState } from "react";
import type { SVGProps } from "react";
import Link from "next/link";
import { type Notification, getNotifications, markAllNotificationsRead } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

const POLL_MS = 30000;

function BellIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M6 8a6 6 0 0 1 12 0c0 4 1.5 5.5 2 6H4c.5-.5 2-2 2-6Z" />
      <path d="M9.5 18a2.5 2.5 0 0 0 5 0" />
    </svg>
  );
}

export function NotificationBell() {
  const { t, lang } = useTranslation();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function load() {
      getNotifications()
        .then(setNotifications)
        .catch(() => {});
    }
    load();
    const interval = setInterval(load, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  async function handleMarkAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await markAllNotificationsRead();
    } catch {
      // next poll will reconcile if this failed
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={t("notifications.title")}
        className="relative flex h-11 w-11 items-center justify-center rounded-lg text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
      >
        <BellIcon className="h-5 w-5" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 max-w-[90vw] rounded-xl border border-zinc-200 bg-white p-2 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          <div className="mb-1 flex items-center justify-between px-2 py-1">
            <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{t("notifications.title")}</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              >
                {t("notifications.markAllRead")}
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-2 py-4 text-center text-sm text-zinc-500">{t("notifications.empty")}</p>
            ) : (
              <ul className="space-y-0.5">
                {notifications.map((n) => (
                  <li key={n.id}>
                    <Link
                      href="/cases"
                      onClick={() => setOpen(false)}
                      className={`block rounded-lg px-2 py-2 text-sm transition hover:bg-zinc-50 dark:hover:bg-zinc-800 ${
                        !n.read ? "bg-indigo-50/60 dark:bg-indigo-950/20" : ""
                      }`}
                    >
                      <p className="text-zinc-700 dark:text-zinc-300">{n.message}</p>
                      <p className="mt-0.5 text-xs text-zinc-400">
                        {new Date(n.created_at).toLocaleString(lang)}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
