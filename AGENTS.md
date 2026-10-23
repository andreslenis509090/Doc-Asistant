# CONTEXTO DEL PROYECTO

Vamos a construir, paso a paso, una aplicación web de "Chat con tus documentos" (RAG pequeño). El usuario sube PDFs, la app los procesa y luego puede hacer preguntas y recibir respuestas basadas SOLO en el contenido de sus documentos, citando documento y página.

## Sobre mí
- Me llamo Andres.
- Domino Python y FastAPI, y trabajo con arquitectura por capas: router → service → repository. Tengo bases de SQL (T-SQL y procedimientos almacenados), pero soy nuevo en Supabase, pgvector, Vercel y RAG.
- Mi idioma principal es el español. Responde SIEMPRE en español; deja los términos técnicos en inglés (chunk, embedding, RLS, etc.) pero explícalos la primera vez.

## Stack
- Backend: Python + FastAPI, con arquitectura router → service → repository.
- Base de datos / Auth / Storage: Supabase (Postgres + pgvector, Supabase Auth, Supabase Storage).
- Frontend: React (Next.js o Vite; propón cuál conviene y por qué antes de decidir).
- Deploy: Vercel (frontend y backend FastAPI como funciones serverless).
- LLM para respuestas: API de Gemini (Google AI Studio, capa gratuita), usando un modelo Flash. No quiero pagar por la API durante el desarrollo.
- Embeddings: también con la API de Gemini (misma clave). Verifica en la documentación oficial qué modelo de embeddings y qué dimensiones soporta, y propón la dimensión para la columna `vector(N)`. Esta decisión se toma en la Etapa 1 y NO debe cambiar después, porque cambiarla obliga a regenerar todos los vectores.

## Arquitectura general
1. El usuario inicia sesión (Supabase Auth).
2. Sube un PDF → se guarda en Supabase Storage.
3. Ingesta: se extrae el texto, se divide en chunks (~500-800 tokens con solapamiento), se generan embeddings y se guardan en la tabla `chunks` (con pgvector), junto con documento y número de página.
4. Chat: la pregunta se convierte en embedding → búsqueda por similitud coseno (función SQL `match_chunks`) filtrada por usuario → los top-k chunks se envían como contexto al LLM → respuesta con streaming y citas (documento + página).
5. Seguridad: Row Level Security (RLS) para que cada usuario solo vea sus documentos y chunks.

## Etapas (las haremos EN ORDEN, una a la vez)
1. Base: proyecto Supabase, extensión `vector`, tablas `documents` y `chunks`, Auth y RLS.
2. Ingesta: extracción de texto del PDF, chunking, embeddings, guardado.
3. Búsqueda y respuesta: `match_chunks`, endpoint `/chat`, prompt con contexto, streaming, citas.
4. Frontend: login, lista de documentos con estado de procesamiento, chat con citas clicables.
5. Pulido y deploy: límites de tamaño y uso, manejo de errores, evaluación con preguntas de prueba, despliegue en Vercel.

## Restricciones importantes
- Vercel usa funciones serverless con límite de tiempo y sin procesos de larga duración: el procesamiento de PDFs grandes no debe depender de una sola petición larga. Ten esto en cuenta en el diseño (procesamiento en segundo plano, tabla de jobs o límite de tamaño inicial).
- Nunca pongas claves o secretos en el código: usa variables de entorno y un `.env.example`.
- Mantén la arquitectura router → service → repository en el backend.

# CÓMO QUIERO QUE TRABAJES

1. Una etapa a la vez. No avances a la siguiente sin que yo lo confirme.
2. Antes de escribir código, dame un mini plan: qué vamos a hacer, qué archivos tocaremos y por qué.
3. EXPLÍCAME CADA COSA que hagas. Para cada decisión, archivo, comando o bloque de código importante, dime:
   - Qué hace.
   - Por qué se hace así (y qué alternativa había).
   - Cómo se conecta con el resto del sistema.
   Explica como a alguien que sabe programar en backend pero es nuevo en esta herramienta o concepto. Usa analogías con lo que ya conozco (capas, SQL, procedimientos almacenados) cuando ayuden.
4. Cuando haya varias opciones válidas (librerías, modelos, estructura), preséntalas con pros y contras y pregúntame antes de decidir.
5. Después de cada paso, dime cómo verificar que funciona (comando, prueba o consulta) antes de continuar.
6. Si algo que te pido es mala idea, riesgoso o poco escalable, dímelo y propón una alternativa en lugar de hacerlo en silencio.
7. Si no estás seguro de algo (versión de una librería, comportamiento de Supabase/Vercel), dilo y verifica en la documentación oficial en lugar de asumir.

# PRIMERA TAREA
Confirma que entendiste el proyecto resumiéndolo en 5-6 líneas con tus palabras, señala cualquier duda o riesgo que veas en el plan, y luego propón el mini plan de la Etapa 1.