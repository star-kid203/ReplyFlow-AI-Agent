// FILE: admin/app/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  Plus,
  Trash2,
  Copy,
  Check,
  Search,
  ArrowUpRight,
  RefreshCw,
  Layers,
  Radio,
  Sliders,
} from "lucide-react";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  description: string;
  communication_style: string;
  plan_tier?: string;
  enabled_channels?: string[];
  is_active: boolean;
}

interface PlatformMetrics {
  total_tenants: number;
  total_conversations: number;
  total_messages: number;
}



const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ExecutiveOverviewPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, mRes] = await Promise.all([
        fetch(`${API_BASE}/businesses`, { cache: "no-store" }).catch(() => null),
        fetch(`${API_BASE}/businesses/platform/metrics`, { cache: "no-store" }).catch(() => null),
      ]);

      if (tRes && tRes.ok) {
        const tData = await tRes.json();
        setTenants(Array.isArray(tData) ? tData : []);
      }
      if (mRes && mRes.ok) {
        const mData = await mRes.json();
        setMetrics(mData);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to remove organization '${name}'?`)) return;
    try {
      const res = await fetch(`${API_BASE}/businesses/${id}`, { method: "DELETE" });
      if (res.ok) await loadData();
    } catch (e) {
      alert("Failed to delete organization");
    }
  };

  const copyWebhook = (id: string) => {
    const url = `${API_BASE}/webhooks/ingest?business_id=${id}`;
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredTenants = tenants.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Enterprise Client Management
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Global directory of onboarded organizations, active AI agents, and channel configurations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl transition"
            title="Refresh Directory"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            href="/provision"
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center gap-2 transition shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" /> Onboard Organization
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/70 border border-slate-800/80 p-5 rounded-2xl">
          <span className="text-xs text-slate-400 font-mono uppercase tracking-wider">Active Organizations</span>
          <div className="text-3xl font-bold text-white mt-2">{tenants.length}</div>
          <p className="text-xs text-slate-500 mt-1">Independent tenants provisioned</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 p-5 rounded-2xl">
          <span className="text-xs text-indigo-400 font-mono uppercase tracking-wider">Managed Operations</span>
          <div className="text-3xl font-bold text-indigo-400 mt-2">{metrics?.total_conversations || 0} Threads</div>
          <p className="text-xs text-slate-500 mt-1">Across all connected channels</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 p-5 rounded-2xl">
          <span className="text-xs text-emerald-400 font-mono uppercase tracking-wider">Processed Traffic</span>
          <div className="text-3xl font-bold text-emerald-400 mt-2">{metrics?.total_messages || 0} Messages</div>
          <p className="text-xs text-slate-500 mt-1">Customer & comment interactions</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 p-5 rounded-2xl">
          <span className="text-xs text-amber-400 font-mono uppercase tracking-wider">Tenant Isolation</span>
          <div className="text-3xl font-bold text-amber-400 mt-2">Logical RLS</div>
          <p className="text-xs text-slate-500 mt-1">Zero cross-tenant bleed</p>
        </div>
      </div>

      {/* Search & Directory */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search organizations by name or slug..."
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 placeholder:text-slate-500"
            />
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Showing {filteredTenants.length} of {tenants.length} tenants
          </span>
        </div>

        {/* Organizations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredTenants.map((t) => (
            <div
              key={t.id}
              className="bg-slate-900/70 border border-slate-800/80 hover:border-slate-700/80 p-6 rounded-2xl space-y-4 transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center font-bold text-white text-sm">
                      {t.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-base">{t.name}</h3>
                      <p className="text-xs text-slate-500 font-mono">ID: {t.id.slice(0, 8)}...</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 font-bold">
                      {t.plan_tier || "Enterprise"}
                    </span>
                    <button
                      onClick={() => handleDelete(t.id, t.name)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                      title="De-provision Organization"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                  {t.description || "Enterprise organization operating with customized AI customer operations."}
                </p>

                {/* Connected Channels */}
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono tracking-wider block mb-1.5">
                    Active Channels:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(t.enabled_channels || ["website_chat", "whatsapp", "linkedin_comment"]).map((ch) => (
                      <span
                        key={ch}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950 text-slate-300 border border-slate-800 font-mono"
                      >
                        {ch.replace("_", " ")}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
                <button
                  onClick={() => copyWebhook(t.id)}
                  className="text-xs text-slate-400 hover:text-indigo-400 flex items-center gap-1.5 transition font-mono"
                >
                  {copiedId === t.id ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied Ingest URL!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" /> Copy Channel Webhook
                    </>
                  )}
                </button>

                {/* Direct Launcher to manage client workspace on port 3000 */}
                <a
                  href={`http://localhost:3000/?tenant=${t.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition"
                >
                  Open Workspace <ArrowUpRight className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}