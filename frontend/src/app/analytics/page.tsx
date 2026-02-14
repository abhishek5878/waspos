"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function AnalyticsPage() {
  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="text-muted-foreground mt-2">
          Deal flow analytics and portfolio insights.
        </p>
      </div>
    </DashboardLayout>
  );
}
