from typing import Any, Dict, List, Optional
from supabase import Client


class DocumentRepository:
    """
    Repositorio de persistencia para documentos y chunks.
    
    Analogía SQL:
    Esta clase encapsula el acceso directo a datos:
    - Tablas: `documents`, `chunks`.
    - Supabase Storage: bucket `documents`.
    - Stored procedure / Función SQL: `match_chunks`.
    """

    def __init__(self, db: Client):
        self.db = db

    def ping(self) -> bool:
        """Verifica conectividad básica contra la base de datos de Supabase."""
        try:
            response = self.db.table("documents").select("id").limit(1).execute()
            return response is not None
        except Exception:
            return False

    def list_user_documents(self) -> List[Dict[str, Any]]:
        """
        Obtiene los documentos del usuario.
        Gracias a RLS en Supabase, automáticamente solo retorna los del usuario autenticado.
        """
        response = self.db.table("documents").select("*").order("created_at", desc=True).execute()
        return response.data or []

    def get_documents_map(self) -> Dict[str, str]:
        """
        Obtiene un mapa {document_id: filename} para asociar rápidamente
        los nombres de archivo reales a los fragmentos encontrados por match_chunks.
        """
        docs = self.list_user_documents()
        return {d["id"]: d["filename"] for d in docs}

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un documento específico si pertenece al usuario (garantizado por RLS)."""
        response = self.db.table("documents").select("*").eq("id", document_id).execute()
        return response.data[0] if response.data else None

    def upload_file_to_storage(self, storage_path: str, file_bytes: bytes) -> str:
        """
        Guarda el archivo binario PDF en el bucket 'documents' de Supabase Storage.
        storage_path tendrá el formato: '{user_id}/{document_id}.pdf' para cumplir con las políticas RLS.
        """
        response = self.db.storage.from_("documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        return storage_path

    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserta un nuevo registro en la tabla `documents` con estado inicial 'pending' o 'processing'."""
        response = self.db.table("documents").insert(document_data).execute()
        if not response.data:
            raise RuntimeError("No se pudo crear el registro del documento en la base de datos.")
        return response.data[0]

    def update_document(self, document_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza campos del documento (como status, page_count o error_message)."""
        response = self.db.table("documents").update(update_data).eq("id", document_id).execute()
        if not response.data:
            raise RuntimeError(f"No se pudo actualizar el documento con id {document_id}")
        return response.data[0]

    def delete_document(self, document_id: str) -> bool:
        """
        Elimina el documento y su archivo físico en Storage.
        En PostgreSQL, la restricción ON DELETE CASCADE borra automáticamente todos los chunks asociados.
        """
        doc = self.get_document_by_id(document_id)
        if not doc:
            return False

        # 1. Intentar borrar archivo físico en Storage
        storage_path = doc.get("storage_path")
        if storage_path:
            try:
                self.db.storage.from_("documents").remove([storage_path])
            except Exception:
                pass

        # 2. Borrar fila en tabla documents
        self.db.table("documents").delete().eq("id", document_id).execute()
        return True

    def insert_chunks(self, chunks_data: List[Dict[str, Any]]) -> None:
        """
        Inserta en bloque (bulk insert) todos los fragmentos y sus vectores en la tabla `chunks`.
        """
        if not chunks_data:
            return
        self.db.table("chunks").insert(chunks_data).execute()

    def match_similar_chunks(
        self,
        query_embedding: List[float],
        match_count: int = 5,
        match_threshold: float = 0.3,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta el stored procedure 'match_chunks' en PostgreSQL vía RPC.
        Aplica filtro explícito por user_id y similitud coseno sobre el índice HNSW.
        """
        params = {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "match_threshold": match_threshold,
            "filter_user_id": user_id
        }
        response = self.db.rpc("match_chunks", params).execute()
        return response.data or []
