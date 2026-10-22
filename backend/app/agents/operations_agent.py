# FILE: backend/app/agents/operations_agent.py
import json
import uuid
from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.llm_provider import get_llm_provider
from app.models.entities import (
    ActionStatus,
    AgentAction,
    Business,
    BusinessKnowledge,
    Conversation,
    ConversationStatus,
    Message,
    MessageSender,
    Product,
)


# 1. State Definition (Context passing through the graph)
class AgentState(TypedDict):
    business_id: uuid.UUID
    conversation_id: uuid.UUID
    customer_message: str
    channel: str

    # Context loaded from DB
    business_name: str
    communication_style: str
    conversation_history: List[Dict[str, str]]

    # Step 1: Understanding
    intent: str
    sentiment: str
    product_keywords: List[str]

    # Step 2: Verified Ground Truth from PostgreSQL
    verified_knowledge: List[Dict[str, str]]
    verified_products: List[Dict[str, Any]]

    # Step 3: Reasoning & Autonomy Mode
    mode: str  # "automatic" | "approval_required" | "escalate"
    confidence: float
    reasoning: str
    proposed_action: Optional[str]

    # Step 4: Verification & Response
    final_response: str


class OperationsAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider().get_model(temperature=0.1)

    async def run(self, conversation_id: uuid.UUID, customer_message: str) -> Dict[str, Any]:
        """Runs the LangGraph agent for an incoming message."""
        # 1. Load initial business and conversation context from DB
        conv_query = select(Conversation).where(Conversation.id == conversation_id)
        conv_result = await self.db.execute(conv_query)
        conv = conv_result.scalar_one_or_none()

        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        biz_query = select(Business).where(Business.id == conv.business_id)
        biz_result = await self.db.execute(biz_query)
        business = biz_result.scalar_one()

        # Load recent message history
        msg_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        msg_result = await self.db.execute(msg_query)
        messages = list(reversed(msg_result.scalars().all()))

        history = [
            {"sender": m.sender.value, "content": m.content}
            for m in messages
        ]

        initial_state: AgentState = {
            "business_id": business.id,
            "conversation_id": conversation_id,
            "customer_message": customer_message,
            "channel": conv.channel.value,
            "business_name": business.name,
            "communication_style": business.communication_style,
            "conversation_history": history,
            "intent": "general_inquiry",
            "sentiment": "neutral",
            "product_keywords": [],
            "verified_knowledge": [],
            "verified_products": [],
            "mode": "automatic",
            "confidence": 1.0,
            "reasoning": "",
            "proposed_action": None,
            "final_response": "",
        }

        # Build and execute the graph
        workflow = StateGraph(AgentState)
        workflow.add_node("understand_intent", self._understand_intent_node)
        workflow.add_node("retrieve_ground_truth", self._retrieve_ground_truth_node)
        workflow.add_node("reason_and_classify", self._reason_and_classify_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("record_action", self._record_action_node)

        # Sequential Flow
        workflow.set_entry_point("understand_intent")
        workflow.add_edge("understand_intent", "retrieve_ground_truth")
        workflow.add_edge("retrieve_ground_truth", "reason_and_classify")
        workflow.add_edge("reason_and_classify", "generate_response")
        workflow.add_edge("generate_response", "record_action")
        workflow.add_edge("record_action", END)

        app = workflow.compile()
        final_state = await app.ainvoke(initial_state)
        return final_state

    # --- NODE IMPLEMENTATIONS ---

    async def _understand_intent_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 1: Extract intent, sentiment, and product keywords."""
        prompt = (
            "Analyze this customer message for a customer-operations system.\n"
            f"Customer Message: '{state['customer_message']}'\n\n"
            "Return a strictly valid JSON object with:\n"
            "- 'intent': one of ('product_inquiry', 'order_status', 'refund_request', 'complaint', 'general_faq')\n"
            "- 'sentiment': one of ('positive', 'neutral', 'frustrated', 'angry')\n"
            "- 'product_keywords': list of product names or model numbers mentioned (e.g. ['iPhone 17', 'black'])\n"
            "Output JSON only."
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        try:
            cleaned = response.content.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
            return {
                "intent": data.get("intent", "general_inquiry"),
                "sentiment": data.get("sentiment", "neutral"),
                "product_keywords": data.get("product_keywords", []),
            }
        except Exception:
            return {
                "intent": "general_inquiry",
                "sentiment": "neutral",
                "product_keywords": [],
            }

    async def _retrieve_ground_truth_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 2: Retrieve verified products and policies from PostgreSQL."""
        # 1. Query policies / knowledge
        k_query = select(BusinessKnowledge).where(
            BusinessKnowledge.business_id == state["business_id"],
            BusinessKnowledge.is_active.is_(True)
        )
        k_res = await self.db.execute(k_query)
        knowledge_items = [
            {"category": k.category, "title": k.title, "content": k.content}
            for k in k_res.scalars().all()
        ]

        # 2. Query products matching keywords or return catalog
        p_query = select(Product).where(Product.business_id == state["business_id"])
        p_res = await self.db.execute(p_query)
        products = [
            {
                "sku": p.sku,
                "name": p.name,
                "price": float(p.price),
                "stock_quantity": p.stock_quantity,
                "metadata": p.metadata_info
            }
            for p in p_res.scalars().all()
        ]

        return {
            "verified_knowledge": knowledge_items,
            "verified_products": products,
        }

    async def _reason_and_classify_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 3: Determine autonomy mode (automatic, approval_required, escalate)."""
        sentiment = state["sentiment"]
        intent = state["intent"]

        # Mode 3: Human Escalation Trigger
        if sentiment == "angry" or intent == "complaint" or "scam" in state["customer_message"].lower():
            return {
                "mode": "escalate",
                "confidence": 0.95,
                "reasoning": "Customer exhibits high frustration/anger or claims severe dissatisfaction. Requires human intervention.",
                "proposed_action": "route_to_human_agent",
            }

        # Mode 2: Approval Required Trigger (e.g. refunds)
        if intent == "refund_request" or "refund" in state["customer_message"].lower():
            return {
                "mode": "approval_required",
                "confidence": 0.88,
                "reasoning": "Customer requested a refund. In accordance with CamTech policy, refund actions require human staff approval.",
                "proposed_action": "create_refund_approval_ticket",
            }

        # Mode 1: Automatic Resolution
        return {
            "mode": "automatic",
            "confidence": 0.98,
            "reasoning": "Routine product or policy question. Verified information available in database.",
            "proposed_action": "respond_automatically",
        }

    async def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 4: Formulate the response using ONLY verified facts."""
        mode = state["mode"]

        if mode == "escalate":
            reply = (
                f"Thank you for contacting {state['business_name']}. I understand your frustration and "
                "I have escalated your inquiry directly to our senior support team. A team member will "
                "review this conversation and reach out to you shortly."
            )
            return {"final_response": reply}

        if mode == "approval_required":
            reply = (
                f"Thank you for reaching out to {state['business_name']}. I have registered your request "
                "regarding your refund. In accordance with our policy, refund requests are reviewed by our "
                "support managers. We have submitted your case for approval and will notify you as soon as it is processed."
            )
            return {"final_response": reply}

        # Mode 1: Automatic Response formulation
        system_prompt = (
            f"You are the AI Customer Operations Agent for {state['business_name']}.\n"
            f"Communication style: {state['communication_style']}.\n"
            "CRITICAL INSTRUCTION: You must strictly base your response on the verified business knowledge "
            "and verified products provided below. NEVER invent prices, stock numbers, discounts, or policies. "
            "If an item is out of stock, state that it is out of stock.\n\n"
            f"VERIFIED KNOWLEDGE:\n{json.dumps(state['verified_knowledge'], indent=2)}\n\n"
            f"VERIFIED PRODUCTS:\n{json.dumps(state['verified_products'], indent=2)}\n"
        )

        user_prompt = f"Customer message: '{state['customer_message']}'\nFormulate the response."

        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        return {"final_response": response.content.strip()}

    async def _record_action_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 5: Auditability - Record the agent's action and send the message."""
        # 1. Update conversation status if escalated
        conv_query = select(Conversation).where(Conversation.id == state["conversation_id"])
        conv_res = await self.db.execute(conv_query)
        conv = conv_res.scalar_one()

        if state["mode"] == "escalate":
            conv.status = ConversationStatus.ESCALATED
        elif state["mode"] == "approval_required":
            conv.status = ConversationStatus.PENDING_APPROVAL

        # 2. Record Agent Action for human auditability
        action = AgentAction(
            conversation_id=state["conversation_id"],
            action_type=state["proposed_action"] or state["mode"],
            status=ActionStatus.EXECUTED if state["mode"] == "automatic" else ActionStatus.PENDING,
            reasoning=state["reasoning"],
            payload={
                "intent": state["intent"],
                "sentiment": state["sentiment"],
                "mode": state["mode"],
                "confidence": state["confidence"],
                "response": state["final_response"],
            },
            requires_approval=(state["mode"] == "approval_required"),
        )
        self.db.add(action)

        # 3. Append the agent message to the conversation
        msg = Message(
            conversation_id=state["conversation_id"],
            sender=MessageSender.AGENT,
            content=state["final_response"],
            metadata_info={"agent_mode": state["mode"], "confidence": state["confidence"]}
        )
        self.db.add(msg)

        await self.db.commit()
        return {}