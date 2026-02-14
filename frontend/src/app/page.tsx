"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { DealPipeline } from "@/components/pipeline/DealPipeline";

export default function Home() {
  return (
    <DashboardLayout>
      <DealPipeline />
    </DashboardLayout>
  );
}
