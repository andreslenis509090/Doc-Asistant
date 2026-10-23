from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, chat, documents, health

app = FastAPI(
    title="RAG Documents Chat API",
    description="Backend en FastAPI para chat con documentos PDF usando Supabase, pgvector y Gemini",
    version="1.0.0"
)

# Configuración de CORS para permitir conexiones desde el Frontend (React / Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers por capas
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Bienvenido a la API de Chat RAG",
        "docs": "/docs",
        "status": "online"
    }
