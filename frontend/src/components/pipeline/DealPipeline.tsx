"use client";

import { useState, useMemo } from "react";
import { DealStage, Deal } from "@/types";
import { DealCard } from "./DealCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Filter, SortAsc, Check } from "lucide-react";
import { useDeals } from "@/hooks/useDeals";
import { useSearch } from "@/contexts/SearchContext";
import { DealDetailModal } from "./DealDetailModal";

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

type SortBy = "updated" | "valuation" | "company";

export function DealPipeline() {
  const { search } = useSearch();
  const [filterStage, setFilterStage] = useState<DealStage | "all">("all");
  const [filterSector, setFilterSector] = useState<string>("");
  const [sortBy, setSortBy] = useState<SortBy>("updated");
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data, isLoading, error } = useDeals({
    per_page: 200,
    stage: filterStage === "all" ? undefined : filterStage,
    sector: filterSector || undefined,
    search: search || undefined,
  });

  const rawDeals = (data?.deals ?? []).map(formatDealForCard);

  const deals = useMemo(() => {
    let list = [...rawDeals];
    if (filterStage !== "all") {
      list = list.filter((d) => d.stage === filterStage);
    }
    if (filterSector) {
      list = list.filter((d) => d.sector === filterSector);
    }
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (d) =>
          d.company_name?.toLowerCase().includes(q) ||
          d.one_liner?.toLowerCase().includes(q) ||
          d.sector?.toLowerCase().includes(q)
      );
    }
    if (sortBy === "valuation") {
      list.sort((a, b) => (b.asking_valuation ?? 0) - (a.asking_valuation ?? 0));
    } else if (sortBy === "company") {
      list.sort((a, b) => (a.company_name ?? "").localeCompare(b.company_name ?? ""));
    } else {
      list.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    }
    return list;
  }, [rawDeals, search, sortBy, filterStage, filterSector]);

  const getDealsByStage = (stage: DealStage) =>
    deals.filter((deal) => deal.stage === stage);

  const sectors = useMemo(() => {
    const s = new Set<string>();
    rawDeals.forEach((d) => d.sector && s.add(d.sector));
    return Array.from(s).sort();
  }, [rawDeals]);

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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Stage</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => setFilterStage("all")}>
                {filterStage === "all" ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                All stages
              </DropdownMenuItem>
              {PIPELINE_STAGES.map((s) => (
                <DropdownMenuItem key={s.key} onClick={() => setFilterStage(s.key)}>
                  {filterStage === s.key ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                  {s.label}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Sector</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => setFilterSector("")}>
                {!filterSector ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                All sectors
              </DropdownMenuItem>
              {sectors.map((sec) => (
                <DropdownMenuItem key={sec} onClick={() => setFilterSector(sec)}>
                  {filterSector === sec ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                  {sec}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <SortAsc className="h-4 w-4 mr-2" />
                Sort
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={() => setSortBy("updated")}>
                {sortBy === "updated" ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                Latest updated
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("valuation")}>
                {sortBy === "valuation" ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                Valuation (high → low)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("company")}>
                {sortBy === "company" ? <Check className="h-4 w-4 mr-2" /> : <span className="w-4 mr-2" />}
                Company name A–Z
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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
                    <DealCard
                      key={deal.id}
                      deal={deal}
                      onClick={() => {
                        setSelectedDeal(deal);
                        setDetailOpen(true);
                      }}
                    />
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

      <DealDetailModal
        deal={selectedDeal}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />
    </div>
  );
}
