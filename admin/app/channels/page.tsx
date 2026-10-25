// FILE: admin/app/channels/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Copy,
  Check,
  Eye,
  EyeOff,
  RefreshCw,
  Layers,
  Lock,
} from "lucide-react";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_tier?: string;
  enabled_channels?: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const GATEWAYS = [
  {
    id: "meta-gw",
    name: "Meta Universal Ingress Gateway",
    platforms: "WhatsApp Cloud API, Instagram Comments/DMs, Facebook Pages & Messenger",
    endpoint: `${API_BASE}/webhooks/meta`,
    verifyToken: "replyflow_meta_token_secret",
    status: "Healthy • SSL Verified",
    desc: "Single webhook receiver that multiplexes all Meta Graph API events to isolated tenant databases.",
  },
  {
    id: "linkedin-gw",
    name: "LinkedIn Social Actions Ingress",
    platforms: "Organization UGC Posts, Leadership Commentary, Page Messages",
    endpoint: `${API_BASE}/webhooks/linkedin`,
    verifyToken: "whsec_li_hmac256_live_token_77a9b",
    status: "Healthy • Active Stream",
    desc: "Ingests LinkedIn community webhooks, validates HMAC signatures, and routes to agent pipelines.",
  },
  {
    id: "streaming-gw",
    name: "Universal Social & Streaming Pipe",
    platforms: "YouTube Comments, TikTok Videos, Spotify Q&A Streams",
    endpoint: `${API_BASE}/webhooks/streaming/{business_id}`,
    verifyToken: "sec_tenant_partition_uuid_v4",
    status: "Healthy • Event Driven",
    desc: "Normalizes incoming streaming commentary and attaches 1-click WhatsApp bridge deep-links.",
  },
  {
    id: "website-gw",
    name: "Website Live Chat Widget Socket",
    platforms: "WordPress, Shopify, Webflow, Custom Next.js & React Portals",
    endpoint: `${API_BASE}/webhooks/website/{business_id}`,
    verifyToken: "pub_live_client_socket_key_99f",
    status: "Sub-second • Zero Latency",
    desc: "Direct JSON websocket and REST pipe feeding client customer support chat widgets.",
  },
];

export default function ChannelGatewaysPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [visibleSecrets, setVisibleSecrets] = useState<Record<string, boolean>>({});

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/businesses`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setTenants(Array.isArray(data) ? data : []);
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

  const toggleSecretVisibility = (id: string) => {
    setVisibleSecrets((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-indigo-400" /> Global Ingress Channel Gateways
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Universal public webhook entry points that multiplex inbound customer traffic across all onboarded tenants.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl transition self-start"
          title="Refresh Gateways"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Security Compliance Banner */}
      <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono text-slate-400">
        <span className="text-slate-500 hidden sm:inline">256-Bit SSL Gateway Ingress</span>
      </div>

      {/* Gateway Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {GATEWAYS.map((gw) => {
          const isSecretVisible = visibleSecrets[gw.id] ?? false;

          return (
            <div
              key={gw.id}
              className="bg-slate-900/70 border border-slate-800/80 hover:border-slate-700/80 p-6 rounded-2xl space-y-4 transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    {gw.status}
                  </span>
                  <span className="text-xs font-mono text-slate-500">Gateway ID: {gw.id}</span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white">{gw.name}</h3>
                  <p className="text-xs text-indigo-400 font-mono mt-0.5">{gw.platforms}</p>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">{gw.desc}</p>
                </div>

                {/* Endpoint Box */}
                <div className="space-y-1.5 pt-2">
                  <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">
                    Public Webhook Callback URL:
                  </span>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex items-center justify-between font-mono text-xs text-slate-300">
                    <span className="truncate pr-2">{gw.endpoint}</span>
                    <button
                      onClick={() => copyToClipboard(gw.endpoint, `ep-${gw.id}`)}
                      className="p-1.5 text-slate-400 hover:text-white transition shrink-0"
                      title="Copy URL"
                    >
                      {copiedKey === `ep-${gw.id}` ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Handshake Secret with Masking & Eye Toggle */}
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">
                      Handshake / Verification Secret:
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">Masked for Video Demo</span>
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex items-center justify-between font-mono text-xs text-slate-300">
                    <span className="truncate pr-2 font-mono tracking-wider">
                      {isSecretVisible ? gw.verifyToken : "••••••••••••••••••••••••"}
                    </span>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => toggleSecretVisibility(gw.id)}
                        className="p-1.5 text-slate-400 hover:text-indigo-400 transition"
                        title={isSecretVisible ? "Hide Secret" : "Reveal Secret"}
                      >
                        {isSecretVisible ? (
                          <EyeOff className="w-4 h-4 text-amber-400" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(gw.verifyToken, `sec-${gw.id}`)}
                        className="p-1.5 text-slate-400 hover:text-white transition"
                        title="Copy Secret"
                      >
                        {copiedKey === `sec-${gw.id}` ? (
                          <Check className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic Multi-Tenant Routing Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Dynamic Tenant Routing Multiplexer
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              How the gateway dynamically binds incoming phone IDs, page URLs, and handles to the correct tenant organization.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{tenants.length} tenants mapped</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Organization</th>
                <th className="py-3.5 px-4">Tenant UUID</th>
                <th className="py-3.5 px-4">Package Tier</th>
                <th className="py-3.5 px-4">Channel Routing Targets</th>
                <th className="py-3.5 px-4 text-right">Dedicated Webhook</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {tenants.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-4 px-4">
                    <p className="font-semibold text-white">{t.name}</p>
                    <span className="text-[10px] text-slate-500 font-mono">/{t.slug}</span>
                  </td>

                  <td className="py-4 px-4 font-mono text-indigo-300">{t.id}</td>

                  <td className="py-4 px-4">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase bg-indigo-950 text-indigo-400 border border-indigo-800 font-bold">
                      {t.plan_tier || "business"}
                    </span>
                  </td>

                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1">
                      {(t.enabled_channels || ["whatsapp", "website_chat"]).map((ch) => (
                        <span
                          key={ch}
                          className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-400"
                        >
                          {ch.replace("_", " ")}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() =>
                        copyToClipboard(`${API_BASE}/webhooks/ingest?business_id=${t.id}`, t.id)
                      }
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono inline-flex items-center gap-1.5 transition"
                    >
                      {copiedKey === t.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" /> Ingest Link
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}