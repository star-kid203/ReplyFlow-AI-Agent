// FILE: frontend/app/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import {
  fetchConversations,
  fetchPendingApprovals,
  fetchProducts,
  fetchBusiness,
  processAgentInteraction,
  Conversation,
  PendingApproval,
  Product,
  Business,
} from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
  Briefcase,
  ShoppingBag,
  Package,
  Layers,
} from "lucide-react";

// AFTER (correct TypeScript):
interface LiveUsage {
  plan_tier: string;
  plan_display_name: string;
  monthly_price_usd: number;
  responses_used: number;
  responses_limit: number;
  comments_used: number;
  comments_limit: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DashboardPage() {
  const [tenantId, setTenantId] = useState<string>("");
  const [business, setBusiness] = useState<Business | null>(null);
  const [usage, setUsage] = useState<LiveUsage | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulator
  const [inputMessage, setInputMessage] = useState("What services does your firm provide?");
  const [channel, setChannel] = useState("linkedin_comment");
  const [handle, setHandle] = useState("@director_lead");
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  const loadData = async (activeId: string) => {
    setLoading(true);
    try {
      const [cData, aData, pData, bData, uRes] = await Promise.all([
        fetchConversations(activeId),
        fetchPendingApprovals(activeId),
        fetchProducts(activeId),
        fetchBusiness(activeId),
        fetch(`${API_BASE}/packages/tenant/${activeId}/usage`, { cache: "no-store" }).catch(() => null),
      ]);
      setConversations(Array.isArray(cData) ? cData : []);
      setApprovals(Array.isArray(aData) ? aData : []);
      setProducts(Array.isArray(pData) ? pData : []);
      if (bData) setBusiness(bData);
      if (uRes && uRes.ok) setUsage(await uRes.json());
    } catch (e) {
      console.error("Dashboard load failed:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = getActiveTenantId();
    setTenantId(id);
    loadData(id);
  }, []);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !tenantId) return;

    setSimulating(true);
    try {
      const result = await processAgentInteraction({
        business_id: tenantId,
        external_customer_id: handle,
        channel: channel,
        content: inputMessage,
        customer_name: handle.replace("@", ""),
      });
      setSimResult(result);
      await loadData(tenantId);
    } catch (err) {
      alert("Simulation failed.");
    } finally {
      setSimulating(false);
    }
  };

  const isServiceBusiness =
    business?.description?.toLowerCase().includes("consulting") ||
    business?.description?.toLowerCase().includes("software") ||
    business?.description?.toLowerCase().includes("it") ||
    business?.description?.toLowerCase().includes("solutions");

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            {business?.name || "Client Workspace"}
            <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 font-bold">
              {usage?.plan_display_name || business?.plan_tier || "Business"} Plan
            </span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            {business?.description || "Customer operations workspace"}
          </p>
        </div>

        <button
          onClick={() => loadData(tenantId)}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
        >
          Refresh Data
        </button>
      </div>

      {/* Quota & Operational Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
            <Package className="w-3.5 h-3.5 text-amber-400" /> Plan Responses Used
          </span>
          <div className="mt-2 text-3xl font-bold text-white">
            {usage?.responses_used ?? 0}
            <span className="text-xs text-slate-500 font-normal"> / {(usage?.responses_limit ?? 25000).toLocaleString()}</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Monthly AI reply quota</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-indigo-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
            <MessageSquare className="w-3.5 h-3.5" /> Comments Processed
          </span>
          <div className="mt-2 text-3xl font-bold text-indigo-400">
            {usage?.comments_used ?? 0}
            <span className="text-xs text-slate-500 font-normal"> / {(usage?.comments_limit ?? 10000).toLocaleString()}</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">LinkedIn & social comments</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider font-mono">Auto-Resolved</span>
          <div className="mt-2 text-3xl font-bold text-emerald-400">
            {conversations.filter((c) => c.status === "open").length}
          </div>
          <p className="text-xs text-slate-500 mt-1">Grounded without human</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-rose-400 uppercase tracking-wider font-mono">Escalated Tickets</span>
          <div className="mt-2 text-3xl font-bold text-rose-400">
            {conversations.filter((c) => c.status === "escalated").length}
          </div>
          <p className="text-xs text-slate-500 mt-1">Handed over to staff</p>
        </div>
      </div>

      {/* Simulator + Ground Truth Portfolio */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" /> Interactive Interaction Simulator
          </h2>

          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 font-semibold">User Handle</label>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold">Channel</label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white"
                >
                  <option value="linkedin_comment">LinkedIn Comment</option>
                  <option value="youtube_comment">YouTube Comment</option>
                  <option value="website_chat">Website Chat</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 font-semibold">Customer Message</label>
              <textarea
                rows={3}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white"
              />
            </div>

            <button
              type="submit"
              disabled={simulating}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition"
            >
              {simulating ? "Executing AI State Machine..." : "Run Interaction Test"}
            </button>
          </form>

          {simResult && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between font-mono">
                <span className="text-slate-400">Decision:</span>
                <span className="text-emerald-400 font-bold uppercase">{simResult.decision}</span>
              </div>
              <p className="text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800 font-sans">
                {simResult.response_text}
              </p>
            </div>
          )}
        </div>

        {/* Real Ground Truth Offerings */}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            {isServiceBusiness ? <Briefcase className="w-5 h-5 text-indigo-400" /> : <ShoppingBag className="w-5 h-5 text-emerald-400" />}
            {isServiceBusiness ? "Verified Solutions & Offerings" : "Verified Catalog"}
          </h2>

          {products.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs border border-slate-800 rounded-xl bg-slate-950">
              No offerings added yet. Use the Business Brain tab to add verified services or crawl official website pages.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {products.map((p) => (
                <div
                  key={p.id}
                  className="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between text-xs"
                >
                  <div>
                    <p className="font-semibold text-white">{p.name}</p>
                    <p className="text-[11px] text-slate-400 font-mono">{p.sku}</p>
                  </div>
                  <span className="font-bold text-slate-200">
                    {p.price === "0.00" || p.price === 0 ? "Custom Quote" : `$${p.price}`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}