"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateDeal } from "@/hooks/useDeals";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { DealStage, DealSource } from "@/types";
import { Upload, FileText } from "lucide-react";

interface NewDealDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const STAGES: { key: DealStage; label: string }[] = [
  { key: "inbound", label: "Inbound" },
  { key: "screening", label: "Screening" },
  { key: "first_meeting", label: "First Meeting" },
  { key: "deep_dive", label: "Deep Dive" },
  { key: "ic_review", label: "IC Review" },
  { key: "term_sheet", label: "Term Sheet" },
];

const SOURCES: { key: DealSource; label: string }[] = [
  { key: "inbound", label: "Inbound" },
  { key: "referral", label: "Referral" },
  { key: "portfolio_intro", label: "Portfolio Intro" },
  { key: "outbound", label: "Outbound" },
  { key: "conference", label: "Conference" },
  { key: "other", label: "Other" },
];

export function NewDealDialog({ open, onOpenChange }: NewDealDialogProps) {
  const isDemo = useAuthStore((s) => s.isDemo);
  const createDeal = useCreateDeal();
  const [companyName, setCompanyName] = useState("");
  const [website, setWebsite] = useState("");
  const [oneLiner, setOneLiner] = useState("");
  const [sector, setSector] = useState("");
  const [stage, setStage] = useState<DealStage>("inbound");
  const [source, setSource] = useState<DealSource>("inbound");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length) setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!companyName.trim()) {
      setError("Company name is required");
      return;
    }

    if (isDemo) {
      setError("Connect your backend to create real deals.");
      return;
    }

    try {
      setUploading(true);
      const deal = await createDeal.mutateAsync({
        company_name: companyName.trim(),
        website: website.trim() || undefined,
        one_liner: oneLiner.trim() || undefined,
        sector: sector.trim() || undefined,
        stage,
        source,
      });

      if (file && deal?.id) {
        try {
          await api.uploadDocument(file, deal.id, "pitch_deck");
        } catch (uploadErr) {
          console.error("Upload failed:", uploadErr);
          setError("Deal created but pitch deck upload failed.");
        }
      }

      onOpenChange(false);
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create deal");
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setCompanyName("");
    setWebsite("");
    setOneLiner("");
    setSector("");
    setStage("inbound");
    setSource("inbound");
    setFile(null);
    setError("");
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New Deal</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="company">Company Name *</Label>
            <Input
              id="company"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Acme Inc"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              type="url"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://acme.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="oneLiner">One-liner</Label>
            <Input
              id="oneLiner"
              value={oneLiner}
              onChange={(e) => setOneLiner(e.target.value)}
              placeholder="AI-powered workflow automation"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sector">Sector</Label>
              <Input
                id="sector"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                placeholder="Enterprise Software"
              />
            </div>
            <div className="space-y-2">
              <Label>Stage</Label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value as DealStage)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {STAGES.map((s) => (
                  <option key={s.key} value={s.key}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Source</Label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value as DealSource)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {SOURCES.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Pitch Deck (optional)</Label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragActive ? "border-wasp-gold bg-wasp-gold/5" : "border-border hover:border-wasp-gold/50"
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div className="flex items-center justify-center gap-2 text-sm">
                  <FileText className="h-4 w-4" />
                  {file.name}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-muted-foreground text-sm">
                  <Upload className="h-8 w-8" />
                  Drop PDF or PPTX here, or click to browse
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="wasp" disabled={uploading}>
              {uploading ? "Creating..." : "Create Deal"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
