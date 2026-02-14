"use client";

import { DealStage, Deal } from "@/types";
import { DealCard } from "./DealCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Filter, SortAsc } from "lucide-react";
import { useDeals } from "@/hooks/useDeals";

const PIPELINE_STAGES: { key: DealStage; label: string; color: string }[] = [
  { key: "inbound", label: "Inbound", color: "bg-slate-500" },
  { key: "screening", label: "Screening", color: "bg-blue-500" },
  { key: "first_meeting", label: "First Meeting", color: "bg-indigo-500" },
  { key: "deep_dive", label: "Deep Dive", color: "bg-purple-500" },
  { key: "ic_review", label: "IC Review", color: "bg-amber-500" },
  { key: "term_sheet", label: "Term Sheet", color: "bg-emerald-500" },
];

function formatDealForCard(d: any): Deal {
  return {
    id: d.id,
    firm_id: d.firm_id,
    lead_partner_id: d.lead_partner_id,
    company_name: d.company_name,
    website: d.website,
    description: d.description,
    one_liner: d.one_liner,
    stage: d.stage,
    source: d.source,
    sector: d.sector,
    sub_sector: d.sub_sector,
    asking_valuation: d.asking_valuation != null ? Number(d.asking_valuation) : undefined,
    proposed_check: d.proposed_check != null ? Number(d.proposed_check) : undefined,
    round_size: d.round_size != null ? Number(d.round_size) : undefined,
    created_at: d.created_at,
    updated_at: d.updated_at,
  };
}

export function DealPipeline() {
  const { data, isLoading, error } = useDeals({ per_page: 200 });
  const deals = (data?.deals ?? []).map(formatDealForCard);

  const getDealsByStage = (stage: DealStage) =>
    deals.filter((deal) => deal.stage === stage);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-wasp-gold border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-destructive">Failed to load deals. Please try again.</p>
      </div>
    );
  }

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
