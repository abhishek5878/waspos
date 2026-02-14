"use client";

import { Deal } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Building2, Calendar, DollarSign, Zap } from "lucide-react";

interface DealCardProps {
  deal: Deal;
  onClick?: () => void;
}

export function DealCard({ deal, onClick }: DealCardProps) {
  return (
    <Card
      className="cursor-pointer hover:border-wasp-gold/50 transition-colors"
      onClick={onClick}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{deal.company_name}</h4>
            {deal.one_liner && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {deal.one_liner}
              </p>
            )}
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {deal.sector && (
            <Badge variant="outline" className="text-xs">
              {deal.sector}
            </Badge>
          )}
          <Badge variant="secondary" className="text-xs capitalize">
            {deal.source.replace("_", " ")}
          </Badge>
        </div>

        {/* Metrics */}
        <div className="space-y-2 text-xs">
          {deal.asking_valuation && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <DollarSign className="h-3 w-3" />
              <span>
                {formatCurrency(deal.asking_valuation)} valuation
              </span>
            </div>
          )}
          {deal.round_size && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Building2 className="h-3 w-3" />
              <span>{formatCurrency(deal.round_size)} round</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>Added {formatDate(deal.created_at)}</span>
          </div>
        </div>

        {/* AI Indicator */}
        {deal.team_summary && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 text-xs text-wasp-gold">
              <Zap className="h-3 w-3" />
              <span>AI-analyzed</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
