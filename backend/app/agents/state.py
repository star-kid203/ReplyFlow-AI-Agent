# FILE: backend/app/agents/state.py
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentStepLog(TypedDict):
    agent_name: str
    node_id: str
    role_description: str
    action_taken: str
    evidence_consulted: str
    latency_ms: int
    tokens_consumed: int
    status: str  # "success" | "warning" | "escalated"
    timestamp: str


class AgentState(TypedDict):
    """
    Shared Context passed across all cooperating agents in the LangGraph workflow.
    Supports multi-agent delegation, critique, validation, and human escalation.
    """
    business_id: str
    customer_id: str
    conversation_id: str
    customer_name: Optional[str]
    channel: str

    message_content: str
    business_name: str
    business_description: str
    communication_style: str
    business_type: str
    agent_name: str
    conversation_history: List[Dict[str, str]]

    # Agent 1: Inbound Triage & Sentiment Specialist
    intent: str
    sentiment: str
    human_requested: bool
    has_stated_problem: bool
    user_is_insisting: bool
    search_query: str
    project_scope_topic: Optional[str]
    problem_summary: Optional[str]
    expected_resolution: Optional[str]
    suggested_emoji: Optional[str]
    temporal_context: Dict[str, Any]

    # Agent 2: Zetaris Data Fabric Specialist
    retrieved_knowledge: List[Dict[str, str]]
    retrieved_products: List[Dict[str, Any]]
    recommended_alternatives: List[Dict[str, Any]]
    multi_store_inventory: Dict[str, Any]

    # Agent 3: Commercial Negotiator & Scoping Specialist
    meeting_agreed_time: Optional[str]
    meeting_platform: Optional[str]
    is_meeting_ready_to_book: bool
    drafted_response: str

    # Agent 4: Policy & Safety Guardrail Specialist (Critique & Validation)
    decision: str  # "auto_respond", "require_approval", "escalate", "book_meeting_and_confirm"
    requires_human: bool
    escalation_reason: Optional[str]
    proposed_action: Optional[str]
    handoff_summary: Dict[str, Any]
    validation_passed: bool
    critique_feedback: Optional[str]

    # Agent 5: Action & Dispatch Specialist
    final_response: str
    agent_trace_logs: List[AgentStepLog]
    total_execution_ms: int
    total_tokens_burned: int