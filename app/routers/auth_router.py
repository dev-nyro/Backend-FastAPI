from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from ..auth.jwt_handler import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..models.user_model import User, UserAuth, Token, UserCreate  # Added UserCreate
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from uuid import UUID
from passlib.context import CryptContext

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Fix the tokenUrl to match the full path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autenticación de usuario
    
    ### Descripción
    Autentica un usuario y retorna un token JWT.
    
    ### Parámetros
    - **username**: Email del usuario
    - **password**: Contraseña del usuario
    
    ### Retorna
    - **access_token**: Token JWT para autenticación
    - **token_type**: Tipo de token (bearer)
    """
    supabase = get_supabase_client(use_service_role=True)
    
    try:
        print(f"Attempting login for user: {form_data.username}")  # Debug info
        user_query = supabase.table('users').select("*").eq('email', form_data.username).execute()
        
        if not user_query.data:
            print("User not found")  # Debug info
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_query.data[0]
        print(f"Found user data: {user}")  # Debug info
        
        # Verify password using pwd_context
        if not pwd_context.verify(form_data.password, user['hashed_password']):
            print("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token with all necessary data
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user['email'],
            "user_id": str(user['id']),  # Ensure it's a string
            "company_id": str(user['company_id']),  # Ensure it's a string
            "role": user['role']  # Make sure role is included
        }
        print(f"Creating token with data: {token_data}")  # Debug info
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        # Remove sensitive data
        user_response = dict(user)
        user_response.pop('hashed_password', None)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Login error: {str(e)}")  # For debugging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """
    Registro de nuevo usuario
    
    ### Descripción
    Crea un nuevo usuario en el sistema y retorna un token JWT.
    
    ### Parámetros
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    - **full_name**: Nombre completo
    - **company_id**: ID de la empresa (opcional)
    
    ### Retorna
    - **access_token**: Token JWT para autenticación
    - **token_type**: Tipo de token (bearer)
    """
    supabase = get_supabase_client(use_service_role=True)  # Changed to use service role
    
    try:
        # Check if company exists - use str for UUID comparison
        company = supabase.table('companies').select("*").eq('id', str(user_data.company_id)).execute()
        if not company.data:
            raise HTTPException(
                status_code=400,
                detail="Invalid company_id"
            )
        
        # Check if user exists
        existing = supabase.table('users').select("*").eq('email', user_data.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create new user with service role
        new_user = {
            "email": user_data.email,
            "hashed_password": pwd_context.hash(user_data.password),  # Hash the password properly
            "full_name": user_data.full_name,
            "role": user_data.role,
            "company_id": str(user_data.company_id),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"Attempting to insert user: {new_user}")
        response = supabase.table('users').insert(new_user).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create user"
            )
            
        user = response.data[0]
        print(f"User created: {user}")
        
        # Create access token with company_id
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user['email'],
                "user_id": user['id'],
                "company_id": str(user['company_id']),
                "role": user['role']  # Include role in token
            },
            expires_delta=access_token_expires
        )
        
        # Remove sensitive data
        user.pop('hashed_password', None)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Register error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/me", dependencies=[Depends(auth_middleware)])
async def get_current_user(request: Request):
    """
    Test endpoint to verify token and get current user info
    """
    user_payload = request.state.user
    return {
        "message": "Token is valid",
        "user": user_payload
    }