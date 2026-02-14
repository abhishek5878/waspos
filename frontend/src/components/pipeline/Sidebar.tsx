"use client";

import { useState } from "react";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const navigation = [
  { name: "Pipeline", href: "/", icon: LayoutDashboard, current: true },
  { name: "Deals", href: "/deals", icon: FileText, current: false },
  { name: "Ghostwriter", href: "/ghostwriter", icon: Zap, current: false },
  { name: "IC Polls", href: "/polls", icon: Vote, current: false },
  { name: "Analytics", href: "/analytics", icon: BarChart3, current: false },
  { name: "Team", href: "/team", icon: Users, current: false },
  { name: "Settings", href: "/settings", icon: Settings, current: false },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

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
            />
          </div>
        </div>
      )}

      {/* New Deal Button */}
      <div className="px-4 mb-4">
        <Button
          variant="wasp"
          className={cn("w-full", collapsed && "px-2")}
        >
          <PlusCircle className="h-4 w-4" />
          {!collapsed && <span className="ml-2">New Deal</span>}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navigation.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              item.current
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              collapsed && "justify-center"
            )}
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && <span>{item.name}</span>}
          </a>
        ))}
      </nav>

      {/* User */}
      <div className="border-t border-border p-4">
        <div
          className={cn(
            "flex items-center gap-3",
            collapsed && "justify-center"
          )}
        >
          <div className="h-8 w-8 rounded-full bg-wasp-gold/20 flex items-center justify-center">
            <span className="text-wasp-gold text-sm font-medium">JD</span>
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">Jane Doe</p>
              <p className="text-xs text-muted-foreground truncate">Partner</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
