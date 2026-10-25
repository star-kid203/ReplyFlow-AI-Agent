// FILE: admin/app/provision/page.tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  Package,
  Building2,
  Sliders,
  Database,
  MapPin,
  Trash2,
  Plus,
  Check,
  Lock,
} from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface BranchSourceItem {
  id: string;
  branch_name: string;
  country: string;
  city: string;
  exact_address: string;
  source_type: "pos_register" | "cloud_spreadsheet" | "warehouse_depot" | "ecommerce_store";
  connection_url: string;
}

const TIER_SPECIFICATIONS = [
  {
    id: "startup",
    name: "Start Up",
    price: "$29",
    priceNum: 29,
    responses: "1,000",
    comments: "500",
    channelCap: "150/ch",
    maxLocations: 1,
    desc: "Early-stage retail stores and solo business founders.",
    channels: ["website_chat", "whatsapp"],
    features: [
      "1,000 Monthly AI Responses",
      "500 Social Comments (Cap 150/ch)",
      "Website Live Chat & WhatsApp Cloud API",
      "Standard Business Brain Grounding",
      "Single Store Location / POS Sync",
    ],
  },
  {
    id: "stella",
    name: "Stella",
    price: "$79",
    priceNum: 79,
    responses: "5,000",
    comments: "2,000",
    channelCap: "1,000/ch",
    maxLocations: 2,
    desc: "Growing consumer brands and social-first retail storefronts.",
    channels: ["website_chat", "whatsapp", "instagram_comment", "instagram_dm", "facebook_comment"],
    features: [
      "5,000 Monthly AI Responses",
      "2,000 Social Comments (Cap 1,000/ch)",
      "Meta Suite (Instagram DMs/Comments, FB Page)",
      "Automated Sentiment & Emoji Modulation",
      "Up to 2 Store Locations / Depots",
    ],
  },
  {
    id: "business",
    name: "Business",
    price: "$199",
    priceNum: 199,
    responses: "25,000",
    comments: "10,000",
    channelCap: "5,000/ch",
    maxLocations: 5,
    desc: "B2B consultancies, IT agencies, and omnichannel supply enterprises.",
    badge: "RECOMMENDED B2B",
    channels: [
      "website_chat",
      "whatsapp",
      "instagram_comment",
      "instagram_dm",
      "facebook_comment",
      "linkedin_comment",
      "linkedin_message",
      "youtube_comment",
    ],
    features: [
      "25,000 Monthly AI Responses",
      "10,000 Social Comments (Cap 5,000/ch)",
      "LinkedIn Page UGC & YouTube Video Bridges",
      "Multi-Branch Data Fabric (Up to 5 Locations)",
      "Lead-to-DM Private Handoff & Booking",
    ],
  },
  {
    id: "business_premium",
    name: "Business Premium",
    price: "$499",
    priceNum: 499,
    responses: "100,000",
    comments: "50,000",
    channelCap: "50,000/ch",
    maxLocations: 99,
    desc: "High-volume enterprises requiring dedicated multi-depot data fabric & SLAs.",
    badge: "ENTERPRISE SLA",
    channels: [
      "website_chat",
      "whatsapp",
      "instagram_comment",
      "instagram_dm",
      "facebook_comment",
      "linkedin_comment",
      "linkedin_message",
      "youtube_comment",
      "spotify_qa",
      "tiktok",
    ],
    features: [
      "100,000 Monthly AI Responses",
      "50,000 Social Comments (Cap 50,000/ch)",
      "All Omnichannel Pipes (+ TikTok & Spotify Q&A)",
      "Unlimited Multi-Branch Locations Worldwide",
      "24/7 Dedicated Human Operator Queue & SLA",
    ],
  },
];

const INDUSTRIES = [
  "Technology & Software (SaaS)",
  "Consumer Electronics & Hardware",
  "Healthcare & Telehealth Clinics",
  "Accounting, Tax & Financial Services",
  "Food & Beverage / Restaurant Chains",
  "Retail & Fashion E-Commerce",
  "Logistics, Freight & Supply Chain",
  "Real Estate & Property Management",
  "Legal & Corporate Advisory",
  "Manufacturing & Industrial Supplies",
  "Education & EdTech Academies",
  "Automotive & Dealerships",
  "Beauty, Cosmetics & Wellness",
  "Hospitality, Hotels & Travel",
  "Agriculture & Agribusiness Supplies",
];

