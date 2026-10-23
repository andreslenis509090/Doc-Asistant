import io
from typing import Any, Dict, List
from fastapi import HTTPException, status
from pypdf import PdfReader

# Límite de páginas inicial para no saturar timeouts en funciones serverless
MAX_PDF_PAGES = 20
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class PdfService:
    """
    Servicio de extracción de texto y metadatos de documentos PDF.
    
    ¿Qué hace?
    Lee los bytes del PDF en memoria (sin guardarlos en disco temporal)
    y extrae el texto página por página preservando el número de página original.
    
    ¿Por qué se hace así?
    Conservar el número de página exacto es el núcleo de la capacidad de 'citar documento y página'
    que requiere nuestro sistema RAG.
    """

    @staticmethod
    def extract_pages(file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extrae el texto de cada página del PDF.
        Retorna una lista de diccionarios con el formato:
        [{"page_number": 1, "text": "..."}, {"page_number": 2, "text": "..."}]
        """
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo subido no es un PDF válido o está dañado: {str(e)}"
            )

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El PDF no contiene páginas."
            )

        if total_pages > MAX_PDF_PAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El PDF tiene {total_pages} páginas. El límite máximo admitido en esta fase es de {MAX_PDF_PAGES} páginas."
            )

        pages: List[Dict[str, Any]] = []
        total_text_length = 0

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned_text = page_text.strip()
            total_text_length += len(cleaned_text)

            pages.append({
                "page_number": idx + 1,  # Páginas en formato humano (iniciando en 1)
                "text": cleaned_text
            })

        if total_text_length == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo extraer texto del PDF. Podría ser un documento escaneado (solo imágenes) sin capa de texto seleccionable."
            )

        return pages
