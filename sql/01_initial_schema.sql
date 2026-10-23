-- ==============================================================================
-- ETAPA 1: ESQUEMA BASE DE DATOS PARA RAG (Supabase + pgvector)
-- ==============================================================================

-- 1. Habilitar la extensión pgvector
-- Proporciona el tipo de dato `vector` y operadores de distancia (como <=> para coseno).
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabla `documents`: Registro de archivos PDF subidos por cada usuario
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    page_count INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Comentarios explicativos en columnas
COMMENT ON TABLE public.documents IS 'Metadatos de documentos PDF subidos por los usuarios';
COMMENT ON COLUMN public.documents.status IS 'pending: subido, processing: chunking/embeddings en curso, completed: listo para chat, failed: error';

-- 3. Tabla `chunks`: Fragmentos de texto con sus vectores de embedding
-- Usamos vector(768) correspondiente a gemini-embedding-001 con output_dimensionality=768
CREATE TABLE IF NOT EXISTS public.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    embedding VECTOR(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.chunks IS 'Fragmentos de texto y embeddings vectoriales de 768 dimensiones';

-- 4. Índices para rendimiento en búsquedas relacionales
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON public.chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_user_id ON public.chunks(user_id);

-- 5. Índice vectorial HNSW (Hierarchical Navigable Small World)
-- Usa vector_cosine_ops para optimizar búsquedas por similitud coseno (<=>).
-- HNSW ofrece velocidad de búsqueda sublineal O(log N) sin necesidad de reentrenar tras inserciones.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON public.chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 6. Configuración de Row Level Security (RLS)
-- Garantiza que a nivel del motor PostgreSQL ningún usuario pueda ver o modificar datos de otro.
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

-- Políticas para `documents`
CREATE POLICY "Los usuarios solo ven sus propios documentos"
ON public.documents FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Los usuarios solo insertan sus propios documentos"
ON public.documents FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Los usuarios solo actualizan sus propios documentos"
ON public.documents FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Los usuarios solo eliminan sus propios documentos"
ON public.documents FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Políticas para `chunks`
CREATE POLICY "Los usuarios solo ven sus propios chunks"
ON public.chunks FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Los usuarios solo insertan sus propios chunks"
ON public.chunks FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Los usuarios solo eliminan sus propios chunks"
ON public.chunks FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- 7. Función almacenada `match_chunks`
-- Realiza la búsqueda semántica por similitud coseno.
-- Recibe el vector de la consulta, la cantidad máxima de resultados, un umbral mínimo de similitud y el user_id.
-- Seguridad: aplica el filtro por user_id y respeta la sesión auth.uid() de RLS si está presente.
CREATE OR REPLACE FUNCTION public.match_chunks (
    query_embedding VECTOR(768),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.3,
    filter_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    page_number INT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
SECURITY INVOKER -- Se ejecuta con los privilegios del usuario llamante (aplica RLS)
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.page_number,
        c.content,
        (1 - (c.embedding <=> query_embedding))::FLOAT AS similarity
    FROM public.chunks c
    WHERE 
        -- Filtro explícito de usuario si se proporciona
        (filter_user_id IS NULL OR c.user_id = filter_user_id)
        -- Si hay una sesión JWT activa en Supabase, forzar que coincida con auth.uid()
        AND (auth.uid() IS NULL OR c.user_id = auth.uid())
        -- Filtrar por similitud mínima (1 - distancia_coseno)
        AND (1 - (c.embedding <=> query_embedding)) > match_threshold
    ORDER BY c.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION public.match_chunks IS 'Búsqueda vectorial de chunks por similitud coseno con aislamiento estricto por usuario';
