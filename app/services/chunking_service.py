from typing import Any, Dict, List


class ChunkingService:
    """
    Servicio de fragmentación de texto (Chunking).
    
    ¿Qué hace?
    Toma el texto extraído página por página y lo divide en fragmentos manejables
    (~500-800 tokens con solapamiento), asociando siempre cada chunk a su página de origen.
    
    ¿Por qué se hace así?
    1. Si un chunk es demasiado largo, el embedding pierde especificidad (se diluye el tema).
    2. Si un chunk es demasiado corto, carece de contexto suficiente para que el LLM responda.
    3. El solapamiento (overlap) asegura que frases o conceptos que caen en el corte
       no queden incompletos o sin sentido en ambos lados.
    """

    def __init__(
        self,
        target_chunk_chars: int = 1800,  # ~450 tokens aproximados en español
        overlap_chars: int = 250         # ~60 tokens de solapamiento
    ):
        self.target_chunk_chars = target_chunk_chars
        self.overlap_chars = overlap_chars

    def create_chunks(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera los chunks manteniendo la trazabilidad del número de página.
        Retorna lista de:
        {
            "chunk_index": 0,
            "page_number": 1,
            "content": "...",
            "token_count": 450
        }
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_index = 0

        for page in pages:
            page_number = page["page_number"]
            page_text = page["text"]

            # Si la página está vacía o solo tiene espacios, la ignoramos
            if not page_text:
                continue

            # Si el texto de la página cabe en un solo chunk, lo tomamos directamente
            if len(page_text) <= self.target_chunk_chars:
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "page_number": page_number,
                    "content": page_text,
                    "token_count": self._estimate_tokens(page_text)
                })
                global_chunk_index += 1
                continue

            # Si el texto es más largo, aplicamos ventana deslizante con solapamiento
            page_chunks = self._split_text_with_overlap(page_text)
            for chunk_content in page_chunks:
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "page_number": page_number,
                    "content": chunk_content,
                    "token_count": self._estimate_tokens(chunk_content)
                })
                global_chunk_index += 1

        return chunks

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Divide el texto buscando cortes naturales (puntos, saltos de línea) con solapamiento."""
        result: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.target_chunk_chars

            if end >= text_len:
                # Llegamos al final del texto
                chunk = text[start:].strip()
                if chunk:
                    result.append(chunk)
                break

            # Intentar buscar un corte natural hacia atrás (punto o salto de línea)
            cut_point = text.rfind("\n\n", start, end)
            if cut_point == -1:
                cut_point = text.rfind(". ", start, end)
            if cut_point == -1:
                cut_point = text.rfind("\n", start, end)
            if cut_point == -1:
                cut_point = text.rfind(" ", start, end)

            # Si no encontramos ningún separador razonable, cortamos forzosamente en el límite
            if cut_point == -1 or cut_point <= start:
                cut_point = end

            chunk = text[start:cut_point].strip()
            if chunk:
                result.append(chunk)

            # Avanzamos el inicio restando el solapamiento para no perder contexto
            start = max(start + 1, cut_point - self.overlap_chars)

        return result

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimación estándar: en español ~4 caracteres equivalen aproximadamente a 1 token."""
        return max(1, len(text) // 4)
