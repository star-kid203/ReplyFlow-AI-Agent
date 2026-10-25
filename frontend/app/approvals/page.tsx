// FILE: frontend/app/approvals/page.tsx
"use client";

import { useEffect, useState } from "react";
import { api, AgentAction, fetchBusiness, Business } from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import { ShieldCheck, Check, X, RefreshCw } from "lucide-react";

export default function ApprovalsPage() {
  const [tenantId, setTenantId] = useState<string>("");
  const [business, setBusiness] = useState<Business | null>(null);
  const [approvals, setApprovals] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);

  const loadApprovals = async (activeId: string) => {
    setLoading(true);
    try {
      const [data, bizData] = await Promise.all([
        api.listPendingApprovals(activeId),
        fetchBusiness(activeId),
      ]);
      setApprovals(data || []);
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
    loadApprovals(id);
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await api.approveAction(id, "Manager Alex");
      await loadApprovals(tenantId);
    } catch (err) {
      alert("Approval failed.");
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt("Enter reason for rejection:") || "Policy mismatch";
    try {
      await api.rejectAction(id, "Manager Alex", reason);
      await loadApprovals(tenantId);
    } catch (err) {
      alert("Rejection failed.");
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center">
            <ShieldCheck className="w-6 h-6 mr-2.5 text-amber-400" />
            Human-in-the-Loop Approvals: <span className="text-amber-400 ml-2">{business?.name || "Client"}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review proposed actions (refunds, discounts, contract exceptions) for this organization before execution.
          </p>
        </div>

        <button
          onClick={() => loadApprovals(tenantId)}
          className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition"
          title="Refresh Queue"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {approvals.length === 0 ? (
        <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/40">
          <Check className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">All clear!</h3>
          <p className="text-xs text-slate-400 mt-1">
            No pending agent actions require human sign-off for {business?.name}.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((act) => (
            <div
              key={act.id}
              className="p-5 border border-slate-800 rounded-2xl bg-slate-900/70 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800/60 font-mono">
                    {act.action_type}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">ID: {act.id.slice(0, 8)}</span>
                </div>
                <p className="text-sm text-white font-medium">{act.reasoning}</p>
                <div className="text-xs text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono">
                  {JSON.stringify(act.payload, null, 2)}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleApprove(act.id)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>
                <button
                  onClick={() => handleReject(act.id)}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <X className="w-3.5 h-3.5" /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}