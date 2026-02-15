"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { Deal } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Upload, FileText } from "lucide-react";

interface DealDetailModalProps {
  deal: Deal | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DealDetailModal({ deal, open, onOpenChange }: DealDetailModalProps) {
  const isDemo = useAuthStore((s) => s.isDemo);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length) setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (!deal?.id || !file || isDemo) return;
    setUploading(true);
    setUploadSuccess(false);
    try {
      await api.uploadDocument(file, deal.id, "pitch_deck");
      setUploadSuccess(true);
      setFile(null);
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  if (!deal) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{deal.company_name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {deal.one_liner && (
            <p className="text-sm text-muted-foreground">{deal.one_liner}</p>
          )}
          <div className="flex flex-wrap gap-2">
            {deal.sector && <Badge variant="outline">{deal.sector}</Badge>}
            <Badge variant="secondary" className="capitalize">{deal.source.replace("_", " ")}</Badge>
            <Badge variant="secondary">{deal.stage.replace("_", " ")}</Badge>
          </div>
          <div className="text-sm space-y-1">
            {deal.asking_valuation && (
              <p>Valuation: {formatCurrency(deal.asking_valuation)}</p>
            )}
            {deal.round_size && (
              <p>Round: {formatCurrency(deal.round_size)}</p>
            )}
            <p className="text-muted-foreground">Added {formatDate(deal.created_at)}</p>
          </div>

          <div className="pt-4 border-t border-border">
            <h4 className="font-medium mb-2">Upload Pitch Deck</h4>
            {isDemo ? (
              <p className="text-sm text-muted-foreground">Connect your backend to upload pitch decks.</p>
            ) : (
              <>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
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
                      <Upload className="h-6 w-6" />
                      Drop PDF or PPTX here, or click to browse
                    </div>
                  )}
                </div>
                {file && (
                  <Button
                    variant="wasp"
                    size="sm"
                    className="mt-2 w-full"
                    onClick={handleUpload}
                    disabled={uploading}
                  >
                    {uploading ? "Uploading..." : "Upload"}
                  </Button>
                )}
                {uploadSuccess && (
                  <p className="text-sm text-green-500 mt-2">Pitch deck uploaded successfully.</p>
                )}
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
