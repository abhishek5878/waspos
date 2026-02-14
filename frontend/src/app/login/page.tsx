"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const { token, login, isHydrated } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Fallback: if zustand persist doesn't fire, unblock after 500ms
  useEffect(() => {
    const t = setTimeout(() => {
      if (!useAuthStore.getState().isHydrated) {
        useAuthStore.setState({ isHydrated: true });
      }
    }, 500);
    return () => clearTimeout(t);
  }, []);

  if (!isHydrated || (isHydrated && token)) {
    if (token) router.replace("/");
    if (!isHydrated) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-wasp-gold border-t-transparent" />
        </div>
      );
    }
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md border-border">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="h-12 w-12 rounded-xl bg-wasp-gold flex items-center justify-center">
              <span className="text-wasp-navy font-bold text-2xl">W</span>
            </div>
          </div>
          <CardTitle className="text-2xl">Wasp-OS</CardTitle>
          <CardDescription>Investment Operating System</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@firm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="bg-background"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="bg-background"
              />
            </div>
            <Button
              type="submit"
              variant="wasp"
              className="w-full"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() => {
                useAuthStore.getState().demoLogin();
                router.replace("/");
              }}
            >
              Try Demo
            </Button>
          </form>
          <p className="text-xs text-muted-foreground text-center mt-4">
            Sign in with your firm credentials, or try the demo to explore without a backend.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
