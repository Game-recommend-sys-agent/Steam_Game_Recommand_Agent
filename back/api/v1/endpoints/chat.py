from fastapi import APIRouter, HTTPException
from back.schemas.chat import ChatRequest, ChatResponse
from back.services.langchain import LangChainService

router = APIRouter()
service = LangChainService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await service.chat(request.query)
        sources = [doc.metadata for doc in result.get("source_documents", [])]
        return ChatResponse(answer=result["result"], sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
