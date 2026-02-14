"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAuthStore } from "@/store/auth";

export default function PollsPage() {
  const isDemo = useAuthStore((s) => s.isDemo);

  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">IC Polls</h1>
        <p className="text-muted-foreground mt-2">
          Blind conviction polling and divergence analysis.
        </p>
        {isDemo && (
          <p className="text-sm text-wasp-gold mt-4">
            Deploy your backend to create and participate in polls.
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
