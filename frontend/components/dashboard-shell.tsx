import type { ReactNode } from "react";

import { DashboardNav } from "./dashboard-nav";

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="dashboard-brand">
          <p>KDP Deutschland</p>
          <h1>Opportunity Engine</h1>
          <span>
            Discovery, keyword expansion, cluster scoring, and reporting are now separated into
            focused pages.
          </span>
        </div>
        <DashboardNav />
      </aside>

      <main className="dashboard-main">{children}</main>
    </div>
  );
}
