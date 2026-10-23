from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Esquema de respuesta para el healthcheck del sistema."""
    status: str
    app_env: str
    supabase_connected: bool
    embedding_model: str
    embedding_dimension: int


class DocumentResponse(BaseModel):
    """DTO para devolver información de un documento."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_size_bytes: int
    page_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    """DTO de respuesta tras subir y procesar un PDF."""
    id: str
    filename: str
    status: str
    page_count: int
    chunks_count: int
    message: str


class AuthRequest(BaseModel):
    """DTO para login y registro de usuarios en Supabase Auth."""
    email: str
    password: str


class AuthResponse(BaseModel):
    """DTO con token de acceso para autorizar peticiones en Swagger y Frontend."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class Citation(BaseModel):
    """Metadatos de cada fragmento citado en la respuesta."""
    document_id: str
    document_name: str
    page_number: int
    similarity: float
    snippet: str


class ChatRequest(BaseModel):
    """Petición de chat enviada por el usuario."""
    message: str
    document_id: Optional[str] = None
    match_count: int = 4


class ChatResponse(BaseModel):
    """Respuesta síncrona alternativa (para clientes que no admiten streaming)."""
    answer: str
    citations: List[Citation]


