from typing import List
from google import genai
from google.genai import types
import numpy as np
from app.core.config import settings


class EmbeddingService:
    """
    Servicio de generación de vectores semánticos con la API de Gemini.
    
    ¿Qué hace?
    1. Usa el modelo oficial `gemini-embedding-001`.
    2. Trunca la salida a 768 dimensiones vía MRL (Matryoshka Representation Learning).
    3. Normaliza obligatoriamente los vectores resultantes mediante norma L2 (longitud euclidiana = 1.0).
    4. Envía los textos en lotes (batching) para optimizar tiempo y cuota de peticiones.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    def generate_document_embeddings(self, texts: List[str], batch_size: int = 30) -> List[List[float]]:
        """
        Genera embeddings para una lista de chunks de texto usando RETRIEVAL_DOCUMENT.
        Procesa en lotes para no exceder límites de payload ni tiempos de espera.
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        # Procesamiento en lotes (chunks de 30 textos por llamada)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.dimension
                )
            )

            # Extraer y normalizar cada vector del lote
            for item in response.embeddings:
                normalized_vector = self._normalize_l2(item.values)
                all_embeddings.append(normalized_vector)

        return all_embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Genera el embedding para la pregunta del usuario en el chat usando RETRIEVAL_QUERY.
        """
        response = self.client.models.embed_content(
            model=self.model,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.dimension
            )
        )

        raw_vector = response.embeddings[0].values
        return self._normalize_l2(raw_vector)

    @staticmethod
    def _normalize_l2(vector: List[float]) -> List[float]:
        """
        Normalización L2 obligatoria:
        v_norm = v / ||v||
        
        Garantiza que el producto escalar (o distancia coseno en pgvector) funcione correctamente
        cuando output_dimensionality < 3072.
        """
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()
