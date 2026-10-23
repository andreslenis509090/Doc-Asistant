from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from supabase import Client
from app.core.supabase import get_current_user_id, get_supabase_client
from app.models.schemas import ChatRequest, ChatResponse
from app.repositories.document_repository import DocumentRepository
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service(
    db: Client = Depends(get_supabase_client)
) -> ChatService:
    repository = DocumentRepository(db)
    return ChatService(repository)


@router.post("/stream")
def chat_stream(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service)
):
    """
    Endpoint de chat en tiempo real mediante SSE (Server-Sent Events / Streaming).
    
    Envía eventos con el formato:
    - data: {"type": "citations", "citations": [...]}
    - data: {"type": "token", "content": "..."}
    - data: {"type": "done"}
    """
    generator = service.stream_chat(
        message=payload.message,
        user_id=user_id,
        document_id=payload.document_id,
        match_count=payload.match_count
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("", response_model=ChatResponse)
def chat_sync(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    Endpoint de chat síncrono estándar (útil para pruebas inmediatas en Swagger UI).
    Devuelve la respuesta completa junto con las citas encontradas.
    """
    return service.ask_sync(
        message=payload.message,
        user_id=user_id,
        document_id=payload.document_id,
        match_count=payload.match_count
    )
