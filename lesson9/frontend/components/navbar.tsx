"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bitcoin } from "lucide-react";
import { cn } from "@/lib/utils";
import { SchedulerHealthIndicator } from "@/components/scheduler-health-indicator";

interface NavItem {
  href: string;
  label: string;
  matchPrefix?: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "仪表盘" },
  { href: "/predict", label: "手动预测" },
  { href: "/history", label: "推送历史" },
  { href: "/settings", label: "设置" },
];

function isActive(pathname: string, item: NavItem): boolean {
  if (item.href === pathname) return true;
  if (item.matchPrefix && pathname.startsWith(item.matchPrefix)) return true;
  return false;
}

export function Navbar() {
  const pathname = usePathname() ?? "/";
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/60 bg-slate-950/70 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 text-base font-bold tracking-tight text-slate-50"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 shadow-lg shadow-orange-500/30">
            <Bitcoin className="h-5 w-5 text-white" aria-hidden />
          </span>
          <span>
            BTC <span className="text-orange-400">Arb</span>
            <span className="ml-2 text-xs font-normal text-slate-500">Terminal</span>
          </span>
        </Link>
        <ul className="flex flex-1 items-center gap-1 text-sm">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "relative rounded-lg px-3.5 py-2 font-medium transition-all duration-150",
                    active
                      ? "bg-orange-500/15 text-orange-300"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  {item.label}
                  {active && (
                    <span className="absolute -bottom-[17px] left-1/2 h-[2px] w-6 -translate-x-1/2 rounded-full bg-orange-400" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
        <SchedulerHealthIndicator />
      </nav>
    </header>
  );
}
