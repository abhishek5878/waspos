"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar } from "@/components/pipeline/Sidebar";
import { useAuthStore } from "@/store/auth";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, isHydrated, isDemo } = useAuthStore();

  // Fallback: if zustand persist doesn't fire (e.g. localStorage blocked), unblock after 500ms
  useEffect(() => {
    const t = setTimeout(() => {
      if (!useAuthStore.getState().isHydrated) {
        useAuthStore.setState({ isHydrated: true });
      }
    }, 500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    if (!token && pathname !== "/login") {
      router.replace("/login");
    }
  }, [token, isHydrated, pathname, router]);

  if (!isHydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-wasp-gold border-t-transparent" />
      </div>
    );
  }

  if (!token) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {isDemo && (
        <div className="bg-wasp-gold/10 border-b border-wasp-gold/30 px-4 py-2 text-center text-sm text-wasp-gold">
          Demo mode — using mock data.{" "}
          <a
            href="https://github.com/abhishek5878/waspos/blob/main/DEPLOYMENT.md"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-wasp-gold/80"
          >
            Deploy your backend
          </a>{" "}
          to use real data.
        </div>
      )}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
