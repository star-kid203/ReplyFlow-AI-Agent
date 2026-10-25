// FILE: frontend/components/Sidebar.tsx
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  LayoutDashboard,
  Inbox,
  ShieldCheck,
  AlertOctagon,
  Database,
  Sparkles,
  Bot,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Zap,
} from "lucide-react";
import { getActiveTenantId } from "@/lib/tenant";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const clientNavigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Live Inbox", href: "/inbox", icon: Inbox },
  { name: "Approvals Queue", href: "/approvals", icon: ShieldCheck },
  { name: "Escalations", href: "/escalations", icon: AlertOctagon },
  { name: "Audit & Learning Farm", href: "/audit", icon: GraduationCap },
  { name: "Business Brain", href: "/knowledge", icon: Database },
  { name: "Social & Campaign Rules", href: "/simulator", icon: Sparkles },
  { name: "Usage & Billing", href: "/usage", icon: Zap },

];

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [collapsed, setCollapsed] = useState(false);
  const [tenantId, setTenantId] = useState<string>("");
  const [businessName, setBusinessName] = useState<string>("Loading...");
  const [agentName, setAgentName] = useState<string>("AI Agent");

  useEffect(() => {
    const id = getActiveTenantId();
    setTenantId(id);

    fetch(`${API_BASE}/businesses/${id}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setBusinessName(data.name);
          setAgentName(data.agent_display_name || `${data.name} AI`);
        }
      })
      .catch(() => {
        setBusinessName("Client Workspace");
      });
  }, [pathname, searchParams]);

  // Lock tenant ID to all navigation links so browser tabs never cross boundaries
  const queryParam = tenantId ? `?tenant=${tenantId}` : "";

  return (
    <aside
      className={`bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col justify-between shrink-0 transition-all duration-300 relative ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3.5 top-7 bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200 rounded-full p-1 shadow-md z-20 transition"
        title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>

      <div>
        <div className="p-5 border-b border-slate-800 flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 shrink-0">
            <Bot className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="truncate">
              <h1 className="font-bold text-white text-base tracking-wide truncate">ReplyFlow</h1>
              <p className="text-[11px] text-slate-400 truncate">Client Ops Workspace</p>
            </div>
          )}
        </div>

        <nav className="p-3 space-y-1.5">
          {clientNavigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={`${item.href}${queryParam}`}
                className={`flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/20 shadow-sm"
                    : "hover:bg-slate-800/60 hover:text-slate-200 text-slate-400"
                } ${collapsed ? "justify-center" : ""}`}
                title={collapsed ? item.name : undefined}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Dynamic Tenant Indicator Footer */}
      <div className="p-3 border-t border-slate-800">
        {!collapsed ? (
          <div className="bg-slate-950/60 rounded-xl p-3 text-xs border border-slate-800/80">
            <p className="text-slate-400 text-[10px] uppercase font-mono tracking-wider">Connected Client:</p>
            <p className="font-bold text-white truncate text-sm mt-0.5" title={businessName}>
              {businessName}
            </p>
            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {agentName}: Live & Grounded
            </div>
          </div>
        ) : (
          <div className="flex justify-center p-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title={businessName} />
          </div>
        )}
      </div>
    </aside>
  );
}