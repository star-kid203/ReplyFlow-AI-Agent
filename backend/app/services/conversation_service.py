# FILE: backend/app/services/conversation_service.py
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ChannelType, Conversation, Message, MessageSender
from app.repositories.conversation_repository import ConversationRepository


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.repo = ConversationRepository(db)

    async def receive_incoming_message(
        self,
        business_id: uuid.UUID,
        external_customer_id: str,
        channel: ChannelType,
        content: str,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> Message:
        """
        Main Ingestion Flow:
        1. Resolve customer
        2. Resolve or create active conversation
        3. Persist incoming customer message
        """
        customer = await self.repo.get_or_create_customer(
            business_id=business_id,
            external_id=external_customer_id,
            name=customer_name,
            email=customer_email
        )

        conversation = await self.repo.get_or_create_conversation(
            business_id=business_id,
            customer_id=customer.id,
            channel=channel
        )

        message = await self.repo.add_message(
            conversation_id=conversation.id,
            sender=MessageSender.CUSTOMER,
            content=content
        )
        return message

    async def get_conversation(self, conversation_id: uuid.UUID) -> Conversation:
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found."
            )
        return conversation

    async def list_conversations(self, business_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Conversation]:
        return await self.repo.list_conversations(business_id, skip=skip, limit=limit)