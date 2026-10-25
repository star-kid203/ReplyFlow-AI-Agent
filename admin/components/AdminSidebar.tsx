// FILE: admin/components/AdminSidebar.tsx
"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlusCircle,
  Radio,
  Layers,
  Shield,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const navItems = [
  { name: "Executive Overview", href: "/", icon: LayoutDashboard },
  { name: "New Client", href: "/provision", icon: PlusCircle },
  { name: "Subscription Plan", href: "/packages", icon: Layers },
  { name: "Channel Gateways", href: "/channels", icon: Radio },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col justify-between shrink-0 transition-all duration-300 relative z-30 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3.5 top-7 bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200 rounded-full p-1 shadow-md z-40 transition"
        title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>

      <div>
        {/* Brand */}
        <div className="p-5 border-b border-slate-800 flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="truncate">
              <h1 className="font-bold text-white text-base tracking-wide truncate">ReplyFlow</h1>
              <p className="text-[11px] text-indigo-400 font-mono font-medium truncate">Organization HQ</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
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

      {/* Cluster Footer */}
      <div className="p-3 border-t border-slate-800">
        {!collapsed ? (
          <div className="bg-slate-950/70 rounded-xl p-3 text-xs border border-slate-800/80 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">Infrastructure</span>
            <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Multi-Tenant Cluster Active</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center p-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title="System Active" />
          </div>
        )}
      </div>
    </aside>
  );
}