const AUDIENCE_TYPES = [
  "B2B Enterprise Decision Makers & Corporate Buyers",
  "Direct-to-Consumer (D2C) Retail Shoppers",
  "Medical Patients & Clinic Visitors",
  "Wholesale Resellers & Regional Distributors",
  "SME Business Owners & Entrepreneurs",
  "Government Agencies & Public Institutions",
  "High-Net-Worth & Luxury Clients",
];

export default function ProvisionTenantPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);

  // Step 1: Package
  const [selectedPlan, setSelectedPlan] = useState("business");
  const activePlanConfig = TIER_SPECIFICATIONS.find((p) => p.id === selectedPlan) || TIER_SPECIFICATIONS[2];

  // Step 2: Enterprise Identity
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [industry, setIndustry] = useState("Consumer Electronics & Hardware");
  const [targetAudience, setTargetAudience] = useState("Direct-to-Consumer (D2C) Retail Shoppers");
  const [description, setDescription] = useState("");

  // Step 3: Social & Comment Directives (All 5 Categories)
  const [filterNoise, setFilterNoise] = useState(true);
  const [convertLeads, setConvertLeads] = useState(true);
  const [handleCriticism, setHandleCriticism] = useState(true);
  const [routeGrievances, setRouteGrievances] = useState(true);
  const [routePartnerships, setRoutePartnerships] = useState(true);

  // Step 4: Dynamic Branch Locations (Clean Slate — Zero Hardcoding)
  const [branchLocations, setBranchLocations] = useState<BranchSourceItem[]>([
    {
      id: "branch-1",
      branch_name: "",
      country: "Cameroon",
      city: "",
      exact_address: "",
      source_type: "pos_register",
      connection_url: "",
    },
  ]);

  const [creating, setCreating] = useState(false);

  const handleNameChange = (val: string) => {
    setName(val);
    setSlug(val.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-"));
  };

  const handleAddBranch = () => {
    if (branchLocations.length >= activePlanConfig.maxLocations) {
      alert(`The ${activePlanConfig.name} plan supports up to ${activePlanConfig.maxLocations} registered location(s). Select a higher tier to add more.`);
      return;
    }
    setBranchLocations([
      ...branchLocations,
      {
        id: `branch-${Date.now()}`,
        branch_name: "",
        country: "Cameroon",
        city: "",
        exact_address: "",
        source_type: "pos_register",
        connection_url: "",
      },
    ]);
  };

  const handleRemoveBranch = (id: string) => {
    if (branchLocations.length === 1) {
      alert("At least one primary branch or office must be specified.");
      return;
    }
    setBranchLocations(branchLocations.filter((b) => b.id !== id));
  };

  const handleUpdateBranch = (id: string, field: keyof BranchSourceItem, val: string) => {
    setBranchLocations(
      branchLocations.map((b) => (b.id === id ? { ...b, [field]: val } : b))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      const bizType = industry.toLowerCase().includes("software") || industry.toLowerCase().includes("consulting")
        ? "service"
        : "retail";

      // 1. Create Business Organization in PostgreSQL
      const res = await fetch(`${API_BASE}/businesses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          slug: slug.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
          description: description.trim() || `${name} operating in ${industry}, serving ${targetAudience}.`,
          communication_style: "professional, consultative, and concise",
          agent_display_name: `${name.trim()} AI`,
          business_type: bizType,
          plan_tier: selectedPlan,
          subscription_status: "active",
          enabled_channels: activePlanConfig.channels,
          comment_rules: {
            filter_noise: filterNoise,
            convert_leads: convertLeads,
            handle_criticism: handleCriticism,
            route_sensitive_to_dm: routeGrievances,
            route_partnerships: routePartnerships,
            target_intents: ["lead", "pricing", "inquiry", "criticism", "complaint", "partnership"],
          },
          is_active: true,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to provision organization");
      }

      const newBiz = await res.json();

      // 2. Persist Registered Branch Locations & Data Fabric Connectors
      const validBranches = branchLocations.filter((b) => b.branch_name.trim() !== "");

      await fetch(`${API_BASE}/connectors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_id: newBiz.id,
          connector_type: "zetaris_fabric",
          name: "Universal Zero-Copy Data Fabric",
          base_url: "fabric.internal:10000",
          config: {
            mode: "zero_copy_federation",
            industry_sector: industry,
            target_audience: targetAudience,
            inventory_sources: validBranches,
          },
        }),
      });

      alert(`Organization '${name}' successfully onboarded on ${activePlanConfig.name} plan with ${validBranches.length} registered location(s)!`);
      router.push("/");
    } catch (err: any) {
      alert(`Provisioning error: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Organizations Overview
      </Link>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Onboard New Client</h1>
        </div>

        {/* STEP PROGRESS INDICATOR */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl font-mono text-xs">
          {[
            { num: 1, label: "Plan" },
            { num: 2, label: "Sector" },
            { num: 3, label: "SocialMedia" },
            { num: 4, label: "Locations" },
          ].map((s) => (
            <button
              key={s.num}
              type="button"
              onClick={() => setCurrentStep(s.num as any)}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
                currentStep === s.num
                  ? "bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30"
                  : currentStep > s.num
                  ? "text-emerald-400 bg-slate-950 border border-slate-800"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <span>{s.num}.</span>
              <span className="hidden sm:inline">{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* ========================================================================= */}
        {/* STEP 1: PACKAGE SELECTION & REAL BOUNDARIES */}
        {/* ========================================================================= */}
        {currentStep === 1 && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Package className="w-5 h-5 text-amber-400" />
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                  Step 1: Assign Paid Subscription Tier & Boundaries
                </h2>
                <p className="text-xs text-slate-400">Sets hard monthly response ceilings, per-channel caps, and allowed communication pipes.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {TIER_SPECIFICATIONS.map((pkg) => {
                const isSelected = selectedPlan === pkg.id;
                return (
                  <div
                    key={pkg.id}
                    onClick={() => setSelectedPlan(pkg.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition flex flex-col justify-between space-y-3 relative ${
                      isSelected
                        ? "bg-amber-950/30 border-amber-500 shadow-lg shadow-amber-950/20"
                        : "bg-slate-950 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    {pkg.badge && (
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-amber-500 text-slate-950 font-bold self-start">
                        {pkg.badge}
                      </span>
                    )}

                    <div>
                      <h3 className="text-sm font-bold text-white">{pkg.name}</h3>
                      <div className="text-xl font-extrabold text-white mt-1">
                        {pkg.price}
                        <span className="text-xs text-slate-400 font-normal"> / month</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{pkg.desc}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 space-y-1">
                      <div>Replies: <span className="text-white font-semibold">{pkg.responses}/mo</span></div>
                      <div>Comments: <span className="text-white font-semibold">{pkg.comments}/mo</span></div>
                      <div>Channel Cap: <span className="text-indigo-400 font-semibold">{pkg.channelCap}</span></div>
                    </div>

                    <ul className="pt-2 border-t border-slate-800/80 space-y-1 text-[10px] text-slate-300">
                      {pkg.features.map((feat, i) => (
                        <li key={i} className="flex items-center gap-1.5">
                          <Check className="w-3 h-3 text-emerald-400 shrink-0" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 pt-1">
                      <CheckCircle2 className={`w-4 h-4 ${isSelected ? "text-amber-400" : "text-slate-600"}`} />
                      <span>{isSelected ? "Tier Assigned" : "Select Tier"}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end pt-3">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider rounded-xl transition flex items-center gap-2"
              >
                Proceed to Identity & Industry <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 2: ENTERPRISE IDENTITY & 15+ SECTORS */}
        {/* ========================================================================= */}
        {currentStep === 2 && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Building2 className="w-5 h-5 text-indigo-400" />
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                  Step 2: Company Profile, Industry & Target Market
                </h2>
                <p className="text-xs text-slate-400">Grounds the agent in the company's verified industry domain and audience expectations.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Company Legal Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="e.g. DouaTech Solution Sarl, CamTech Electronics"
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Tenant Slug (Partition ID)</label>
                <input
                  type="text"
                  required
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="douatech-solutions"
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Industry / Operating Sector (15 Verified Sectors)</label>
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-sans"
                >
                  {INDUSTRIES.map((ind) => (
                    <option key={ind} value={ind}>
                      {ind}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Target Client Base / Customer Audience</label>
                <select
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-sans"
                >
                  {AUDIENCE_TYPES.map((aud) => (
                    <option key={aud} value={aud}>
                      {aud}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300">Operational Overview & Service Scope</label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief overview of operational practices, physical locations, and core client deliverables..."
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
              />
            </div>

            <div className="flex justify-between pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>

              <button
                type="button"
                disabled={!name.trim()}
                onClick={() => setCurrentStep(3)}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-bold uppercase tracking-wider rounded-xl transition flex items-center gap-2"
              >
                Configure Social Directives <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 3: ALL 5 SOCIAL DIRECTIVES & CHANNEL GATING */}
        {/* ========================================================================= */}
        {currentStep === 3 && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sliders className="w-5 h-5 text-emerald-400" />
                <div>
                  <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                    Step 3: 5-Tier Social Comment Engagement Directives
                  </h2>
                  <p className="text-xs text-slate-400">Governance rules applied across all comments on supported plan channels.</p>
                </div>
              </div>
              <span className="text-xs font-mono bg-slate-950 border border-slate-800 px-3 py-1 rounded-full text-indigo-400">
                Plan: {activePlanConfig.name}
              </span>
            </div>

            {/* Allowed Channels for this plan */}
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
              <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">
                Active Channel Pipes for {activePlanConfig.name} Plan:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {activePlanConfig.channels.map((ch) => (
                  <span
                    key={ch}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800"
                  >
                    ✓ {ch.replace("_", " ")}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {/* Directive 1 */}
              <label className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={filterNoise}
                  onChange={(e) => setFilterNoise(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
                />
                <div>
                  <span className="font-bold text-white text-xs block">1. Zero-Cost Noise & Emoji Filter (0 Tokens)</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Drops pure emojis (🔥, ❤️) and friend tags without invoking LLMs, preserving 75% of client token budgets.
                  </p>
                </div>
              </label>

              {/* Directive 2 */}
              <label className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={convertLeads}
                  onChange={(e) => setConvertLeads(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
                />
                <div>
                  <span className="font-bold text-white text-xs block">2. Commercial Sales Inquiries</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Replies with verified pricing and provides 1-click WhatsApp deep-links or private DM discovery scheduling.
                  </p>
                </div>
              </label>

              {/* Directive 3 */}
              <label className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={handleCriticism}
                  onChange={(e) => setHandleCriticism(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
                />
                <div>
                  <span className="font-bold text-white text-xs block">3. Brand Sarcasm & Skepticism Defense</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Engages critics and skeptics publicly with polite brand confidence and verified performance metrics.
                  </p>
                </div>
              </label>

              {/* Directive 4 */}
              <label className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={routeGrievances}
                  onChange={(e) => setRouteGrievances(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
                />
                <div>
                  <span className="font-bold text-white text-xs block">4. Customer Support Grievances & Disputes</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    De-escalates publicly, moves sensitive disputes to private channels, and provisions high-priority Live Inbox tickets.
                  </p>
                </div>
              </label>

              {/* Directive 5 */}
              <label className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={routePartnerships}
                  onChange={(e) => setRoutePartnerships(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 mt-0.5"
                />
                <div>
                  <span className="font-bold text-white text-xs block">5. Technical & B2B Partnership Inquiries</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Captures API integration, reseller, and agency collaboration requests, routing them to engineering discovery.
                  </p>
                </div>
              </label>
            </div>

            <div className="flex justify-between pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>

              <button
                type="button"
                onClick={() => setCurrentStep(4)}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider rounded-xl transition flex items-center gap-2"
              >
                Map Branch Locations <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 4: DYNAMIC MULTI-BRANCH LOCATIONS & DATA SOURCES */}
        {/* ========================================================================= */}
        {currentStep === 4 && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-400" />
                <div>
                  <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                    Step 4: Multi-Branch Locations & Live Inventory Data Sources
                  </h2>
                  <p className="text-xs text-slate-400">
                    Register physical store showrooms, warehouse depots, or office branches with their real data links.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleAddBranch}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-slate-700 transition"
              >
                <Plus className="w-3.5 h-3.5 text-indigo-400" /> Add Location ({branchLocations.length}/{activePlanConfig.maxLocations})
              </button>
            </div>

            <div className="space-y-4">
              {branchLocations.map((branch, index) => (
                <div
                  key={branch.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 relative hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                    <span className="text-[10px] font-mono uppercase text-indigo-400 font-bold flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" /> Branch Location #{index + 1}
                    </span>
                    {branchLocations.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveBranch(branch.id)}
                        className="p-1 text-slate-500 hover:text-rose-400 transition"
                        title="Remove location"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  {/* Row 1: Branch Name */}
                  <div>
                    <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                      Branch / Office / Showroom Name
                    </label>
                    <input
                      type="text"
                      required
                      value={branch.branch_name}
                      onChange={(e) => handleUpdateBranch(branch.id, "branch_name", e.target.value)}
                      placeholder="e.g. Flagship Retail Showroom, Central Logistics Hub, Engineering Practice HQ"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                    />
                  </div>

                  {/* Row 2: Country & City */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                        Country
                      </label>
                      <input
                        type="text"
                        required
                        value={branch.country}
                        onChange={(e) => handleUpdateBranch(branch.id, "country", e.target.value)}
                        placeholder="e.g. Cameroon, Nigeria, United States"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                        City / Town
                      </label>
                      <input
                        type="text"
                        required
                        value={branch.city}
                        onChange={(e) => handleUpdateBranch(branch.id, "city", e.target.value)}
                        placeholder="e.g. Douala, Yaoundé, Lagos, Boston"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                      />
                    </div>
                  </div>

                  {/* Row 3: Physical Address */}
                  <div>
                    <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                      Exact Street Address / PO Box (For precise customer pickup & agency lookup)
                    </label>
                    <input
                      type="text"
                      required
                      value={branch.exact_address}
                      onChange={(e) => handleUpdateBranch(branch.id, "exact_address", e.target.value)}
                      placeholder="e.g. Boulevard de la Liberté, Akwa (Opposite Commercial Bank)"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                    />
                  </div>

                  {/* Row 4: Platform Method & URL */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                        Platform / Recording Method
                      </label>
                      <select
                        value={branch.source_type}
                        onChange={(e) => handleUpdateBranch(branch.id, "source_type", e.target.value as any)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white text-xs focus:outline-none focus:border-indigo-500 font-sans"
                      >
                        <option value="pos_register">Live POS / Barcode Cash Register</option>
                        <option value="cloud_spreadsheet">Cloud Spreadsheet (OneDrive / Google Sheets .XLSX)</option>
                        <option value="warehouse_depot">Central Warehouse (S3 / Cloud ERP Database)</option>
                        <option value="ecommerce_store">E-Commerce Storefront (Shopify / WooCommerce)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] text-slate-400 font-semibold block mb-1">
                        Connection Link / File URL
                      </label>
                      <input
                        type="text"
                        required
                        value={branch.connection_url}
                        onChange={(e) => handleUpdateBranch(branch.id, "connection_url", e.target.value)}
                        placeholder="https://pos.store.com/api or cloud drive file URL"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 font-mono text-white text-[11px] focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3.5 bg-slate-950 border border-indigo-900/40 rounded-xl text-xs text-indigo-300 font-mono">
              🔒 <strong>Data Isolation Guarantee:</strong> Each branch location is mapped to this tenant partition. The AI agents reference these exact addresses for customer pickup queries with zero hallucination.
            </div>

            <div className="flex justify-between pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setCurrentStep(3)}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>

              <button
                type="submit"
                disabled={creating || !name.trim()}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-40 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition shadow-lg shadow-indigo-950/40"
              >
                {creating ? "Provisioning Organization..." : "Complete Enterprise Onboarding"}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}