"use client";

import { DivergenceView } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, Users } from "lucide-react";

interface DivergenceHeatMapProps {
  data: DivergenceView;
}

export function DivergenceHeatMap({ data }: DivergenceHeatMapProps) {
  const getScoreColor = (score: number) => {
    if (score <= 3) return "bg-red-500";
    if (score <= 5) return "bg-amber-500";
    if (score <= 7) return "bg-blue-500";
    return "bg-emerald-500";
  };

  const getDivergenceStatus = () => {
    if (data.has_consensus) {
      return {
        icon: CheckCircle,
        label: "Consensus",
        color: "text-emerald-500",
        bg: "bg-emerald-500/10",
      };
    }
    if (data.needs_discussion) {
      return {
        icon: AlertTriangle,
        label: "Needs Discussion",
        color: "text-amber-500",
        bg: "bg-amber-500/10",
      };
    }
    return {
      icon: Users,
      label: "Mixed Views",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    };
  };

  const status = getDivergenceStatus();
  const StatusIcon = status.icon;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{data.company_name}</CardTitle>
          <Badge className={`${status.bg} ${status.color} border-0`}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Score Summary */}
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold">{data.average_score.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Avg Score</p>
          </div>
          <div>
            <p className="text-3xl font-bold">{data.divergence}</p>
            <p className="text-xs text-muted-foreground">Divergence</p>
          </div>
          <div>
            <p className="text-3xl font-bold">{data.min_score}-{data.max_score}</p>
            <p className="text-xs text-muted-foreground">Range</p>
          </div>
          <div>
            <p className="text-3xl font-bold">{data.total_votes}</p>
            <p className="text-xs text-muted-foreground">Votes</p>
          </div>
        </div>

        {/* Score Distribution */}
        <div>
          <p className="text-sm font-medium mb-3">Score Distribution</p>
          <div className="flex items-end gap-1 h-24">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((score) => {
              const count = data.score_distribution[score] || 0;
              const maxCount = Math.max(...Object.values(data.score_distribution));
              const height = maxCount > 0 ? (count / maxCount) * 100 : 0;

              return (
                <div
                  key={score}
                  className="flex-1 flex flex-col items-center gap-1"
                >
                  <div
                    className={`w-full rounded-t ${getScoreColor(score)} transition-all`}
                    style={{ height: `${height}%`, minHeight: count > 0 ? "4px" : "0" }}
                  />
                  <span className="text-xs text-muted-foreground">{score}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Flags */}
        <div className="grid grid-cols-2 gap-4">
          {/* Red Flags */}
          <div>
            <p className="text-sm font-medium mb-2 text-red-400">Top Red Flags</p>
            <div className="space-y-1">
              {data.top_red_flags.slice(0, 3).map((flag, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-xs bg-red-500/10 rounded px-2 py-1"
                >
                  <span className="truncate">{flag.flag}</span>
                  <Badge variant="outline" className="ml-2 h-5">
                    {flag.count}
                  </Badge>
                </div>
              ))}
              {data.top_red_flags.length === 0 && (
                <p className="text-xs text-muted-foreground">No red flags</p>
              )}
            </div>
          </div>

          {/* Green Flags */}
          <div>
            <p className="text-sm font-medium mb-2 text-emerald-400">Top Green Flags</p>
            <div className="space-y-1">
              {data.top_green_flags.slice(0, 3).map((flag, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-xs bg-emerald-500/10 rounded px-2 py-1"
                >
                  <span className="truncate">{flag.flag}</span>
                  <Badge variant="outline" className="ml-2 h-5">
                    {flag.count}
                  </Badge>
                </div>
              ))}
              {data.top_green_flags.length === 0 && (
                <p className="text-xs text-muted-foreground">No green flags</p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
