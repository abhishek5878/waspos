"use client";

import { useState } from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, Minus, Plus } from "lucide-react";

interface ConvictionSliderProps {
  dealName: string;
  onSubmit: (vote: {
    score: number;
    redFlags: string[];
    greenFlags: string[];
    notes?: string;
  }) => void;
}

const RED_FLAG_OPTIONS = [
  "Market timing",
  "Team risk",
  "Competition",
  "Unit economics",
  "Regulatory",
  "Technical risk",
  "Customer concentration",
  "Capital intensive",
];

const GREEN_FLAG_OPTIONS = [
  "Strong team",
  "Large TAM",
  "Product-market fit",
  "Network effects",
  "Capital efficient",
  "Unique insight",
  "Strong traction",
  "Defensible moat",
];

export function ConvictionSlider({ dealName, onSubmit }: ConvictionSliderProps) {
  const [score, setScore] = useState(5);
  const [redFlags, setRedFlags] = useState<string[]>([]);
  const [greenFlags, setGreenFlags] = useState<string[]>([]);
  const [notes, setNotes] = useState("");

  const getScoreLabel = (s: number) => {
    if (s <= 2) return "Strong Pass";
    if (s <= 4) return "Lean Pass";
    if (s <= 6) return "Neutral";
    if (s <= 8) return "Lean Invest";
    return "Strong Conviction";
  };

  const getScoreColor = (s: number) => {
    if (s <= 3) return "text-red-500";
    if (s <= 5) return "text-amber-500";
    if (s <= 7) return "text-blue-500";
    return "text-emerald-500";
  };

  const toggleFlag = (
    flag: string,
    flags: string[],
    setFlags: (f: string[]) => void
  ) => {
    if (flags.includes(flag)) {
      setFlags(flags.filter((f) => f !== flag));
    } else {
      setFlags([...flags, flag]);
    }
  };

  const handleSubmit = () => {
    onSubmit({
      score,
      redFlags,
      greenFlags,
      notes: notes || undefined,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Vote: {dealName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Score Slider */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Conviction Score</span>
            <div className="flex items-center gap-2">
              <span className={cn("text-3xl font-bold", getScoreColor(score))}>
                {score}
              </span>
              <span className="text-sm text-muted-foreground">/10</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setScore(Math.max(1, score - 1))}
              disabled={score <= 1}
            >
              <Minus className="h-4 w-4" />
            </Button>

            <SliderPrimitive.Root
              className="relative flex w-full touch-none select-none items-center"
              value={[score]}
              onValueChange={([v]) => setScore(v)}
              max={10}
              min={1}
              step={1}
            >
              <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
                <SliderPrimitive.Range
                  className={cn(
                    "absolute h-full",
                    score <= 3
                      ? "bg-red-500"
                      : score <= 5
                      ? "bg-amber-500"
                      : score <= 7
                      ? "bg-blue-500"
                      : "bg-emerald-500"
                  )}
                />
              </SliderPrimitive.Track>
              <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" />
            </SliderPrimitive.Root>

            <Button
              variant="outline"
              size="icon"
              onClick={() => setScore(Math.min(10, score + 1))}
              disabled={score >= 10}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <p className={cn("text-center text-sm font-medium", getScoreColor(score))}>
            {getScoreLabel(score)}
          </p>
        </div>

        {/* Red Flags */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <span className="text-sm font-medium">Red Flags</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {RED_FLAG_OPTIONS.map((flag) => (
              <Badge
                key={flag}
                variant={redFlags.includes(flag) ? "destructive" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleFlag(flag, redFlags, setRedFlags)}
              >
                {flag}
              </Badge>
            ))}
          </div>
        </div>

        {/* Green Flags */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-medium">Green Flags</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {GREEN_FLAG_OPTIONS.map((flag) => (
              <Badge
                key={flag}
                variant={greenFlags.includes(flag) ? "default" : "outline"}
                className={cn(
                  "cursor-pointer",
                  greenFlags.includes(flag) && "bg-emerald-500 hover:bg-emerald-600"
                )}
                onClick={() => toggleFlag(flag, greenFlags, setGreenFlags)}
              >
                {flag}
              </Badge>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="text-sm font-medium mb-2 block">
            Private Notes (optional)
          </label>
          <Input
            placeholder="Any additional thoughts..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Submit */}
        <Button variant="wasp" className="w-full" onClick={handleSubmit}>
          Submit Vote
        </Button>
      </CardContent>
    </Card>
  );
}
