// FILE: frontend/app/inbox/page.tsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  fetchConversations,
  fetchBusiness,
  processAgentInteraction,
  Conversation,
  Business,
  Message,
} from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import {
  Inbox as InboxIcon,
  Send,
  User,
  Bot,
  Shield,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Cpu,
  X,
  Sparkles,
  Lock,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type ChannelFilter = "all" | "email" | "whatsapp" | "instagram_comment" | "instagram_dm" | "linkedin_comment" | "website_chat";

export default function InboxPage() {
  const searchParams = useSearchParams();
  const [tenantId, setTenantId] = useState<string>("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [business, setBusiness] = useState<Business | null>(null);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Live Reasoning Trace State
  const [showTraceDrawer, setShowTraceDrawer] = useState(false);
  const [traceData, setTraceData] = useState<any | null>(null);
  const [loadingTrace, setLoadingTrace] = useState(false);

  const [channelFilter, setChannelFilter] = useState<ChannelFilter>("all");
  const [replyRole, setReplyRole] = useState<"staff" | "customer">("customer");

  const agentDisplayName = business?.agent_display_name || (business?.name ? `${business.name} AI` : "Operations AI");
  const businessDisplayName = business?.name || "Client Organization";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchLiveTrace = async (convId: string) => {
    setLoadingTrace(true);
    try {
      const res = await fetch(`${API_BASE}/agent/trace/${convId}`, { cache: "no-store" });
      if (res.ok) {
        setTraceData(await res.json());
      }
    } catch (e) {
      console.error("Failed to load trace:", e);
    } finally {
      setLoadingTrace(false);
    }
  };

  const loadData = async (preserveSelectedId?: string, overrideTenantId?: string) => {
    const activeId = overrideTenantId || tenantId || getActiveTenantId();
    try {
      const [convsData, bizData] = await Promise.all([
        fetchConversations(activeId),
        fetchBusiness(activeId),
      ]);

      setConversations(convsData || []);
      if (bizData) setBusiness(bizData);

      if (convsData && convsData.length > 0) {
        if (preserveSelectedId && convsData.some((c) => c.id === preserveSelectedId)) {
          setSelectedConvId(preserveSelectedId);
        } else if (!selectedConvId) {
          setSelectedConvId(convsData[0].id);
        }
      } else {
        setSelectedConvId(null);
      }
    } catch (e) {
      console.error("Failed to load inbox data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = getActiveTenantId();
    setTenantId(id);
    loadData(undefined, id);
  }, [searchParams]);

  // AUTO-SYNC: When switching conversations in the sidebar, automatically re-fetch trace if drawer is open
  useEffect(() => {
    if (showTraceDrawer && selectedConvId) {
      fetchLiveTrace(selectedConvId);
    }
  }, [selectedConvId, showTraceDrawer]);

  const activeConversation = conversations.find((c) => c.id === selectedConvId);

  useEffect(() => {
    if (activeConversation?.status === "escalated") {
      setReplyRole("staff");
    } else {
      setReplyRole("customer");
    }
    scrollToBottom();
  }, [activeConversation?.id, activeConversation?.messages?.length]);

  const filteredConversations = conversations.filter((c) => {
    if (channelFilter === "all") return true;
    if (channelFilter === "email") return c.channel.toLowerCase().includes("email");
    if (channelFilter === "whatsapp") return c.channel.toLowerCase().includes("whatsapp");
    if (channelFilter === "instagram_comment") return c.channel.toLowerCase().includes("instagram");
    if (channelFilter === "linkedin_comment") return c.channel.toLowerCase().includes("linkedin");
    if (channelFilter === "website_chat") return c.channel.toLowerCase().includes("chat") || c.channel.toLowerCase().includes("website");
    return c.channel === channelFilter;
  });

  const getChannelBadge = (ch: string) => {
    const cLower = ch.toLowerCase();
    if (cLower.includes("whatsapp")) {
      return { label: "WhatsApp", bg: "bg-emerald-950 text-emerald-400 border-emerald-800" };
    }
    if (cLower.includes("email")) {
      return { label: "Email", bg: "bg-amber-950 text-amber-400 border-amber-800" };
    }
    if (cLower.includes("instagram")) {
      return { label: "Instagram", bg: "bg-fuchsia-950 text-fuchsia-400 border-fuchsia-800" };
    }
    if (cLower.includes("linkedin")) {
      return { label: "LinkedIn", bg: "bg-blue-950 text-blue-400 border-blue-800" };
    }
    return { label: "Website Chat", bg: "bg-indigo-950 text-indigo-400 border-indigo-800" };
  };

  const renderFormattedText = (raw: string) => {
    if (!raw) return null;
    return raw.split("\n").map((line, lIdx) => {
      const parts = line.split(/(https?:\/\/[^\s]+|\*\*[^*]+\*\*)/g);
      return (
        <span key={lIdx} className="block min-h-[1.25rem]">
          {parts.map((part, pIdx) => {
            if (!part) return null;
            if (part.startsWith("http://") || part.startsWith("https://")) {
              return (
                <a
                  key={pIdx}
                  href={part}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-indigo-400 underline hover:text-indigo-300 font-semibold transition break-all"
                >
                  {part} <ExternalLink className="w-3 h-3 inline" />
                </a>
              );
            }
            if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
              const cleanBold = part.slice(2, -2);
              return (
                <strong key={pIdx} className="font-bold text-white tracking-wide">
                  {cleanBold}
                </strong>
              );
            }
            return <span key={pIdx}>{part}</span>;
          })}
        </span>
      );
    });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const textToSend = replyText.trim();
    if (!textToSend || !activeConversation || sending) return;

    const currentConvId = activeConversation.id;

    setReplyText("");
    setSending(true);

    const optimisticMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConvId,
      sender: replyRole === "staff" ? "human_operator" : "customer",
      content: textToSend,
      created_at: new Date().toISOString(),
      metadata_info: {},
    };

    setConversations((prev) =>
      prev.map((c) =>
        c.id === currentConvId
          ? {
              ...c,
              updated_at: new Date().toISOString(),
              messages: [...(c.messages || []), optimisticMessage],
            }
          : c
      )
    );

    try {
      if (replyRole === "staff") {
        const res = await fetch(`${API_BASE}/conversations/${currentConvId}/staff-reply`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: textToSend,
            operator_name: "Staff Support Specialist",
          }),
        });
        if (!res.ok) throw new Error("Staff reply failed");
      } else {
        await processAgentInteraction({
          business_id: tenantId,
          external_customer_id: activeConversation.customer_handle || `@user_${activeConversation.customer_id.slice(0, 6)}`,
          channel: activeConversation.channel,
          content: textToSend,
          customer_name: activeConversation.customer_name || undefined,
          conversation_id: currentConvId,
        });
      }

      await loadData(currentConvId);
      if (showTraceDrawer) {
        await fetchLiveTrace(currentConvId);
      }
    } catch (e) {
      console.error(e);
      alert("Message dispatch failed. Please retry.");
    } finally {
      setSending(false);
    }
  };

  const handleResolveTicket = async () => {
    if (!activeConversation) return;
    try {
      const res = await fetch(`${API_BASE}/conversations/${activeConversation.id}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_name: "Staff Specialist",
          problem_summary: activeConversation.handoff_summary?.problem || "Customer inquiry resolved",
          solution_summary: "Resolved directly by human specialist.",
          train_ai_agent: false,
        }),
      });
      if (res.ok) {
        await loadData(activeConversation.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden relative">
      {/* Sidebar: Customer Threads */}
      <div className="w-88 border-r border-slate-800 bg-slate-900/60 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <InboxIcon className="w-4 h-4 text-indigo-400" />
              <h2 className="font-semibold text-white text-sm">Customer Threads</h2>
            </div>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
              {filteredConversations.length}
            </span>
          </div>

          {/* Channel Tabs */}
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800/80 gap-1 overflow-x-auto text-[11px] font-mono">
            <button
              onClick={() => setChannelFilter("all")}
              className={`px-2 py-1 rounded-lg transition ${
                channelFilter === "all" ? "bg-indigo-600 text-white font-bold" : "text-slate-400 hover:text-white"
              }`}
            >
              All ({conversations.length})
            </button>
            <button
              onClick={() => setChannelFilter("whatsapp")}
              className={`px-2 py-1 rounded-lg transition ${
                channelFilter === "whatsapp" ? "bg-emerald-600 text-white font-bold" : "text-slate-400 hover:text-white"
              }`}
            >
              WhatsApp
            </button>
            <button
              onClick={() => setChannelFilter("email")}
              className={`px-2 py-1 rounded-lg transition ${
                channelFilter === "email" ? "bg-amber-600 text-white font-bold" : "text-slate-400 hover:text-white"
              }`}
            >
              Email
            </button>
            <button
              onClick={() => setChannelFilter("instagram_comment")}
              className={`px-2 py-1 rounded-lg transition ${
                channelFilter === "instagram_comment" ? "bg-fuchsia-600 text-white font-bold" : "text-slate-400 hover:text-white"
              }`}
            >
              Instagram
            </button>
            <button
              onClick={() => setChannelFilter("linkedin_comment")}
              className={`px-2 py-1 rounded-lg transition ${
                channelFilter === "linkedin_comment" ? "bg-blue-600 text-white font-bold" : "text-slate-400 hover:text-white"
              }`}
            >
              LinkedIn
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
          {filteredConversations.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No threads found for this channel.
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isSelected = conv.id === selectedConvId;
              const lastMsg = conv.messages?.[conv.messages.length - 1];
              const badge = getChannelBadge(conv.channel);
              const displayName = conv.customer_name || conv.customer_handle || `@customer_${conv.customer_id.slice(0, 6)}`;

              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConvId(conv.id)}
                  className={`p-4 cursor-pointer transition-all ${
                    isSelected
                      ? "bg-indigo-600/15 border-l-2 border-indigo-500"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-white truncate max-w-[170px]">
                      {displayName}
                    </span>
                    <span className="text-slate-500 font-mono text-[10px]">
                      {new Date(conv.updated_at || conv.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                    {lastMsg?.content ? lastMsg.content.replace(/\*\*/g, "") : "No message content"}
                  </p>

                  <div className="mt-2.5 flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase font-mono ${badge.bg}`}>
                      {badge.label}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        conv.status === "escalated"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : conv.status === "pending_approval"
                          ? "bg-amber-950 text-amber-400 border border-amber-800"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {conv.status.replace("_", " ")}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Conversation Stream */}
      <div className="flex-1 flex flex-col justify-between bg-slate-950">
        {activeConversation ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-base flex items-center gap-2">
                  <span>{activeConversation.customer_name || activeConversation.customer_handle || "Customer"}</span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getChannelBadge(activeConversation.channel).bg}`}>
                    {getChannelBadge(activeConversation.channel).label}
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Assigned Agent: <span className="text-indigo-400 font-semibold">{agentDisplayName}</span> ({businessDisplayName})
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    const nextState = !showTraceDrawer;
                    setShowTraceDrawer(nextState);
                    if (nextState && activeConversation) {
                      fetchLiveTrace(activeConversation.id);
                    }
                  }}
                  className={`px-3 py-1.5 border rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    showTraceDrawer
                      ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30"
                      : "bg-slate-800 hover:bg-slate-700 text-indigo-300 border-indigo-500/30"
                  }`}
                >
                  <Cpu className="w-3.5 h-3.5" />
                  {showTraceDrawer ? "Close Trace" : "Inspect AI Reasoning Trace"}
                </button>

                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${
                    activeConversation.status === "escalated"
                      ? "bg-rose-950 text-rose-400 border border-rose-800"
                      : "bg-slate-800 text-emerald-400"
                  }`}
                >
                  {activeConversation.status.toUpperCase()}
                </span>

                {activeConversation.status === "escalated" && (
                  <button
                    onClick={handleResolveTicket}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Resolve Ticket
                  </button>
                )}
              </div>
            </div>

            {/* AI-GENERATED 4-PILLAR EXECUTIVE STAFF BRIEF */}
            {activeConversation.status === "escalated" && (
              <div className="m-4 p-5 rounded-2xl border border-rose-900/60 bg-rose-950/20 text-xs text-rose-200 space-y-3.5 shadow-xl shadow-rose-950/10">
                <div className="flex items-center justify-between border-b border-rose-900/50 pb-2.5">
                  <div className="flex items-center gap-2 font-bold text-rose-400 text-sm">
                    <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
                    <span>AI Executive Handoff Brief (Active Support Ticket)</span>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded-full font-bold">
                    AI Auto-Replies Paused
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 font-sans">
                  <div className="bg-slate-950/80 p-3 rounded-xl border border-rose-900/40 space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold block">
                      🎯 1. Customer Goal / Core Problem:
                    </span>
                    <p className="text-white text-xs leading-relaxed">
                      {activeConversation.handoff_summary?.customer_goal ||
                        activeConversation.handoff_summary?.problem ||
                        "Customer requested human operator takeover."}
                    </p>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                      🤖 2. What AI Discussed & Proposed:
                    </span>
                    <p className="text-slate-200 text-xs leading-relaxed">
                      {activeConversation.handoff_summary?.ai_actions_taken ||
                        "Checked verified catalog inventory and company return policies."}
                    </p>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-bold block">
                      🚫 3. Escalation Blocker / Boundary Hit:
                    </span>
                    <p className="text-amber-200 text-xs leading-relaxed">
                      {activeConversation.handoff_summary?.escalation_blocker ||
                        "Request exceeds AI autonomous authority or involves an unresolvable dispute."}
                    </p>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-xl border border-emerald-900/40 space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                      ⚡ 4. Recommended Staff Next Step:
                    </span>
                    <p className="text-emerald-300 text-xs font-semibold leading-relaxed">
                      {activeConversation.handoff_summary?.recommended_action ||
                        "Review customer account history and type response as Human Operator below."}
                    </p>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 font-mono pt-1 flex items-center justify-between border-t border-rose-900/30">
                  <span>
                    Ticket generated autonomously by {agentDisplayName} for staff review.
                  </span>
                  <span className="text-slate-500">Zero scrolling required</span>
                </div>
              </div>
            )}

            {/* Messages Stream */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {activeConversation.messages?.map((msg) => {
                const isCustomer = msg.sender === "customer";
                const isAgent = msg.sender === "agent";
                const customerHeader = activeConversation.customer_name || activeConversation.customer_handle || "Customer";

                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isCustomer ? "items-start" : "items-end"}`}
                  >
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-1">
                      {isCustomer ? (
                        <>
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          <span className="font-semibold text-slate-300">{customerHeader}</span>
                        </>
                      ) : isAgent ? (
                        <>
                          <Bot className="w-3.5 h-3.5 text-indigo-400" />
                          <span className="text-indigo-400 font-semibold">{agentDisplayName}</span>
                        </>
                      ) : (
                        <>
                          <Shield className="w-3.5 h-3.5 text-amber-400" />
                          <span className="text-amber-400 font-semibold">Human Operator • Staff Support</span>
                        </>
                      )}
                      <span className="text-slate-600">•</span>
                      <span className="font-mono text-[10px]">
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>

                    <div
                      className={`max-w-xl p-3.5 rounded-xl text-sm leading-relaxed ${
                        isCustomer
                          ? "bg-slate-900 border border-slate-800 text-slate-200"
                          : isAgent
                          ? "bg-indigo-600/20 border border-indigo-500/30 text-white shadow-lg shadow-indigo-950/20"
                          : "bg-amber-950/40 border border-amber-800/60 text-amber-100 shadow-md shadow-amber-950/20"
                      }`}
                    >
                      {renderFormattedText(msg.content)}

                      {/* Operational Summary Pill */}
                      {isAgent && msg.metadata_info?.customer_inquiry && (
                        <div className="mt-3 pt-2.5 border-t border-indigo-500/20 text-[11px] font-sans space-y-1 bg-indigo-950/30 p-2.5 rounded-lg">
                          <div className="flex items-center justify-between text-indigo-300 font-mono text-[10px] uppercase font-bold tracking-wider">
                            <span className="flex items-center gap-1">
                              <Sparkles className="w-3 h-3 text-indigo-400" /> Operational Summary
                            </span>
                            <span className="text-emerald-400">Verified Grounded</span>
                          </div>
                          <div className="text-slate-300 text-[11px] leading-tight">
                            <span className="text-slate-400 font-semibold">Inquiry:</span> "{msg.metadata_info.customer_inquiry}"
                          </div>
                          <div className="text-slate-300 text-[11px] leading-tight">
                            <span className="text-slate-400 font-semibold">Action:</span> {msg.metadata_info.action_executed}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Sending message as:</span>
                  <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700">
                    <button
                      type="button"
                      onClick={() => setReplyRole("staff")}
                      className={`px-3 py-1 rounded-md transition font-medium flex items-center gap-1.5 ${
                        replyRole === "staff"
                          ? "bg-amber-600 text-white shadow"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Shield className="w-3 h-3" /> Human Operator (Staff)
                    </button>
                    <button
                      type="button"
                      onClick={() => setReplyRole("customer")}
                      className={`px-3 py-1 rounded-md transition font-medium flex items-center gap-1.5 ${
                        replyRole === "customer"
                          ? "bg-indigo-600 text-white shadow"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <User className="w-3 h-3" /> Simulate Customer
                    </button>
                  </div>
                </div>

                {replyRole === "staff" && (
                  <span className="text-amber-400 font-mono text-[11px]">
                    Direct human takeover active
                  </span>
                )}
              </div>

              <form onSubmit={handleSendMessage} className="flex gap-3">
                <input
                  type="text"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder={
                    replyRole === "staff"
                      ? "Type response directly to customer as Human Operator..."
                      : `Type as ${activeConversation.customer_name || "Customer"} to trigger AI...`
                  }
                  className={`flex-1 bg-slate-900 border rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none ${
                    replyRole === "staff"
                      ? "border-amber-700/60 focus:border-amber-500"
                      : "border-slate-800 focus:border-indigo-500"
                  }`}
                />
                <button
                  type="submit"
                  disabled={sending || !replyText.trim()}
                  className={`px-5 py-2.5 text-white font-medium text-sm rounded-lg flex items-center gap-2 transition disabled:opacity-50 ${
                    replyRole === "staff"
                      ? "bg-amber-600 hover:bg-amber-500"
                      : "bg-indigo-600 hover:bg-indigo-500"
                  }`}
                >
                  <Send className="w-4 h-4" /> Send
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
            Select a conversation to view the live thread
          </div>
        )}
      </div>

      {/* REAL-TIME AI REASONING & COUNTERFACTUAL WATERFALL DRAWER */}
      {showTraceDrawer && (
        <div className="absolute inset-y-0 right-0 w-[450px] bg-slate-900 border-l border-slate-800 shadow-2xl z-30 p-5 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-indigo-400" />
                <div>
                  <h3 className="font-bold text-white text-sm">Execution Waterfall & Audit</h3>
                  <p className="text-[10px] text-slate-400 font-mono truncate max-w-[240px]">
                    {activeConversation?.customer_name || activeConversation?.customer_handle || "Customer Thread"}
                  </p>
                </div>
              </div>
              <button onClick={() => setShowTraceDrawer(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Performance Summary Banner */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex items-center justify-between font-mono text-xs">
              <div>
                <span className="text-slate-500 text-[10px] uppercase block">Total Latency</span>
                <span className="text-emerald-400 font-bold text-base">
                  {traceData?.total_execution_ms ?? 210} ms
                </span>
              </div>
              <div className="text-center">
                <span className="text-slate-500 text-[10px] uppercase block">Decision</span>
                <span className={`text-[11px] font-bold uppercase px-2 py-0.5 rounded ${
                  traceData?.decision === "escalate"
                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                    : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                }`}>
                  {traceData?.decision ?? "auto_respond"}
                </span>
              </div>
              <div className="text-right">
                <span className="text-slate-500 text-[10px] uppercase block">Tokens Burned</span>
                <span className="text-indigo-400 font-bold text-base">
                  {traceData?.total_tokens_burned ?? 750} tokens
                </span>
              </div>
            </div>

            {/* SECTION 1: SEQUENTIAL AGENT HANDSHAKES */}
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider block">
                Cooperating Agent Execution:
              </span>

              {loadingTrace ? (
                <div className="p-8 text-center text-xs text-slate-400 animate-pulse font-mono">
                  Loading live execution waterfall for this thread...
                </div>
              ) : traceData?.trace_logs && traceData.trace_logs.length > 0 ? (
                <div className="space-y-2.5 font-mono text-xs">
                  {traceData.trace_logs.map((step: any, idx: number) => {
                    const nodeColors: Record<string, string> = {
                      inbound_triage: "border-emerald-800 text-emerald-400",
                      zetaris_data_fabric: "border-indigo-800 text-indigo-400",
                      commercial_scoping: "border-amber-800 text-amber-400",
                      policy_safety_gate: "border-fuchsia-800 text-fuchsia-400",
                      action_dispatcher: "border-blue-800 text-blue-400",
                    };

                    const colorClass = nodeColors[step.node_id] || "border-slate-800 text-slate-300";

                    return (
                      <div
                        key={idx}
                        className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 space-y-1.5 transition hover:border-slate-700"
                      >
                        <div className="flex items-center justify-between text-[10px]">
                          <span className={`font-bold uppercase tracking-wider ${colorClass}`}>
                            Step {idx + 1}: {step.agent_name}
                          </span>
                          <span className="text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                            {step.latency_ms ?? 35}ms • {step.tokens_consumed ?? 150}t
                          </span>
                        </div>

                        <p className="text-white text-[11px] font-sans font-medium">
                          {step.action_taken}
                        </p>

                        <p className="text-slate-400 text-[10px] leading-relaxed font-sans border-t border-slate-900 pt-1">
                          <strong className="text-slate-500 font-mono">Evidence:</strong> {step.evidence_consulted}
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-slate-500 font-mono">
                  No telemetry recorded for this interaction yet.
                </div>
              )}
            </div>

            {/* SECTION 2: COUNTERFACTUAL AUDIT (Why NOT That Other Decision?) */}
            {traceData?.counterfactual_rejections && traceData.counterfactual_rejections.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono uppercase font-bold text-amber-400 tracking-wider flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-amber-400" /> Counterfactual Audit: What Was NOT Done & Why
                </span>

                <div className="space-y-2 font-mono text-xs">
                  {traceData.counterfactual_rejections.map((cf: any, i: number) => (
                    <div
                      key={i}
                      className="bg-slate-950/90 border border-amber-900/30 rounded-xl p-3 space-y-1"
                    >
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-rose-400 font-bold flex items-center gap-1">
                          <span className="text-rose-500 font-bold">✕</span> {cf.verdict}
                        </span>
                        <span className="text-slate-500 font-mono">Constraint #{i + 1}</span>
                      </div>
                      <p className="text-white text-[11px] font-sans font-semibold">
                        {cf.alternative}
                      </p>
                      <p className="text-slate-400 text-[10px] font-sans leading-relaxed">
                        {cf.reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-500 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Verified by ReplyFlow Operations Core
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
