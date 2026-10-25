// FILE: frontend/lib/tenant.ts
"use client";

export const FALLBACK_BUSINESS_ID = "ed722c20-1307-4748-a9b4-ccf5e454fe21";

export function getActiveTenantId(): string {
  if (typeof window === "undefined") return FALLBACK_BUSINESS_ID;

  // 1. Absolute Priority: URL query param (?tenant=... or ?business_id=...)
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("tenant") || params.get("business_id");
  if (fromUrl && fromUrl.trim() !== "") {
    // Save to sessionStorage (tab-isolated) and localStorage
    try {
      sessionStorage.setItem("replyflow_active_tenant", fromUrl.trim());
      localStorage.setItem("replyflow_active_tenant", fromUrl.trim());
    } catch {}
    return fromUrl.trim();
  }

  // 2. Tab-isolated session storage (prevents one tab from overwriting another)
  try {
    const fromSession = sessionStorage.getItem("replyflow_active_tenant");
    if (fromSession && fromSession.trim() !== "") return fromSession.trim();
  } catch {}

  // 3. Persistent local storage fallback
  try {
    const stored = localStorage.getItem("replyflow_active_tenant");
    if (stored && stored.trim() !== "") return stored.trim();
  } catch {}

  return FALLBACK_BUSINESS_ID;
}

export function setActiveTenantId(tenantId: string) {
  if (typeof window === "undefined" || !tenantId) return;
  try {
    sessionStorage.setItem("replyflow_active_tenant", tenantId.trim());
    localStorage.setItem("replyflow_active_tenant", tenantId.trim());
  } catch {}
}