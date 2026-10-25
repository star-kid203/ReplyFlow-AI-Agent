// FILE: admin/app/packages/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import {
  Package,
  CheckCircle2,
  Users,
  MessageSquare,
  Shield,
  Layers,
  ArrowUpRight,
  RefreshCw,
  Building2,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

interface Subscriber {
  id: string;
  name: string;
  slug: string;
  status: string;
  is_active: boolean;
}

interface PackageTierData {
  tier_id: string;
  display_name: string;
  monthly_price_usd: number;
  monthly_response_limit: number;
  monthly_customer_limit: number;
  monthly_comment_limit: number;
  per_channel_comment_cap: number;
  allowed_channels: string[];
  features: string[];
  subscriber_count: number;
  subscribers: Subscriber[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function PackagesManagementPage() {
  const [packages, setPackages] = useState<PackageTierData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPackages = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/packages`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setPackages(data || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, []);

  const getTierColor = (tierId: string) => {
    switch (tierId) {
      case "startup":
        return "border-slate-800 text-slate-300";
      case "stella":
        return "border-indigo-800/80 text-indigo-400";
      case "business":
        return "border-amber-600/60 text-amber-400";
      case "business_premium":
        return "border-emerald-500/60 text-emerald-400";
      default:
        return "border-slate-800 text-slate-300";
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Package className="w-6 h-6 text-amber-400" /> Subscription Packages & Quota Limits
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Governance matrix for Start Up, Stella, Business, and Business Premium tiers with active subscriber distributions.
          </p>
        </div>

        <button
          onClick={fetchPackages}
          className="p-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl transition self-start"
          title="Refresh Packages"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* 4 Tier Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {packages.map((pkg) => (
          <div
            key={pkg.tier_id}
            className={`bg-slate-900/80 border ${getTierColor(pkg.tier_id)} rounded-2xl p-6 flex flex-col justify-between space-y-6 shadow-xl transition-all relative overflow-hidden`}
          >
            {pkg.tier_id === "business" && (
              <span className="absolute -right-12 top-6 bg-amber-500 text-slate-950 text-[9px] font-extrabold uppercase tracking-widest py-1 px-12 rotate-45 font-mono shadow">
                DOUATECH
              </span>
            )}
            {pkg.tier_id === "business_premium" && (
              <span className="absolute -right-12 top-6 bg-emerald-500 text-slate-950 text-[9px] font-extrabold uppercase tracking-widest py-1 px-12 rotate-45 font-mono shadow">
                ENTERPRISE
              </span>
            )}

            <div className="space-y-4">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  {pkg.tier_id.replace("_", " ")}
                </span>
                <h2 className="text-xl font-bold text-white mt-1">{pkg.display_name}</h2>
                <div className="mt-2 text-3xl font-extrabold text-white">
                  ${pkg.monthly_price_usd}
                  <span className="text-xs text-slate-400 font-normal"> / month</span>
                </div>
              </div>

              {/* Hard Quotas */}
              <div className="bg-slate-950/70 border border-slate-800/80 p-3.5 rounded-xl space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Replies / Mo:</span>
                  <span className="text-white font-bold">{pkg.monthly_response_limit.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Customers:</span>
                  <span className="text-white font-bold">{pkg.monthly_customer_limit.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Comments:</span>
                  <span className="text-white font-bold">{pkg.monthly_comment_limit.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Channel Cap:</span>
                  <span className="text-white font-bold">{pkg.per_channel_comment_cap.toLocaleString()}</span>
                </div>
              </div>

              {/* Allowed Channels */}
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-mono tracking-wider block mb-1.5">
                  Channels Included:
                </span>
                <div className="flex flex-wrap gap-1">
                  {pkg.allowed_channels.map((ch) => (
                    <span
                      key={ch}
                      className="text-[9px] px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 font-mono"
                    >
                      {ch.replace("_", " ")}
                    </span>
                  ))}
                </div>
              </div>

              {/* Feature Highlights */}
              <ul className="space-y-2 text-xs text-slate-300">
                {pkg.features.map((feat, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Subscriber Footprint */}
            <div className="pt-4 border-t border-slate-800/80">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-indigo-400" /> Subscribers:
                </span>
                <span className="text-white font-bold bg-slate-800 px-2 py-0.5 rounded-full font-mono">
                  {pkg.subscriber_count} Organizations
                </span>
              </div>

              {pkg.subscribers.length > 0 && (
                <div className="mt-2.5 space-y-1">
                  {pkg.subscribers.map((sub) => (
                    <div
                      key={sub.id}
                      className="text-[11px] text-slate-300 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800/80 flex items-center justify-between"
                    >
                      <span className="truncate">{sub.name}</span>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}