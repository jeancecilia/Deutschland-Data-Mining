"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/discovery", label: "Discovery" },
  { href: "/keywords", label: "Keywords" },
  { href: "/clusters", label: "Clusters" },
  { href: "/reports", label: "Reports" },
  { href: "/runtime", label: "Runtime" }
];

export function DashboardNav() {
  const pathname = usePathname();
  const currentPath = pathname ?? "/";

  return (
    <nav className="dashboard-nav" aria-label="Primary">
      {navItems.map((item) => {
        const isActive =
          item.href === "/"
            ? currentPath === "/"
            : currentPath === item.href || currentPath.startsWith(`${item.href}/`);

        return (
          <Link key={item.href} href={item.href} data-active={isActive ? "true" : "false"}>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
