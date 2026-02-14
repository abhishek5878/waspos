"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Users,
  MessageSquare,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface DivergenceRevealProps {
  pollId: string;
  companyName: string;
}

// Mock divergence data - replace with API call
const MOCK_DIVERGENCE = {
  poll_id: "poll-1",
  deal_id: "deal-1",
  company_name: "TechStartup AI",
  total_votes: 5,
  average_score: 6.4,
  min_score: 3,
  max_score: 9,
  divergence: 6,
  std_deviation: 2.1,
  score_distribution: {
    1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 1, 9: 1, 10: 0,
  } as Record<number, number>,
  top_red_flags: [
    { flag: "Market Timing", count: 3 },
    { flag: "Competition", count: 2 },
    { flag: "Unit Economics", count: 2 },
  ],
  top_green_flags: [
    { flag: "Exceptional Founders", count: 4 },
    { flag: "Strong Traction", count: 3 },
    { flag: "Massive TAM", count: 2 },
  ],
  has_consensus: false,
  needs_discussion: true,
  votes: [
    { id: "v1", conviction_score: 9, user_name: "Sarah Chen", red_flags: ["Market Timing"], green_flags: ["Exceptional Founders", "Strong Traction"] },
    { id: "v2", conviction_score: 8, user_name: "Michael Park", red_flags: ["Competition"], green_flags: ["Exceptional Founders", "Massive TAM"] },
    { id: "v3", conviction_score: 7, user_name: "James Liu", red_flags: ["Unit Economics"], green_flags: ["Strong Traction", "Exceptional Founders"] },
    { id: "v4", conviction_score: 5, user_name: "Emma Wilson", red_flags: ["Market Timing", "Competition"], green_flags: ["Exceptional Founders"] },
    { id: "v5", conviction_score: 3, user_name: "David Kim", red_flags: ["Market Timing", "Unit Economics", "Competition"], green_flags: [] },
  ],
};

