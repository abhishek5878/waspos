"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function DealsPage() {
  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Deals</h1>
        <p className="text-muted-foreground mt-2">
          Deals list view. Use the Pipeline for the kanban board.
        </p>
      </div>
    </DashboardLayout>
  );
}
