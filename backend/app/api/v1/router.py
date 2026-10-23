# FILE: backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import (
    agent,
    approvals,
    businesses,
    connectors,
    conversations,
    health,
    knowledge,
    packages,
    products,
    social,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(businesses.router)
api_router.include_router(packages.router)
api_router.include_router(products.router)
api_router.include_router(knowledge.router)
api_router.include_router(connectors.router)
api_router.include_router(conversations.router)
api_router.include_router(agent.router)
api_router.include_router(approvals.router)
api_router.include_router(social.router)
api_router.include_router(webhooks.router)