"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { BlindPollConfession } from "@/components/radar/BlindPollConfession";
import { DivergenceReveal } from "@/components/radar/DivergenceReveal";
import { api } from "@/lib/api";
import type { DivergenceViewData } from "@/components/radar/DivergenceReveal";

export default function PollPage() {
  const params = useParams();
  const pollId = params.pollId as string;

  const [poll, setPoll] = useState<{
    id: string;
    deal_id: string;
    firm_id: string;
    title: string;
    description?: string;
    company_name: string;
    is_active: boolean;
    is_revealed: boolean;
    reveal_threshold: number;
    total_votes: number;
  } | null>(null);
  const [divergenceData, setDivergenceData] = useState<DivergenceViewData | null>(null);
  const [hasVoted, setHasVoted] = useState(false);
  const [isLeadPartner] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPoll() {
      try {
        const p = await api.getPoll(pollId);
        setPoll({
          ...p,
          company_name: (p as { company_name?: string }).company_name || p.title || "Deal",
          total_votes: p.vote_count ?? 0,
        });
        if (p.is_revealed) {
          const dv = await api.getDivergenceView(pollId);
          setDivergenceData(dv as DivergenceViewData);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load poll");
        setPoll({
          id: pollId,
          deal_id: "",
          firm_id: "",
          title: "IC Vote",
          company_name: "Deal",
          is_active: true,
          is_revealed: false,
          reveal_threshold: 3,
          total_votes: 0,
        });
      } finally {
        setLoading(false);
      }
    }
    fetchPoll();
  }, [pollId]);

  const FLAG_LABELS: Record<string, string> = {
    market_timing: "Market Timing",
    team_risk: "Team Risk",
    competition: "Competition",
    unit_economics: "Unit Economics",
    regulatory: "Regulatory Risk",
    technical: "Technical Risk",
    capital_intensive: "Capital Intensive",
    concentration: "Customer Concentration",
    founder_quality: "Exceptional Founders",
    market_size: "Massive TAM",
    traction: "Strong Traction",
    moat: "Deep Moat",
    network_effects: "Network Effects",
    unique_insight: "Unique Insight",
    capital_efficient: "Capital Efficient",
    timing: "Perfect Timing",
  };

  const handleVoteSubmit = async (vote: { score: number; redFlags: string[]; greenFlags: string[]; notes?: string }) => {
    try {
      await api.submitVote(pollId, {
        conviction_score: vote.score,
        red_flags: vote.redFlags.map((id) => FLAG_LABELS[id] || id),
        green_flags: vote.greenFlags.map((id) => FLAG_LABELS[id] || id),
        private_notes: vote.notes,
      });
      setHasVoted(true);
    } catch (e) {
      console.error("Vote failed:", e);
    }
  };

  const handleReveal = async () => {
    try {
      const updated = await api.revealPoll(pollId);
      setPoll((prev) => (prev ? { ...prev, is_revealed: true } : null));
      const dv = await api.getDivergenceView(pollId);
      setDivergenceData(dv as DivergenceViewData);
    } catch (e) {
      console.error("Reveal failed:", e);
    }
  };

  if (loading || !poll) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center text-zinc-400">
        {loading ? "Loading..." : error || "Poll not found"}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {!poll.is_revealed ? (
        <BlindPollConfession
          poll={poll}
          hasVoted={hasVoted}
          isLeadPartner={isLeadPartner}
          onVoteSubmit={handleVoteSubmit}
          onReveal={handleReveal}
        />
      ) : (
        <DivergenceReveal
          pollId={pollId}
          companyName={poll.company_name}
          data={divergenceData}
        />
      )}
    </div>
  );
}
