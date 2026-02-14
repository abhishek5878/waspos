"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAuthStore } from "@/store/auth";

export default function GhostwriterPage() {
  const isDemo = useAuthStore((s) => s.isDemo);

  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Ghostwriter</h1>
        <p className="text-muted-foreground mt-2">
          AI-powered investment memo generation with contradiction flagging.
        </p>
        {isDemo && (
          <p className="text-sm text-wasp-gold mt-4">
            Deploy your backend with Anthropic API key to use Ghostwriter.
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
