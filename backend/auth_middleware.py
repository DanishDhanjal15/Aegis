from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin_config import verify_firebase_token

# Security scheme for extracting Bearer token
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependency to verify Firebase authentication token and get current user.
    
    Usage:
        @app.get("/protected-route")
        async def protected_route(user = Depends(get_current_user)):
            # user contains decoded token with uid, email, etc.
            return {"message": f"Hello {user['email']}"}
    
    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        
    Returns:
        dict: Decoded token containing user information
        
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Verify the token with Firebase
        decoded_token = verify_firebase_token(token)
        
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Security(security, auto_error=False)):
    """
    Optional authentication dependency. Returns user if authenticated, None otherwise.
    
    Usage:
        @app.get("/optional-auth-route")
        async def optional_route(user = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user['email']}"}
            else:
                return {"message": "Hello guest"}
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        return decoded_token
    except Exception:
        return None
