from fastapi import APIRouter
from back.api.v1.endpoints import chat, document

api_router = APIRouter()
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(document.router, tags=["documents"])