export function DivergenceReveal({ pollId, companyName }: DivergenceRevealProps) {
  const [data] = useState(MOCK_DIVERGENCE);
  const [showVotes, setShowVotes] = useState(false);
  const [animationPhase, setAnimationPhase] = useState(0);

  useEffect(() => {
    // Staggered reveal animation
    const timers = [
      setTimeout(() => setAnimationPhase(1), 500),  // Show divergence score
      setTimeout(() => setAnimationPhase(2), 1500), // Show distribution
      setTimeout(() => setAnimationPhase(3), 2500), // Show flags
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  const getDivergenceStatus = () => {
    if (data.divergence <= 2) {
      return {
        label: "Strong Consensus",
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/30",
        icon: CheckCircle,
      };
    }
    if (data.divergence >= 5) {
      return {
        label: "High Divergence",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        icon: AlertTriangle,
      };
    }
    return {
      label: "Mixed Views",
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
      icon: Users,
    };
  };

  const status = getDivergenceStatus();
  const StatusIcon = status.icon;

  const getScoreColor = (score: number) => {
    if (score <= 3) return "bg-red-500";
    if (score <= 5) return "bg-amber-500";
    if (score <= 7) return "bg-blue-500";
    return "bg-emerald-500";
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-light text-white tracking-tight mb-3">
            {companyName}
          </h1>
          <p className="text-zinc-500">The truth has been revealed</p>
        </div>

        {/* Main Divergence Display */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: animationPhase >= 1 ? 1 : 0, scale: animationPhase >= 1 ? 1 : 0.9 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={cn(
            "rounded-2xl border p-8 mb-8 text-center",
            status.bgColor,
            status.borderColor
          )}
        >
          <StatusIcon className={cn("w-12 h-12 mx-auto mb-4", status.color)} />

          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="text-7xl font-bold text-white">{data.divergence}</div>
            <div className="text-left">
              <div className={cn("text-lg font-medium", status.color)}>
                {status.label}
              </div>
              <div className="text-sm text-zinc-500">Point Spread</div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-8 text-zinc-400">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-red-400" />
              <span>Low: {data.min_score}</span>
            </div>
            <div className="text-2xl font-semibold text-white">
              Avg: {data.average_score.toFixed(1)}
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>High: {data.max_score}</span>
            </div>
          </div>
        </motion.div>

        {/* Score Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: animationPhase >= 2 ? 1 : 0, y: animationPhase >= 2 ? 0 : 20 }}
          transition={{ duration: 0.6 }}
          className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 mb-8"
        >
          <h3 className="text-sm uppercase tracking-widest text-zinc-500 mb-6 text-center">
            Conviction Distribution
          </h3>

          <div className="flex items-end justify-center gap-1 h-32 mb-4">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((score) => {
              const count = data.score_distribution[score] || 0;
              const maxCount = Math.max(...Object.values(data.score_distribution));
              const heightPercent = maxCount > 0 ? (count / maxCount) * 100 : 0;

              return (
                <div key={score} className="flex flex-col items-center flex-1">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPercent}%` }}
                    transition={{ duration: 0.5, delay: score * 0.1 }}
                    className={cn(
                      "w-full rounded-t-sm min-h-[4px]",
                      count > 0 ? getScoreColor(score) : "bg-zinc-800"
                    )}
                    style={{ minHeight: count > 0 ? "8px" : "4px" }}
                  />
                  <div className="mt-2 text-xs text-zinc-500">{score}</div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Flags Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: animationPhase >= 3 ? 1 : 0, y: animationPhase >= 3 ? 0 : 20 }}
          transition={{ duration: 0.6 }}
          className="grid grid-cols-2 gap-4 mb-8"
        >
          {/* Red Flags */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <h3 className="text-sm uppercase tracking-widest text-zinc-500">
                Shared Concerns
              </h3>
            </div>
            <div className="space-y-2">
              {data.top_red_flags.map((flag, i) => (
                <div
                  key={flag.flag}
                  className="flex items-center justify-between bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2"
                >
                  <span className="text-red-300 text-sm">{flag.flag}</span>
                  <span className="text-red-400 text-xs font-medium">
                    {flag.count}/{data.total_votes}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Green Flags */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm uppercase tracking-widest text-zinc-500">
                Shared Excitement
              </h3>
            </div>
            <div className="space-y-2">
              {data.top_green_flags.map((flag, i) => (
                <div
                  key={flag.flag}
                  className="flex items-center justify-between bg-emerald-500/5 border border-emerald-500/20 rounded-lg px-3 py-2"
                >
                  <span className="text-emerald-300 text-sm">{flag.flag}</span>
                  <span className="text-emerald-400 text-xs font-medium">
                    {flag.count}/{data.total_votes}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Individual Votes (Expandable) */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowVotes(!showVotes)}
            className="w-full flex items-center justify-between p-6 hover:bg-zinc-800/30 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-zinc-400" />
              <span className="text-sm uppercase tracking-widest text-zinc-500">
                Individual Convictions
              </span>
            </div>
            {showVotes ? (
              <ChevronUp className="w-5 h-5 text-zinc-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-zinc-500" />
            )}
          </button>

          {showVotes && (
            <div className="border-t border-zinc-800 divide-y divide-zinc-800">
              {data.votes
                .sort((a, b) => b.conviction_score - a.conviction_score)
                .map((vote) => (
                  <div
                    key={vote.id}
                    className="flex items-center gap-4 p-4 hover:bg-zinc-800/20 transition-colors"
                  >
                    {/* Score */}
                    <div
                      className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center text-xl font-bold",
                        vote.conviction_score <= 3
                          ? "bg-red-500/20 text-red-400"
                          : vote.conviction_score <= 5
                          ? "bg-amber-500/20 text-amber-400"
                          : vote.conviction_score <= 7
                          ? "bg-blue-500/20 text-blue-400"
                          : "bg-emerald-500/20 text-emerald-400"
                      )}
                    >
                      {vote.conviction_score}
                    </div>

                    {/* Name and flags */}
                    <div className="flex-1">
                      <div className="font-medium text-white">
                        {vote.user_name}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {vote.green_flags.slice(0, 2).map((flag) => (
                          <span
                            key={flag}
                            className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded"
                          >
                            {flag}
                          </span>
                        ))}
                        {vote.red_flags.slice(0, 2).map((flag) => (
                          <span
                            key={flag}
                            className="text-xs bg-red-500/10 text-red-400 px-2 py-0.5 rounded"
                          >
                            {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Discussion Prompt */}
        {data.needs_discussion && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 3 }}
            className="mt-8 bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 text-center"
          >
            <MessageSquare className="w-8 h-8 text-amber-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-amber-300 mb-2">
              This deal needs discussion
            </h3>
            <p className="text-sm text-amber-200/70">
              A {data.divergence}-point spread suggests significantly different
              reads on this opportunity. Schedule time to explore the divergence.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
