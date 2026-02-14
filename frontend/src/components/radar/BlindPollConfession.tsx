"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Eye,
  EyeOff,
  Lock,
  AlertTriangle,
  Shield,
  Users,
  Clock,
  CheckCircle,
} from "lucide-react";

interface BlindPollConfessionProps {
  poll: {
    id: string;
    title: string;
    company_name: string;
    one_liner?: string;
    is_active: boolean;
    total_votes: number;
    reveal_threshold: number;
    ic_meeting_date?: string;
  };
  hasVoted: boolean;
  isLeadPartner: boolean;
  onVoteSubmit: (vote: {
    score: number;
    redFlags: string[];
    greenFlags: string[];
    notes?: string;
  }) => void;
  onReveal: () => void;
}

const CONFESSION_RED_FLAGS = [
  { id: "market_timing", label: "Market Timing", icon: "⏰" },
  { id: "team_risk", label: "Team Risk", icon: "👥" },
  { id: "competition", label: "Competition", icon: "⚔️" },
  { id: "unit_economics", label: "Unit Economics", icon: "📉" },
  { id: "regulatory", label: "Regulatory Risk", icon: "⚖️" },
  { id: "technical", label: "Technical Risk", icon: "🔧" },
  { id: "capital_intensive", label: "Capital Intensive", icon: "💰" },
  { id: "concentration", label: "Customer Concentration", icon: "🎯" },
];

const CONFESSION_GREEN_FLAGS = [
  { id: "founder_quality", label: "Exceptional Founders", icon: "⭐" },
  { id: "market_size", label: "Massive TAM", icon: "📈" },
  { id: "traction", label: "Strong Traction", icon: "🚀" },
  { id: "moat", label: "Deep Moat", icon: "🏰" },
  { id: "network_effects", label: "Network Effects", icon: "🕸️" },
  { id: "unique_insight", label: "Unique Insight", icon: "💡" },
  { id: "capital_efficient", label: "Capital Efficient", icon: "💎" },
  { id: "timing", label: "Perfect Timing", icon: "🎯" },
];

