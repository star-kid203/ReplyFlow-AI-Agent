// FILE: frontend/lib/api.ts
import { getActiveTenantId } from "@/lib/tenant";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Business {
  id: string;
  name: string;
  slug: string;
  description: string;
  communication_style: string;
  agent_display_name?: string;
  business_type?: string;
  plan_tier?: string;
  subscription_status?: string;
  enabled_channels?: string[];
  comment_rules?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: "customer" | "agent" | "human_operator";
  content: string;
  created_at: string;
  metadata_info?: Record<string, any>;
}

export interface Conversation {
  id: string;
  business_id: string;
  customer_id: string;
  customer_name?: string;
  customer_handle?: string;
  channel: string;
  status: "open" | "pending_approval" | "escalated" | "resolved";
  created_at: string;
  updated_at?: string;
  handoff_summary?: Record<string, any>;
  messages: Message[];
}

export interface AgentStepTrace {
  agent_name: string;
  role_description: string;
  action_taken: string;
  evidence_consulted: string;
  timestamp: string;
}

export interface AgentProcessResult {
  conversation_id: string;
  customer_id: string;
  intent: string;
  sentiment: string;
  decision: "auto_respond" | "require_approval" | "escalate" | string;
  requires_human: boolean;
  escalation_reason?: string;
  response_text: string;
  retrieved_products_count: number;
  agent_trace_logs?: AgentStepTrace[];
}

export interface PendingApproval {
  id: string;
  conversation_id: string;
  action_type: string;
  status: string;
  reasoning: string;
  payload: Record<string, any>;
  requires_approval: boolean;
  created_at: string;
}

export type AgentAction = PendingApproval;

export interface Product {
  id: string;
  sku: string;
  name: string;
  price: string | number;
  min_price?: string | number;
  pricing_model?: string;
  stock_quantity: number;
  description?: string;
  metadata_info?: Record<string, any>;
}

export interface KnowledgeItem {
  id: string;
  category: string;
  title: string;
  content: string;
}

function resolveTenantId(providedId?: string): string {
  if (providedId && providedId !== "undefined" && providedId !== "null" && providedId.trim() !== "") {
    return providedId.trim();
  }
  return getActiveTenantId();
}

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!res.ok) return { status: "unhealthy" };
    return res.json();
  } catch (err) {
    return { status: "offline" };
  }
}

export async function fetchBusiness(businessId?: string): Promise<Business | null> {
  const activeId = resolveTenantId(businessId);
  try {
    const res = await fetch(`${API_BASE}/businesses/${activeId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("fetchBusiness error:", err);
    return null;
  }
}

export async function fetchConversations(businessId?: string): Promise<Conversation[]> {
  const activeId = resolveTenantId(businessId);
  try {
    const res = await fetch(`${API_BASE}/conversations?business_id=${activeId}`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("fetchConversations error:", err);
    return [];
  }
}

export async function fetchPendingApprovals(businessId?: string): Promise<PendingApproval[]> {
  const activeId = resolveTenantId(businessId);
  try {
    const res = await fetch(`${API_BASE}/approvals?business_id=${activeId}`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("fetchPendingApprovals error:", err);
    return [];
  }
}

export async function fetchProducts(businessId?: string): Promise<Product[]> {
  const activeId = resolveTenantId(businessId);
  try {
    const res = await fetch(`${API_BASE}/products?business_id=${activeId}&limit=50`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.items)) return data.items;
    return [];
  } catch (err) {
    console.error("fetchProducts error:", err);
    return [];
  }
}

export async function fetchKnowledge(businessId?: string): Promise<KnowledgeItem[]> {
  const activeId = resolveTenantId(businessId);
  try {
    const res = await fetch(`${API_BASE}/knowledge?business_id=${activeId}`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("fetchKnowledge error:", err);
    return [];
  }
}

export async function processAgentInteraction(data: {
  business_id: string;
  external_customer_id: string;
  channel: string;
  content: string;
  customer_name?: string;
  conversation_id?: string;
}): Promise<AgentProcessResult> {
  const res = await fetch(`${API_BASE}/agent/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Agent processing failed");
  }
  return res.json();
}

export async function fetchConversationTrace(conversationId: string): Promise<AgentStepTrace[]> {
  try {
    const res = await fetch(`${API_BASE}/agent/trace/${conversationId}`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("fetchConversationTrace error:", err);
    return [];
  }
}

export async function approveAgentAction(actionId: string, reviewerName: string = "Admin") {
  const res = await fetch(`${API_BASE}/approvals/${actionId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer_name: reviewerName }),
  });
  return res.json();
}

export async function rejectAgentAction(actionId: string, reviewerName: string = "Admin", reason: string = "Policy mismatch") {
  const res = await fetch(`${API_BASE}/approvals/${actionId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer_name: reviewerName, rejection_reason: reason }),
  });
  return res.json();
}

export async function ingestBatchSocial(payload: any) {
  const res = await fetch(`${API_BASE}/social/batch-ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export const api = {
  checkHealth: fetchHealth,
  getBusiness: fetchBusiness,
  listConversations: fetchConversations,
  listPendingApprovals: fetchPendingApprovals,
  listProducts: fetchProducts,
  listKnowledge: fetchKnowledge,
  processMessage: processAgentInteraction,
  getTrace: fetchConversationTrace,
  approveAction: approveAgentAction,
  rejectAction: rejectAgentAction,
  batchIngestSocial: ingestBatchSocial,
  listEscalations: async (businessId?: string) => {
    const convs = await fetchConversations(businessId);
    return convs.filter((c) => c.status === "escalated");
  },
};