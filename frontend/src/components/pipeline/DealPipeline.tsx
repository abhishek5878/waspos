"use client";

import { useState } from "react";
import { DealStage, Deal } from "@/types";
import { DealCard } from "./DealCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Filter, SortAsc } from "lucide-react";

const PIPELINE_STAGES: { key: DealStage; label: string; color: string }[] = [
  { key: "inbound", label: "Inbound", color: "bg-slate-500" },
  { key: "screening", label: "Screening", color: "bg-blue-500" },
  { key: "first_meeting", label: "First Meeting", color: "bg-indigo-500" },
  { key: "deep_dive", label: "Deep Dive", color: "bg-purple-500" },
  { key: "ic_review", label: "IC Review", color: "bg-amber-500" },
  { key: "term_sheet", label: "Term Sheet", color: "bg-emerald-500" },
];

// Mock data for demonstration
const MOCK_DEALS: Deal[] = [
  {
    id: "1",
    firm_id: "firm-1",
    company_name: "TechStartup AI",
    one_liner: "AI-powered customer service automation",
    stage: "ic_review",
    source: "referral",
    sector: "AI/ML",
    asking_valuation: 25000000,
    round_size: 5000000,
    created_at: "2024-01-15",
    updated_at: "2024-02-01",
  },
  {
    id: "2",
    firm_id: "firm-1",
    company_name: "FinanceFlow",
    one_liner: "B2B payments infrastructure for emerging markets",
    stage: "deep_dive",
    source: "outbound",
    sector: "Fintech",
    asking_valuation: 40000000,
    round_size: 8000000,
    created_at: "2024-01-20",
    updated_at: "2024-02-05",
  },
  {
    id: "3",
    firm_id: "firm-1",
    company_name: "GreenEnergy Co",
    one_liner: "Solar panel optimization using ML",
    stage: "first_meeting",
    source: "inbound",
    sector: "CleanTech",
    asking_valuation: 15000000,
    round_size: 3000000,
    created_at: "2024-02-01",
    updated_at: "2024-02-10",
  },
  {
    id: "4",
    firm_id: "firm-1",
    company_name: "HealthBridge",
    one_liner: "Telemedicine platform for rural areas",
    stage: "screening",
    source: "portfolio_intro",
    sector: "HealthTech",
    asking_valuation: 20000000,
    round_size: 4000000,
    created_at: "2024-02-05",
    updated_at: "2024-02-12",
  },
  {
    id: "5",
    firm_id: "firm-1",
    company_name: "DataMesh",
    one_liner: "Decentralized data marketplace",
    stage: "inbound",
    source: "inbound",
    sector: "Data/Infrastructure",
    created_at: "2024-02-10",
    updated_at: "2024-02-14",
  },
  {
    id: "6",
    firm_id: "firm-1",
    company_name: "CyberShield",
    one_liner: "Zero-trust security for SMBs",
    stage: "term_sheet",
    source: "referral",
    sector: "Cybersecurity",
    asking_valuation: 50000000,
    round_size: 10000000,
    proposed_check: 3000000,
    created_at: "2024-01-05",
    updated_at: "2024-02-08",
  },
];

export function DealPipeline() {
  const [deals] = useState<Deal[]>(MOCK_DEALS);

  const getDealsByStage = (stage: DealStage) =>
    deals.filter((deal) => deal.stage === stage);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-border">
        <div>
          <h1 className="text-2xl font-semibold">Deal Pipeline</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {deals.length} active deals across {PIPELINE_STAGES.length} stages
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <SortAsc className="h-4 w-4 mr-2" />
            Sort
          </Button>
        </div>
      </div>

      {/* Pipeline Board */}
      <div className="flex-1 overflow-x-auto p-6">
        <div className="flex gap-4 h-full min-w-max">
          {PIPELINE_STAGES.map((stage) => {
            const stageDeals = getDealsByStage(stage.key);
            return (
              <div
                key={stage.key}
                className="w-80 flex-shrink-0 flex flex-col bg-secondary/30 rounded-lg"
              >
                {/* Column Header */}
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className={`h-2 w-2 rounded-full ${stage.color}`}
                      />
                      <h3 className="font-medium">{stage.label}</h3>
                    </div>
                    <Badge variant="secondary">{stageDeals.length}</Badge>
                  </div>
                </div>

                {/* Cards */}
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {stageDeals.map((deal) => (
                    <DealCard key={deal.id} deal={deal} />
                  ))}
                  {stageDeals.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No deals in this stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
