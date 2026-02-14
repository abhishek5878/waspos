"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { BlindPollConfession } from "@/components/radar/BlindPollConfession";
import { DivergenceReveal } from "@/components/radar/DivergenceReveal";

// Mock data - replace with real API call
const MOCK_POLL = {
  id: "poll-1",
  deal_id: "deal-1",
  firm_id: "firm-1",
  title: "IC Vote: TechStartup AI",
  description: "Series A investment decision",
  company_name: "TechStartup AI",
  one_liner: "AI-powered customer service automation",
  is_active: true,
  is_revealed: false,
  reveal_threshold: 3,
  total_votes: 4,
  ic_meeting_date: "2024-02-20T14:00:00Z",
};

export default function PollPage() {
  const params = useParams();
  const pollId = params.pollId as string;

  const [poll, setPoll] = useState(MOCK_POLL);
  const [hasVoted, setHasVoted] = useState(false);
  const [isLeadPartner] = useState(true); // Would come from auth context

  const handleVoteSubmit = async (vote: any) => {
    console.log("Vote submitted:", vote);
    setHasVoted(true);
    // API call would go here
  };

  const handleReveal = async () => {
    setPoll({ ...poll, is_revealed: true });
    // API call would go here
  };

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
        <DivergenceReveal pollId={pollId} companyName={poll.company_name} />
      )}
    </div>
  );
}
