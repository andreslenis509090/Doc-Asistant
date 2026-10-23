import json
from typing import AsyncGenerator, Dict, Generator, List, Optional
from google import genai
from app.core.config import settings
from app.models.schemas import ChatResponse, Citation
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService


class ChatService:
    """
    Servicio RAG de Búsqueda y Generación Aumentada.
    
    ¿Qué hace?
    1. Retrieval: Convierte la pregunta en vector y busca los chunks más similares con pgvector.
    2. Augmentation: Concatena los fragmentos y las fuentes en un prompt blindado contra alucinaciones.
    3. Generation: Llama a Gemini Flash con streaming y emite Server-Sent Events (SSE) con las citas.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.repository = repository
        self.embedding_service = embedding_service or EmbeddingService()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

    def _retrieve_context_and_citations(
        self,
        message: str,
        user_id: str,
        document_id: Optional[str] = None,
        match_count: int = 4
    ) -> tuple[List[Dict], List[Citation]]:
        """Recupera los chunks relevantes y genera la lista tipada de citas."""
        # 1. Vectorizar la pregunta del usuario con RETRIEVAL_QUERY
        query_embedding = self.embedding_service.generate_query_embedding(message)

        # 2. Búsqueda vectorial en Supabase con filtro de user_id y similitud coseno
        raw_chunks = self.repository.match_similar_chunks(
            query_embedding=query_embedding,
            match_count=match_count,
            match_threshold=0.35,
            user_id=user_id
        )

        # Si el usuario eligió filtrar por un documento específico
        if document_id:
            raw_chunks = [c for c in raw_chunks if c["document_id"] == document_id]

        docs_map = self.repository.get_documents_map()

        citations: List[Citation] = []
        for ch in raw_chunks:
            doc_name = docs_map.get(ch["document_id"], "Documento")
            citations.append(
                Citation(
                    document_id=ch["document_id"],
                    document_name=doc_name,
                    page_number=ch["page_number"],
                    similarity=round(ch["similarity"], 4),
                    snippet=ch["content"][:200]
                )
            )

        return raw_chunks, citations

    def stream_chat(
        self,
        message: str,
        user_id: str,
        document_id: Optional[str] = None,
        match_count: int = 4
    ) -> Generator[str, None, None]:
        """
        Generador síncrono para StreamingResponse (formato SSE: Server-Sent Events).
        
        Protocolo de eventos enviados al Frontend:
        1. {"type": "citations", "citations": [...]}  -> fuentes encontradas
        2. {"type": "token", "content": "..."}        -> fragmentos de texto en tiempo real
        3. {"type": "done"}                           -> fin del streaming
        """
        raw_chunks, citations = self._retrieve_context_and_citations(
            message=message,
            user_id=user_id,
            document_id=document_id,
            match_count=match_count
        )

        # 1. Enviar primero las citas para que el frontend las dibuje como etiquetas/badges
        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]}, ensure_ascii=False)}\n\n"

        # 2. Si no hubo coincidencias con suficiente similitud
        if not raw_chunks:
            no_info_msg = (
                "No encontré información relevante sobre tu consulta en tus documentos subidos. "
                "Por favor intenta reformular tu pregunta o asegúrate de que el documento correspondiente esté cargado."
            )
            yield f"data: {json.dumps({'type': 'token', 'content': no_info_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # 3. Construir el contexto documental para el LLM
        context_parts = []
        for idx, ch in enumerate(raw_chunks, start=1):
            doc_name = citations[idx - 1].document_name
            context_parts.append(
                f"--- FRAGMENTO [{idx}] (Documento: \"{doc_name}\", Página {ch['page_number']}) ---\n"
                f"{ch['content']}\n"
            )
        context_text = "\n".join(context_parts)

        # 4. Prompt blindado con instrucciones estrictas de grounding y citas
        prompt = f"""Eres un asistente de inteligencia artificial especializado en responder preguntas basadas estrictamente en documentos PDF provistos.

CONTEXTO RECUPERADO DE LOS DOCUMENTOS DEL USUARIO:
{context_text}

PREGUNTA DEL USUARIO:
{message}

INSTRUCCIONES OBLIGATORIAS:
1. Responde a la pregunta basándote ÚNICA Y EXCLUSIVAMENTE en el CONTEXTO anterior.
2. NO utilices información externa ni asumas datos que no estén expresamente dichos.
3. Si la respuesta no se encuentra en el contexto, indica con cortesía: "No encontré suficiente información sobre eso en tus documentos".
4. SIEMPRE debes incluir citas exactas en tu respuesta para respaldar tus afirmaciones, indicando el documento y la página en formato: `[NombreDelDocumento, Pág. X]`.
5. Responde en español con un tono claro, directo y profesional, usando formato markdown (viñetas, negritas) cuando sea apropiado."""

        # 5. Streaming con Gemini Flash
        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt
            )

            for chunk in response_stream:
                if chunk.text:
                    payload = {"type": "token", "content": chunk.text}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_payload = {"type": "error", "message": f"Error durante la generación: {str(e)}"}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

        # 6. Evento de cierre
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def ask_sync(
        self,
        message: str,
        user_id: str,
        document_id: Optional[str] = None,
        match_count: int = 4
    ) -> ChatResponse:
        """Versión síncrona sin streaming (útil para pruebas en Swagger o clientes REST tradicionales)."""
        full_text = ""
        citations_list: List[Citation] = []

        for sse_event in self.stream_chat(message, user_id, document_id, match_count):
            if sse_event.startswith("data: "):
                event_data = json.loads(sse_event[6:].strip())
                if event_data.get("type") == "citations":
                    citations_list = [Citation(**c) for c in event_data.get("citations", [])]
                elif event_data.get("type") == "token":
                    full_text += event_data.get("content", "")

        return ChatResponse(answer=full_text, citations=citations_list)
