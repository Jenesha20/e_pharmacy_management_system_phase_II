from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

# This creates the standard OAuth2 scheme that Swagger UI understands
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # Don't automatically raise errors
)

def get_oauth2_scheme():
    return OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")