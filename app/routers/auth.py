from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.supabase import get_supabase_client
from app.models.schemas import AuthRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthResponse)
def login(
    payload: AuthRequest,
    db: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Inicia sesión en Supabase Auth con email y contraseña.
    Devuelve el JWT access_token para colocarlo en el botón 'Authorize' de Swagger.
    """
    try:
        response = db.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })

        if not response.session or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas o usuario no confirmado."
            )

        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email or payload.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al iniciar sesión: {str(e)}"
        )


@router.post("/register", response_model=AuthResponse)
def register(
    payload: AuthRequest,
    db: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Registra un nuevo usuario en Supabase Auth.
    """
    try:
        response = db.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo registrar el usuario."
            )

        # Si el proyecto requiere confirmación por email, no habrá session inmediata
        token = response.session.access_token if response.session else ""

        return AuthResponse(
            access_token=token,
            user_id=response.user.id,
            email=response.user.email or payload.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en registro: {str(e)}"
        )
