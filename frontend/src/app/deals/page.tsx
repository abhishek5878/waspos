"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useDeals } from "@/hooks/useDeals";
import { useSearch } from "@/contexts/SearchContext";
import { DealDetailModal } from "@/components/pipeline/DealDetailModal";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Deal } from "@/types";

function formatDeal(d: any): Deal {
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

export default function DealsPage() {
  const { search } = useSearch();
  const { data, isLoading, error } = useDeals({ per_page: 200, search: search || undefined });
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const deals = (data?.deals ?? []).map(formatDeal).filter((d) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return d.company_name?.toLowerCase().includes(q) || d.one_liner?.toLowerCase().includes(q) || d.sector?.toLowerCase().includes(q);
  });

  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold">Deals</h1>
        <p className="text-muted-foreground mt-2">
          {deals.length} deals. Search from the sidebar. Click a deal to view details or upload a pitch deck.
        </p>
        {isLoading && <div className="mt-4 text-sm text-muted-foreground">Loading...</div>}
        {error && <div className="mt-4 text-sm text-destructive">Failed to load deals.</div>}
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {deals.map((deal) => (
            <Card
              key={deal.id}
              className="cursor-pointer hover:border-wasp-gold/50 transition-colors"
              onClick={() => { setSelectedDeal(deal); setDetailOpen(true); }}
            >
              <CardContent className="p-4">
                <h3 className="font-semibold">{deal.company_name}</h3>
                {deal.one_liner && <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{deal.one_liner}</p>}
                <div className="flex flex-wrap gap-1 mt-2">
                  {deal.sector && <Badge variant="outline" className="text-xs">{deal.sector}</Badge>}
                  <Badge variant="secondary" className="text-xs capitalize">{deal.source.replace("_", " ")}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {deal.asking_valuation && formatCurrency(deal.asking_valuation)} · {formatDate(deal.created_at)}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      <DealDetailModal deal={selectedDeal} open={detailOpen} onOpenChange={setDetailOpen} />
    </DashboardLayout>
  );
}
