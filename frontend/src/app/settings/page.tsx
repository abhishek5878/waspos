"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Mail, MessageSquare, ToggleLeft } from "lucide-react";

export default function SettingsPage() {
  const { user, isDemo } = useAuthStore();
  const [emailConnected, setEmailConnected] = useState(false);
  const [slackConnected, setSlackConnected] = useState(false);
  const [aiAutoSummarize, setAiAutoSummarize] = useState(true);
  const [aiExtractContacts, setAiExtractContacts] = useState(true);
  const [aiFlagFollowUps, setAiFlagFollowUps] = useState(true);

  return (
    <DashboardLayout>
      <div className="p-8 max-w-3xl">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configure your firm and AI agent integrations.
        </p>

        <div className="mt-6 p-4 rounded-lg bg-secondary/50">
          <h3 className="font-medium">Account</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {user?.full_name} ({user?.email})
          </p>
          {isDemo && (
            <p className="text-xs text-wasp-gold mt-2">Demo account</p>
          )}
        </div>

        <div className="mt-8 space-y-6">
          <h2 className="text-lg font-medium">AI Agent Integrations</h2>
          <p className="text-sm text-muted-foreground -mt-4">
            Connect your email and Slack so the AI agent can track founder conversations and surface insights.
          </p>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle>Email</CardTitle>
                  <CardDescription>Gmail, Outlook, or IMAP</CardDescription>
                </div>
              </div>
              <Button
                variant={emailConnected ? "outline" : "wasp"}
                size="sm"
                onClick={() => setEmailConnected(!emailConnected)}
                disabled={isDemo}
              >
                {emailConnected ? "Disconnect" : "Connect"}
              </Button>
            </CardHeader>
            {emailConnected && (
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground">
                  AI will scan deal-related threads and extract key updates, meeting notes, and follow-ups.
                </p>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                  <MessageSquare className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle>Slack</CardTitle>
                  <CardDescription>Workspace channels and DMs</CardDescription>
                </div>
              </div>
              <Button
                variant={slackConnected ? "outline" : "wasp"}
                size="sm"
                onClick={() => setSlackConnected(!slackConnected)}
                disabled={isDemo}
              >
                {slackConnected ? "Disconnect" : "Connect"}
              </Button>
            </CardHeader>
            {slackConnected && (
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground">
                  AI will monitor deal channels for updates, intros, and action items.
                </p>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                  <ToggleLeft className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle>Granular AI Controls</CardTitle>
                  <CardDescription>Choose what the AI agent can do</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-summarize emails</Label>
                  <p className="text-xs text-muted-foreground">Generate brief summaries of deal-related threads</p>
                </div>
                <button
                  onClick={() => !isDemo && setAiAutoSummarize(!aiAutoSummarize)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${aiAutoSummarize ? "bg-wasp-gold" : "bg-secondary"} ${isDemo ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${aiAutoSummarize ? "left-6" : "left-1"}`} />
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Extract contacts</Label>
                  <p className="text-xs text-muted-foreground">Pull founder/team contacts from emails</p>
                </div>
                <button
                  onClick={() => !isDemo && setAiExtractContacts(!aiExtractContacts)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${aiExtractContacts ? "bg-wasp-gold" : "bg-secondary"} ${isDemo ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${aiExtractContacts ? "left-6" : "left-1"}`} />
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Flag follow-ups</Label>
                  <p className="text-xs text-muted-foreground">Highlight threads needing your response</p>
                </div>
                <button
                  onClick={() => !isDemo && setAiFlagFollowUps(!aiFlagFollowUps)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${aiFlagFollowUps ? "bg-wasp-gold" : "bg-secondary"} ${isDemo ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${aiFlagFollowUps ? "left-6" : "left-1"}`} />
                </button>
              </div>
              {isDemo && (
                <p className="text-xs text-wasp-gold pt-2">
                  Connect your backend to enable AI integrations.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
