"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { fetchBusiness, Business } from "@/lib/api";
import { getActiveTenantId } from "@/lib/tenant";
import {
  Sparkles,
  Play,
  Sliders,
  MessageSquare,
  RotateCcw,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface TriageResult {
  comment_id: string;
  author_handle: string;
  content: string;
  action_taken: string;
  reason: string;
  reply_text?: string;
}

export default function SocialCampaignSimulatorPage() {
  const searchParams = useSearchParams();
  const [tenantId, setTenantId] = useState<string>("");
  const [business, setBusiness] = useState<Business | null>(null);

  // Campaign Directive Parameters
  const [platform, setPlatform] = useState<string>("linkedin_comment");
  const [postCaption, setPostCaption] = useState<string>("");
  const [postUrl, setPostUrl] = useState<string>("https://linkedin.com/feed/update/urn:li:activity:98471928");
  const [persona, setPersona] = useState<string>("");
  const [commentsJson, setCommentsJson] = useState<string>("");
  const [dailyCap, setDailyCap] = useState(50);

  // 5 Authorized Engagement Rules (Checked = Allowed to Reply | Unchecked = Muted / Dropped)
  const [allowPraise, setAllowPraise] = useState(false); // Default: false (drops hype at 0 tokens)
  const [allowLeads, setAllowLeads] = useState(true);
  const [allowCriticism, setAllowCriticism] = useState(true);
  const [allowGrievances, setAllowGrievances] = useState(true);
  const [allowPartnerships, setAllowPartnerships] = useState(true);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<TriageResult[]>([]);

  // Auto-sync Post URL when changing Target Platform
  const handlePlatformChange = (newPlatform: string) => {
    setPlatform(newPlatform);
    if (newPlatform === "youtube_comment") {
      setPostUrl("https://youtube.com/watch?v=demo_preview_984");
    } else if (newPlatform === "instagram_comment") {
      setPostUrl("https://instagram.com/p/DBc891F0a9b");
    } else if (newPlatform === "facebook_comment") {
      setPostUrl("https://facebook.com/posts/1029384756");
    } else {
      setPostUrl("https://linkedin.com/feed/update/urn:li:activity:98471928");
    }
  };

  const loadTenantPresets = (biz: Business) => {
    setPersona(biz.communication_style || "professional, consultative, and concise");

    const isSoftwareOrService =
      biz.business_type === "service" ||
      biz.description?.toLowerCase().includes("software") ||
      biz.description?.toLowerCase().includes("consulting") ||
      biz.name.toLowerCase().includes("douatech");

    if (isSoftwareOrService) {
      setPlatform("linkedin_comment");
      setPostUrl("https://linkedin.com/feed/update/urn:li:activity:98471928");
      setPostCaption("Excited to launch our scalable digital enterprise architecture & telehealth suite for high-growth African enterprises! 🚀");
      setCommentsJson(
        JSON.stringify(
          [
            {
              comment_id: "c1",
              author_handle: "@dev_alex",
              content: "Fire release!! 🔥🔥🔥",
            },
            {
              comment_id: "c2",
              author_handle: "@cynical_cto",
              content: "Zero downtime? Yeah right, another enterprise marketing hype.",
            },
            {
              comment_id: "c3",
              author_handle: "@founder_sarah",
              content: "Can your firm build our clinic appointment mobile app? How do we start and what is the quote?",
            },
            {
              comment_id: "c4",
              author_handle: "@angry_client",
              content: "Our production portal has been unresponsive since 9 AM and ticket #892 is still pending!",
            },
            {
              comment_id: "c5",
              author_handle: "@b2b_reseller",
              content: "We run 3 electronics stores in Douala. Do you sell iPhone 17 and laptops in bulk?",
            },
          ],
          null,
          2
        )
      );
    } else {
      setPlatform("instagram_comment");
      setPostUrl("https://instagram.com/p/DBc891F0a9b");
      setPostCaption("New flagship inventory drop is live! Check our catalog for the latest laptops, smartphones, and audio gear with same-day dispatch.");
      setCommentsJson(
        JSON.stringify(
          [
            {
              comment_id: "c1",
              author_handle: "@fan_girl",
              content: "Love this so much!! 🔥",
            },
            {
              comment_id: "c2",
              author_handle: "@shopper_jack",
              content: "Do you have the iPhone 17 in black available today and where can I pick it up?",
            },
            {
              comment_id: "c3",
              author_handle: "@price_skeptic",
              content: "Way overpriced. These devices are definitely marked up too high.",
            },
            {
              comment_id: "c4",
              author_handle: "@upset_buyer",
              content: "My order was delayed by 3 days and arrived with broken packaging! I want a refund.",
            },
            {
              comment_id: "c5",
              author_handle: "@b2b_reseller",
              content: "We run 3 electronics stores in Douala. Do you offer wholesale bulk pricing for phone resellers?",
            },
          ],
          null,
          2
        )
      );
    }
  };

  useEffect(() => {
    const activeId = getActiveTenantId();
    setTenantId(activeId);

    fetchBusiness(activeId).then((biz) => {
      if (biz) {
        setBusiness(biz);
        loadTenantPresets(biz);
      }
    });
  }, [searchParams]);

  const handleExecuteDirective = async () => {
    setLoading(true);
    setResults([]);

    const targetIntents: string[] = [];
    if (allowPraise) targetIntents.push("praise", "hype");
    if (allowLeads) targetIntents.push("lead", "pricing", "product_inquiry");
    if (allowCriticism) targetIntents.push("criticism", "sarcasm");
    if (allowGrievances) targetIntents.push("complaint", "support");
    if (allowPartnerships) targetIntents.push("partnership", "api", "integration");

    try {
      const parsedComments = JSON.parse(commentsJson);
      const res = await fetch(`${API_BASE}/social/batch-ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_id: tenantId,
          channel: platform,
          directive: {
            post_id: postUrl,
            post_caption: postCaption,
            creator_persona: persona,
            target_intents: targetIntents,
            ignore_generic_praise: !allowPraise,
            daily_reply_cap: dailyCap,
          },
          comments: parsedComments,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
      } else {
        alert("Campaign directive execution failed.");
      }
    } catch (e: any) {
      alert("Invalid JSON format in comments: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case "skipped_noise":
        return {
          label: "Noise Filtered (0 Tokens)",
          style: "bg-slate-800 text-slate-400 border border-slate-700",
        };
      case "skipped_by_directive":
        return {
          label: "Muted by Governance Rule",
          style: "bg-amber-950/60 text-amber-400 border border-amber-800",
        };
      case "skipped_cap_exceeded":
        return {
          label: "Daily Cap Reached",
          style: "bg-rose-950 text-rose-300 border border-rose-800",
        };
      case "sent_private_dm":
        return {
          label: "Private Lead Handoff",
          style: "bg-indigo-950 text-indigo-300 border border-indigo-800",
        };
      case "partnership_engaged":
        return {
          label: "B2B Partnership Captured",
          style: "bg-sky-950 text-sky-300 border border-sky-800",
        };
      case "replied_publicly":
        return {
          label: "Public Brand Engagement",
          style: "bg-emerald-950 text-emerald-300 border border-emerald-800",
        };
      default:
        return {
          label: action.replace("_", " "),
          style: "bg-amber-950 text-amber-300 border border-amber-800",
        };
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            Social Campaign Directives: <span className="text-indigo-400">{business?.name || "Client"}</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Configure how the AI workforce monitors posts, filters noise at zero token cost, captures leads, and defends the brand.
          </p>
        </div>

        {business && (
          <button
            onClick={() => loadTenantPresets(business)}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition border border-slate-700 self-start md:self-auto"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset {business.name} Presets
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Form: Directive Control Panel */}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-400 font-mono flex items-center gap-2">
              <Sliders className="w-4 h-4" /> 5-Category Governance Panel
            </h2>
            <span className="text-[10px] text-emerald-400 font-mono font-bold">5 TIERS ACTIVE</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300">Target Platform</label>
              <select
                value={platform}
                onChange={(e) => handlePlatformChange(e.target.value)}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="linkedin_comment">LinkedIn Post Comments</option>
                <option value="youtube_comment">YouTube Video Comments</option>
                <option value="instagram_comment">Instagram Post Comments</option>
                <option value="facebook_comment">Facebook Page Comments</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300">Daily Reply Cap</label>
              <input
                type="number"
                value={dailyCap}
                onChange={(e) => setDailyCap(parseInt(e.target.value) || 50)}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300">Target Post URL / Activity URN</label>
            <input
              type="text"
              value={postUrl}
              onChange={(e) => setPostUrl(e.target.value)}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300">Post Caption / Video Context</label>
            <textarea
              rows={2}
              value={postCaption}
              onChange={(e) => setPostCaption(e.target.value)}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* 5 Authorized Engagement Rules (Unchecked = Muted / Dropped) */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 text-xs">
            <span className="text-[10px] uppercase font-mono font-bold text-amber-400 block tracking-wider">
              5 Authorized Engagement Categories:
            </span>

            {/* Rule 1: Noise / Hype */}
            <label className="flex items-start gap-2.5 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={allowPraise}
                onChange={(e) => setAllowPraise(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
              />
              <div>
                <span className="font-semibold text-white">1. Generic Hype & Fan Praise</span>
                <p className="text-[11px] text-slate-500">
                  {allowPraise
                    ? "Checked: AI generates polite thank-you replies."
                    : "Unchecked (Recommended): Drops emojis and hype at 0 token cost."}
                </p>
              </div>
            </label>

            {/* Rule 2: Commercial Leads */}
            <label className="flex items-start gap-2.5 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={allowLeads}
                onChange={(e) => setAllowLeads(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
              />
              <div>
                <span className="font-semibold text-white">2. Commercial Sales Inquiries</span>
                <p className="text-[11px] text-slate-500">Answers inquiries & provides 1-click WhatsApp/DM discovery bridge.</p>
              </div>
            </label>

            {/* Rule 3: Brand Sarcasm & Skepticism */}
            <label className="flex items-start gap-2.5 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={allowCriticism}
                onChange={(e) => setAllowCriticism(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
              />
              <div>
                <span className="font-semibold text-white">3. Brand Sarcasm & Skepticism</span>
                <p className="text-[11px] text-slate-500">Defends the brand with polite pride, verified facts, and confidence.</p>
              </div>
            </label>

            {/* Rule 4: Customer Support Grievances */}
            <label className="flex items-start gap-2.5 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={allowGrievances}
                onChange={(e) => setAllowGrievances(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
              />
              <div>
                <span className="font-semibold text-white">4. Customer Support & Grievances</span>
                <p className="text-[11px] text-slate-500">De-escalates publicly & provisions High-Priority Escalation in Live Inbox.</p>
              </div>
            </label>

            {/* Rule 5: Technical & B2B Partnerships */}
            <label className="flex items-start gap-2.5 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={allowPartnerships}
                onChange={(e) => setAllowPartnerships(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
              />
              <div>
                <span className="font-semibold text-white">5. Technical & B2B Partnerships</span>
                <p className="text-[11px] text-slate-500">Engages developers, agency integrations, and enterprise API inquiries.</p>
              </div>
            </label>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300">Batch Comments Stream (JSON Array)</label>
            <textarea
              rows={6}
              value={commentsJson}
              onChange={(e) => setCommentsJson(e.target.value)}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            onClick={handleExecuteDirective}
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
          >
            <Play className="w-4 h-4" /> {loading ? "Evaluating 5-Tier Pipeline..." : "Execute Campaign Directive"}
          </button>
        </div>

        {/* Right: Results Stream */}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider font-mono text-emerald-400 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Live Execution Feed
            </h2>
            <span className="text-xs text-slate-400 font-mono">{results.length} processed</span>
          </div>

          {results.length === 0 ? (
            <div className="p-16 text-center text-slate-500 text-xs space-y-2 border border-slate-800/60 rounded-xl bg-slate-950">
              <Sparkles className="w-8 h-8 text-indigo-400 mx-auto opacity-40" />
              <p className="font-semibold text-slate-300">Ready to execute campaign directives.</p>
              <p className="text-slate-500 max-w-sm mx-auto">
                Click 'Execute Campaign Directive' to test how the agent drops noise, captures leads, de-escalates grievances, and enforces domain boundaries.
              </p>
            </div>
          ) : (
            <div className="space-y-3.5 max-h-[700px] overflow-y-auto pr-1">
              {results.map((res) => {
                const badge = getActionBadge(res.action_taken);

                return (
                  <div
                    key={res.comment_id}
                    className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl space-y-2.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{res.author_handle}</span>
                      <span
                        className={`text-[10px] uppercase font-mono px-2.5 py-0.5 rounded font-bold ${badge.style}`}
                      >
                        {badge.label}
                      </span>
                    </div>

                    <p className="text-slate-300 font-sans italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                      "{res.content}"
                    </p>

                    <p className="text-[11px] text-slate-400 font-mono">
                      <strong>Audit Decision:</strong> {res.reason}
                    </p>

                    {res.reply_text && (
                      <div className="mt-2 bg-indigo-950/20 border border-indigo-800/40 p-3 rounded-lg text-indigo-200 space-y-1">
                        <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase tracking-wider block">
                          Autonomous Output ({business?.name} AI):
                        </span>
                        <p className="leading-relaxed">{res.reply_text}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}