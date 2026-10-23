from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from supabase import Client
from app.core.supabase import get_current_user_id, get_supabase_client
from app.models.schemas import DocumentResponse, DocumentUploadResponse
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(
    db: Client = Depends(get_supabase_client)
) -> DocumentService:
    repository = DocumentRepository(db)
    return DocumentService(repository)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF para procesar e indexar"),
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """
    Sube un archivo PDF, extrae su texto, genera chunks y embeddings,
    y los almacena en Supabase Storage y PostgreSQL con pgvector.
    
    Requiere autenticación (Bearer JWT token).
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten archivos en formato PDF."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo subido está vacío."
        )

    try:
        result = service.process_and_upload_pdf(
            file_bytes=file_bytes,
            filename=file.filename,
            user_id=user_id
        )

        return DocumentUploadResponse(
            id=result["id"],
            filename=result["filename"],
            status=result["status"],
            page_count=result.get("page_count", 0),
            chunks_count=result.get("chunks_count", 0),
            message="Documento procesado e indexado exitosamente."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento del documento: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service)
) -> List[DocumentResponse]:
    """
    Lista los documentos del usuario autenticado.
    Las políticas RLS aseguran que solo se devuelvan los propios.
    """
    documents = service.get_user_documents()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Obtiene el detalle y estado de un documento por su ID."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin permisos de acceso"
        )
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service)
):
    """Elimina un documento y sus chunks en cascada."""
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin permisos para eliminarlo"
        )
    return {"message": "Documento eliminado exitosamente", "id": document_id}
