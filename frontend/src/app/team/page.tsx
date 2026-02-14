"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function TeamPage() {
  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Team</h1>
        <p className="text-muted-foreground mt-2">
          Manage partners and investment team.
        </p>
      </div>
    </DashboardLayout>
  );
}
