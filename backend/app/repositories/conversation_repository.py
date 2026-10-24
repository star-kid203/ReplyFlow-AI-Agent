# FILE: backend/app/repositories/conversation_repository.py
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import ChannelType, Conversation, ConversationStatus, Customer, Message, MessageSender


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_customer(
        self,
        business_id: uuid.UUID,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Customer:
        query = select(Customer).where(
            Customer.business_id == business_id,
            Customer.external_id == external_id
        )
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(
                business_id=business_id,
                external_id=external_id,
                name=name,
                email=email
            )
            self.db.add(customer)
            await self.db.commit()
            await self.db.refresh(customer)
        return customer

    async def get_or_create_conversation(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: ChannelType
    ) -> Conversation:
        # Find active (open/pending/escalated) conversation
        query = select(Conversation).where(
            Conversation.business_id == business_id,
            Conversation.customer_id == customer_id,
            Conversation.status.in_([ConversationStatus.OPEN, ConversationStatus.PENDING_APPROVAL, ConversationStatus.ESCALATED])
        ).options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                business_id=business_id,
                customer_id=customer_id,
                channel=channel,
                status=ConversationStatus.OPEN
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            conversation.messages = []
        return conversation

    async def get_conversation_by_id(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        query = select(Conversation).where(
            Conversation.id == conversation_id
        ).options(selectinload(Conversation.messages))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        sender: MessageSender,
        content: str,
        metadata_info: Optional[dict] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            metadata_info=metadata_info or {}
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def list_conversations(self, business_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Conversation]:
        query = select(Conversation).where(
            Conversation.business_id == business_id
        ).options(selectinload(Conversation.messages)).offset(skip).limit(limit).order_by(Conversation.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())