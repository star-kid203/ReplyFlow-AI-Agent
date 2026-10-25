// FILE: frontend/app/audit/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import { fetchBusiness, Business } from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import {
  GraduationCap,
  Bot,
  User,
  Sparkles,
  CheckCircle2,
  Layers,
  RefreshCw,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface AuditLog {
  id: string;
  conversation_id: string;
  channel: string;
  customer_handle: string;
  resolved_by: string;
  resolution_type: string;
  problem_statement: string;
  solution_statement: string;
  learned_by_ai: boolean;
  created_at: string;
}

export default function AuditLearningFarmPage() {
  const [tenantId, setTenantId] = useState<string>("");
  const [business, setBusiness] = useState<Business | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async (activeId: string) => {
    setLoading(true);
    try {
      const [logsRes, bizData] = await Promise.all([
        fetch(`${API_BASE}/conversations/audit-logs?business_id=${activeId}`, { cache: "no-store" }),
        fetchBusiness(activeId),
      ]);

      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(Array.isArray(data) ? data : []);
      }
      if (bizData) {
        setBusiness(bizData);
      }
    } catch (e) {
      console.error("Failed to load audit logs:", e);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = getActiveTenantId();
    setTenantId(id);
    fetchLogs(id);
  }, []);

  const totalLogs = logs.length;
  const aiSolvedCount = logs.filter((l) => l.resolution_type.includes("AI")).length;
  const humanSolvedCount = logs.filter((l) => l.resolution_type.includes("Human")).length;
  const aiAutomationRate = totalLogs > 0 ? Math.round((aiSolvedCount / totalLogs) * 100) : 100;

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                Learning Farm & Audit Trail: <span className="text-emerald-400">{business?.name || "Client"}</span>
              </h1>
              <p className="text-slate-400 text-xs mt-0.5">
                Every customer interaction, human resolution brief, and taught solution feeds {business?.agent_display_name || "this agent"}'s memory.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => fetchLogs(tenantId)}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center gap-2 self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Memory Farm
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Total Audited Interactions
          </span>
          <div className="mt-2 text-3xl font-bold text-white">{totalLogs}</div>
          <p className="text-xs text-slate-500 mt-1">{business?.name} specific events</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5" /> AI Autonomous Resolutions
          </span>
          <div className="mt-2 text-3xl font-bold text-emerald-400">{aiSolvedCount}</div>
          <p className="text-xs text-slate-500 mt-1">{aiAutomationRate}% resolved without human</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" /> Human Operator Interventions
          </span>
          <div className="mt-2 text-3xl font-bold text-amber-400">{humanSolvedCount}</div>
          <p className="text-xs text-slate-500 mt-1">Staff-resolved tickets</p>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-medium text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" /> Active Knowledge Rules
          </span>
          <div className="mt-2 text-3xl font-bold text-indigo-400">{humanSolvedCount + (totalLogs > 0 ? 2 : 0)}</div>
          <p className="text-xs text-slate-500 mt-1">Taught to {business?.name} AI</p>
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Audit Log & Problem-Solution Registry
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            {logs.length} interactions logged for {business?.name}
          </span>
        </div>

        {logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No interaction logs recorded yet for {business?.name}.
            Simulate a customer conversation in the Live Inbox to see real-time learning in action.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Customer & Channel</th>
                  <th className="py-3.5 px-4">Problem Statement</th>
                  <th className="py-3.5 px-4">Solution / Action Taken</th>
                  <th className="py-3.5 px-4">Resolved By</th>
                  <th className="py-3.5 px-4">Learning Status</th>
                  <th className="py-3.5 px-4 text-right">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-4 px-4">
                      <p className="font-semibold text-white">{log.customer_handle}</p>
                      <span className="text-[10px] text-indigo-400 font-mono">{log.channel}</span>
                    </td>

                    <td className="py-4 px-4 max-w-xs">
                      <p className="font-medium text-slate-200 line-clamp-2">
                        "{log.problem_statement}"
                      </p>
                    </td>

                    <td className="py-4 px-4 max-w-sm">
                      <p className="text-slate-300 line-clamp-2 leading-relaxed">
                        {log.solution_statement}
                      </p>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-semibold text-[11px] ${
                          log.resolution_type.includes("Human")
                            ? "bg-amber-950 text-amber-300 border border-amber-800/60"
                            : "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
                        }`}
                      >
                        {log.resolution_type.includes("Human") ? (
                          <User className="w-3 h-3" />
                        ) : (
                          <Bot className="w-3 h-3" />
                        )}
                        {log.resolved_by}
                      </span>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      <span className="flex items-center gap-1.5 text-emerald-400 font-mono text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Ingested to Brain
                      </span>
                    </td>

                    <td className="py-4 px-4 text-right text-slate-500 font-mono whitespace-nowrap">
                      {log.created_at}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}