export function BlindPollConfession({
  poll,
  hasVoted,
  isLeadPartner,
  onVoteSubmit,
  onReveal,
}: BlindPollConfessionProps) {
  const [score, setScore] = useState<number | null>(null);
  const [redFlags, setRedFlags] = useState<string[]>([]);
  const [greenFlags, setGreenFlags] = useState<string[]>([]);
  const [confession, setConfession] = useState("");
  const [showConfirmation, setShowConfirmation] = useState(false);

  const toggleFlag = (
    flagId: string,
    flags: string[],
    setFlags: (f: string[]) => void
  ) => {
    if (flags.includes(flagId)) {
      setFlags(flags.filter((f) => f !== flagId));
    } else {
      setFlags([...flags, flagId]);
    }
  };

  const handleSubmit = () => {
    if (score === null) return;
    onVoteSubmit({
      score,
      redFlags,
      greenFlags,
      notes: confession || undefined,
    });
  };

  const canReveal = poll.total_votes >= poll.reveal_threshold;

  if (hasVoted) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-lg w-full text-center space-y-8">
          {/* Sealed envelope visual */}
          <div className="relative">
            <div className="w-32 h-32 mx-auto bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-2xl border border-zinc-700 flex items-center justify-center">
              <Lock className="w-12 h-12 text-zinc-500" />
            </div>
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-emerald-500/20 text-emerald-400 px-4 py-1 rounded-full text-xs font-medium border border-emerald-500/30">
              <CheckCircle className="w-3 h-3 inline mr-1" />
              Sealed
            </div>
          </div>

          <div>
            <h1 className="text-2xl font-light text-white tracking-tight">
              Your conviction is sealed
            </h1>
            <p className="text-zinc-500 mt-2">
              Hidden until the Managing Partner reveals divergence
            </p>
          </div>

          {/* Anonymous vote count */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center justify-center gap-3 text-zinc-400">
              <Users className="w-5 h-5" />
              <span className="text-lg">
                <span className="text-white font-semibold">{poll.total_votes}</span>
                {" "}voices in the darkness
              </span>
            </div>
            <p className="text-xs text-zinc-600 mt-3">
              {poll.reveal_threshold - poll.total_votes > 0
                ? `${poll.reveal_threshold - poll.total_votes} more needed to unlock`
                : "Ready to reveal"}
            </p>
          </div>

          {/* Lead Partner reveal button */}
          {isLeadPartner && (
            <div className="pt-4">
              <Button
                onClick={onReveal}
                disabled={!canReveal}
                className={cn(
                  "w-full py-6 text-lg font-medium transition-all duration-500",
                  canReveal
                    ? "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white"
                    : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                )}
              >
                <Eye className="w-5 h-5 mr-2" />
                Reveal Divergence
              </Button>
              {!canReveal && (
                <p className="text-xs text-zinc-600 mt-2">
                  Waiting for {poll.reveal_threshold - poll.total_votes} more votes
                </p>
              )}
            </div>
          )}

          {/* IC Meeting countdown */}
          {poll.ic_meeting_date && (
            <div className="flex items-center justify-center gap-2 text-zinc-500 text-sm">
              <Clock className="w-4 h-4" />
              IC Meeting:{" "}
              {new Date(poll.ic_meeting_date).toLocaleDateString("en-US", {
                weekday: "long",
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-full px-4 py-2 mb-6">
            <EyeOff className="w-4 h-4 text-zinc-500" />
            <span className="text-sm text-zinc-400">Private Confession</span>
          </div>

          <h1 className="text-4xl font-light text-white tracking-tight mb-3">
            {poll.company_name}
          </h1>
          {poll.one_liner && (
            <p className="text-lg text-zinc-500">{poll.one_liner}</p>
          )}
        </div>

        {/* Conviction Score */}
        <div className="mb-12">
          <h2 className="text-center text-sm uppercase tracking-widest text-zinc-500 mb-6">
            Your Conviction
          </h2>

          <div className="grid grid-cols-10 gap-2">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((num) => (
              <button
                key={num}
                onClick={() => setScore(num)}
                className={cn(
                  "aspect-square rounded-lg border-2 text-xl font-bold transition-all duration-200",
                  score === num
                    ? num <= 3
                      ? "bg-red-500/20 border-red-500 text-red-400"
                      : num <= 5
                      ? "bg-amber-500/20 border-amber-500 text-amber-400"
                      : num <= 7
                      ? "bg-blue-500/20 border-blue-500 text-blue-400"
                      : "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                    : "border-zinc-800 text-zinc-600 hover:border-zinc-600 hover:text-zinc-400"
                )}
              >
                {num}
              </button>
            ))}
          </div>

          {/* Score label */}
          <div className="text-center mt-4">
            <AnimatePresence mode="wait">
              {score && (
                <motion.p
                  key={score}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={cn(
                    "text-lg font-medium",
                    score <= 3
                      ? "text-red-400"
                      : score <= 5
                      ? "text-amber-400"
                      : score <= 7
                      ? "text-blue-400"
                      : "text-emerald-400"
                  )}
                >
                  {score <= 2
                    ? "Strong Pass"
                    : score <= 4
                    ? "Lean Pass"
                    : score <= 6
                    ? "Neutral"
                    : score <= 8
                    ? "Lean Invest"
                    : "Strong Conviction"}
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Red Flags - What haunts you */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <h2 className="text-sm uppercase tracking-widest text-zinc-500">
              What haunts you?
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {CONFESSION_RED_FLAGS.map((flag) => (
              <button
                key={flag.id}
                onClick={() => toggleFlag(flag.id, redFlags, setRedFlags)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-200 text-left",
                  redFlags.includes(flag.id)
                    ? "bg-red-500/10 border-red-500/50 text-red-300"
                    : "border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-400"
                )}
              >
                <span className="text-lg">{flag.icon}</span>
                <span className="text-sm">{flag.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Green Flags - What excites you */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm uppercase tracking-widest text-zinc-500">
              What excites you?
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {CONFESSION_GREEN_FLAGS.map((flag) => (
              <button
                key={flag.id}
                onClick={() => toggleFlag(flag.id, greenFlags, setGreenFlags)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-200 text-left",
                  greenFlags.includes(flag.id)
                    ? "bg-emerald-500/10 border-emerald-500/50 text-emerald-300"
                    : "border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-400"
                )}
              >
                <span className="text-lg">{flag.icon}</span>
                <span className="text-sm">{flag.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Private Confession */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Lock className="w-4 h-4 text-zinc-400" />
            <h2 className="text-sm uppercase tracking-widest text-zinc-500">
              Private confession
            </h2>
            <span className="text-xs text-zinc-600">(only you can see this)</span>
          </div>

          <textarea
            value={confession}
            onChange={(e) => setConfession(e.target.value)}
            placeholder="What would you tell yourself 5 years from now about this decision?"
            rows={3}
            className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-700 resize-none"
          />
        </div>

        {/* Submit */}
        <Button
          onClick={handleSubmit}
          disabled={score === null}
          className={cn(
            "w-full py-6 text-lg font-medium transition-all duration-300",
            score !== null
              ? "bg-white text-black hover:bg-zinc-200"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          )}
        >
          <Lock className="w-5 h-5 mr-2" />
          Seal Your Conviction
        </Button>

        {/* Privacy assurance */}
        <p className="text-center text-xs text-zinc-600 mt-4">
          Your vote is encrypted and anonymous until reveal.
          <br />
          No one—not even the Managing Partner—can see individual votes before unlock.
        </p>
      </div>
    </div>
  );
}
