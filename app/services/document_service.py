import uuid
from typing import Any, Dict, List, Optional
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PdfService


class DocumentService:
    """
    Servicio de lógica de negocio para documentos y RAG.
    
    ¿Qué hace?
    Orquesta todo el flujo de ingesta:
    1. Extrae páginas y valida límites del PDF.
    2. Sube el binario a Supabase Storage con la ruta {user_id}/{document_id}.pdf.
    3. Registra el documento en la tabla `documents` con status='processing'.
    4. Divide el contenido en chunks con solapamiento por página.
    5. Genera y normaliza los embeddings en lote con Gemini.
    6. Guarda los chunks y vectores en la tabla `chunks` (pgvector).
    7. Marca el documento como 'completed'.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        pdf_service: Optional[PdfService] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.repository = repository
        self.pdf_service = pdf_service or PdfService()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()

    def check_health(self) -> bool:
        """Verifica la conectividad con la base de datos."""
        return self.repository.ping()

    def get_user_documents(self) -> List[Dict[str, Any]]:
        """Recupera la lista de documentos del usuario (filtrado por RLS)."""
        return self.repository.list_user_documents()

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Recupera un documento específico validando su propiedad vía RLS."""
        return self.repository.get_document_by_id(document_id)

    def delete_document(self, document_id: str) -> bool:
        """Elimina un documento y sus chunks en cascada."""
        return self.repository.delete_document(document_id)

    def process_and_upload_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Ejecuta la cadena completa de ingesta de un PDF.
        """
        # 1. Extraer páginas y validar límites
        pages = self.pdf_service.extract_pages(file_bytes)
        page_count = len(pages)

        document_id = str(uuid.uuid4())
        # Sanitizar nombre de archivo para evitar problemas en URL de Storage
        safe_filename = filename.replace(" ", "_")
        storage_path = f"{user_id}/{document_id}_{safe_filename}"

        # 2. Subir archivo a Supabase Storage
        self.repository.upload_file_to_storage(storage_path, file_bytes)

        # 3. Crear el registro en tabla documents con status 'processing'
        doc_record = self.repository.create_document({
            "id": document_id,
            "user_id": user_id,
            "filename": filename,
            "storage_path": storage_path,
            "file_size_bytes": len(file_bytes),
            "page_count": page_count,
            "status": "processing"
        })

        try:
            # 4. Fragmentar en chunks por página
            chunks = self.chunking_service.create_chunks(pages)
            if not chunks:
                raise ValueError("El proceso de chunking no generó ningún fragmento válido.")

            # 5. Generar embeddings en lote con Gemini (output_dim=768, normalizado L2)
            chunk_texts = [c["content"] for c in chunks]
            embeddings = self.embedding_service.generate_document_embeddings(chunk_texts)

            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Discrepancia en embeddings: se esperaban {len(chunks)} y se recibieron {len(embeddings)}."
                )

            # 6. Preparar los datos para inserción masiva en tabla `chunks`
            chunks_to_insert = []
            for c, emb in zip(chunks, embeddings):
                chunks_to_insert.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_index": c["chunk_index"],
                    "page_number": c["page_number"],
                    "content": c["content"],
                    "token_count": c["token_count"],
                    "embedding": emb
                })

            # Inserción en bloque en PostgreSQL (con índice HNSW)
            self.repository.insert_chunks(chunks_to_insert)

            # 7. Actualizar estado del documento a 'completed'
            updated_doc = self.repository.update_document(
                document_id=document_id,
                update_data={"status": "completed"}
            )
            updated_doc["chunks_count"] = len(chunks)
            return updated_doc

        except Exception as e:
            # Si algo falla en el proceso, registramos el error en la base de datos
            self.repository.update_document(
                document_id=document_id,
                update_data={"status": "failed", "error_message": str(e)}
            )
            raise e
