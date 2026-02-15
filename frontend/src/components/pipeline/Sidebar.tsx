"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSearch } from "@/contexts/SearchContext";
import { NewDealDialog } from "./NewDealDialog";
import {
  LayoutDashboard,
  FileText,
  Users,
  BarChart3,
  Settings,
  PlusCircle,
  Search,
  Zap,
  Vote,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth";

const navigation = [
  { name: "Pipeline", href: "/", icon: LayoutDashboard },
  { name: "Deals", href: "/deals", icon: FileText },
  { name: "Ghostwriter", href: "/ghostwriter", icon: Zap },
  { name: "IC Polls", href: "/polls", icon: Vote },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Team", href: "/team", icon: Users },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [newDealOpen, setNewDealOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { search, setSearch } = useSearch();

  return (
    <div
      className={cn(
        "flex flex-col border-r border-border bg-card transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-wasp-gold flex items-center justify-center">
              <span className="text-wasp-navy font-bold text-lg">W</span>
            </div>
            <span className="font-semibold text-lg">Wasp-OS</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-accent rounded-md transition-colors"
        >
          <svg
            className={cn(
              "h-4 w-4 transition-transform",
              collapsed && "rotate-180"
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search deals..."
              className="pl-9 bg-secondary border-0"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      )}

      {/* New Deal Button */}
      <div className="px-4 mb-4">
        <Button
          variant="wasp"
          className={cn("w-full", collapsed && "px-2")}
          onClick={() => setNewDealOpen(true)}
        >
          <PlusCircle className="h-4 w-4" />
          {!collapsed && <span className="ml-2">New Deal</span>}
        </Button>
        <NewDealDialog open={newDealOpen} onOpenChange={setNewDealOpen} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navigation.map((item) => {
          const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                collapsed && "justify-center"
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="border-t border-border p-4 space-y-2">
        <div
          className={cn(
            "flex items-center gap-3",
            collapsed && "justify-center"
          )}
        >
          <div className="h-8 w-8 rounded-full bg-wasp-gold/20 flex items-center justify-center flex-shrink-0">
            <span className="text-wasp-gold text-sm font-medium">
              {user?.full_name?.slice(0, 2).toUpperCase() || "?"}
            </span>
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name || "User"}</p>
              <p className="text-xs text-muted-foreground truncate capitalize">{user?.role || ""}</p>
            </div>
          )}
        </div>
        {!collapsed && (
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent rounded-md transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        )}
      </div>
    </div>
  );
}
