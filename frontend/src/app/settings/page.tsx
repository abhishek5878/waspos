"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAuthStore } from "@/store/auth";

export default function SettingsPage() {
  const { user, isDemo } = useAuthStore();

  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configure your firm and preferences.
        </p>
        <div className="mt-6 p-4 rounded-lg bg-secondary/50">
          <h3 className="font-medium">Account</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {user?.full_name} ({user?.email})
          </p>
          {isDemo && (
            <p className="text-xs text-wasp-gold mt-2">Demo account</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
