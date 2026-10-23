from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client, ClientOptions
from app.core.config import settings

# Extractor de token Bearer desde los headers HTTP: Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)


def get_supabase_client(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Client:
    """
    Inyección de dependencias para FastAPI:
    Crea un cliente Supabase con la ANON_KEY y propaga el JWT del usuario autenticado.
    
    ¿Por qué se hace así?
    Al llamar `client.postgrest.auth(token)`, PostgREST reconoce a auth.uid() en PostgreSQL,
    haciendo que las políticas RLS (Row Level Security) se apliquen automáticamente.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase no está configurado correctamente en el archivo .env"
        )

    # Configuramos opciones del cliente para propagar el JWT a Storage y PostgREST
    options = None
    if credentials and credentials.credentials:
        options = ClientOptions(headers={"Authorization": f"Bearer {credentials.credentials}"})

    client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, options=options)

    if credentials and credentials.credentials:
        client.postgrest.auth(credentials.credentials)

    return client


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Client = Depends(get_supabase_client)
) -> str:
    """
    Dependencia de seguridad:
    Verifica que el JWT sea válido a través de Supabase Auth y retorna el user_id (UUID).
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere cabecera 'Authorization: Bearer <access_token>' para esta acción.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_response = db.auth.get_user(credentials.credentials)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticación inválido o expirado."
            )
        return user_response.user.id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validando sesión del usuario: {str(e)}"
        )


def get_admin_supabase_client() -> Client:
    """
    Cliente administrativo con SERVICE_ROLE_KEY (Superusuario / Bypass RLS).
    
    ¡ATENCIÓN DE SEGURIDAD!
    Este cliente se salta todas las políticas RLS de PostgreSQL.
    SOLO debe usarse en tareas internas del sistema donde NO hay un usuario conectado.
    NUNCA usarlo para consultas o escrituras directas solicitadas por usuarios finales.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_SERVICE_ROLE_KEY no está configurada"
        )

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
