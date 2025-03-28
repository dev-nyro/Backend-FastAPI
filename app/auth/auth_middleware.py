from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import verify_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if not credentials:
            print("No credentials provided")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization token"
            )
        
        try:
            print(f"Token received: {credentials.credentials[:20]}...")
            payload = verify_token(credentials.credentials)
            print(f"Token payload: {payload}")
            
            # Validate required claims
            if not all(key in payload for key in ['sub', 'user_id', 'company_id', 'role']):
                print("Missing required claims in token")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token structure"
                )
                
            request.state.user = payload
            return credentials.credentials
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token or expired token"
            )

auth_middleware = JWTBearer()