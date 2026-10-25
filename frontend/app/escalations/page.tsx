// FILE: frontend/app/escalations/page.tsx
"use client";

import { useEffect, useState } from "react";
import { api, Conversation, fetchBusiness, Business } from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import { AlertOctagon, RefreshCw, MessageSquare, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export default function EscalationsPage() {
  const [tenantId, setTenantId] = useState<string>("");
  const [business, setBusiness] = useState<Business | null>(null);
  const [escalations, setEscalations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  const loadEscalations = async (activeId: string) => {
    setLoading(true);
    try {
      const [allConvs, bizData] = await Promise.all([
        api.listConversations(activeId),
        fetchBusiness(activeId),
      ]);
      setEscalations(allConvs.filter((c) => c.status === "escalated"));
      if (bizData) setBusiness(bizData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = getActiveTenantId();
    setTenantId(id);
    loadEscalations(id);
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center">
            <AlertOctagon className="w-6 h-6 mr-2.5 text-rose-400" />
            Urgent Human Escalations: <span className="text-rose-400 ml-2">{business?.name || "Client"}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Active tickets for {business?.name} where the AI agent paused to allow human specialist takeover.
          </p>
        </div>
        <button
          onClick={() => loadEscalations(tenantId)}
          className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
          title="Refresh Queue"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {escalations.length === 0 ? (
        <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/40">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No active escalations</h3>
          <p className="text-xs text-slate-400 mt-1">
            All customer threads for {business?.name} are currently resolved or operating autonomously.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {escalations.map((conv) => {
            const lastMsg = conv.messages?.[conv.messages.length - 1]?.content || "No messages";
            // @ts-ignore
            const summary = conv.handoff_summary?.problem || lastMsg;
            // @ts-ignore
            const resolution = conv.handoff_summary?.expected_resolution || "Customer requested live operator assistance.";

            return (
              <div
                key={conv.id}
                className="p-6 border border-rose-900/40 rounded-2xl bg-rose-950/20 flex flex-col md:flex-row md:items-center justify-between gap-5 hover:border-rose-800/60 transition"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-900 text-rose-300 font-mono uppercase tracking-wider">
                      {conv.channel.replace("_", " ")}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Thread #{conv.id.slice(0, 8)}
                    </span>
                    <span className="text-[10px] bg-rose-950 border border-rose-800 text-rose-400 px-2 py-0.5 rounded font-semibold">
                      AI Paused
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-white">Customer Issue:</h3>
                    <p className="text-sm font-medium text-rose-200 mt-0.5">"{summary}"</p>
                  </div>

                  <p className="text-xs text-slate-400">
                    <strong>Expected Goal:</strong> {resolution}
                  </p>
                </div>

                <Link
                  href={`/inbox?tenant=${tenantId}`}
                  className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shrink-0 transition shadow-lg shadow-rose-950/30"
                >
                  <MessageSquare className="w-4 h-4" /> Open Chat & Take Over
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}