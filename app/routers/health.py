from fastapi import APIRouter, Depends
from supabase import Client
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.models.schemas import HealthResponse
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService

router = APIRouter(prefix="/health", tags=["Health"])


def get_document_service(
    db: Client = Depends(get_supabase_client)
) -> DocumentService:
    """Fábrica de inyección de dependencias para el servicio de documentos."""
    repository = DocumentRepository(db)
    return DocumentService(repository)


@router.get("", response_model=HealthResponse)
def health_check(
    service: DocumentService = Depends(get_document_service)
) -> HealthResponse:
    """
    Endpoint de verificación de estado del backend.
    Comprueba conectividad con Supabase y expone la configuración activa.
    """
    is_connected = service.check_health()

    return HealthResponse(
        status="ok" if is_connected else "degraded",
        app_env=settings.APP_ENV,
        supabase_connected=is_connected,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_dimension=settings.EMBEDDING_DIMENSION
    )
