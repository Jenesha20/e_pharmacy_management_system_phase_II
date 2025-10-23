# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import JWTError, jwt
# from sqlalchemy.orm import Session
# from app.database import get_db
# from app.models.models import Customer, UserRole
# from config import SECRET_KEY, ALGORITHM
# from app.schemas.auth import TokenData

# security = HTTPBearer()

# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: int = payload.get("user_id")
#         role: str = payload.get("role")
        
#         if user_id is None or role is None:
#             raise credentials_exception
            
#         token_data = TokenData(user_id=user_id, role=role)
#     except JWTError:
#         raise credentials_exception
    
#     user = db.query(Customer).filter(Customer.customer_id == user_id).first()
#     if user is None:
#         raise credentials_exception
        
#     return user

# async def get_current_admin(current_user: Customer = Depends(get_current_user)):
#     # Fix: Compare with Enum value or convert to string
#     if current_user.role != UserRole.admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions. Admin access required."
#         )
#     return current_user

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Customer, UserRole
from config import SECRET_KEY, ALGORITHM
from app.schemas.auth import TokenData

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception
    
    user = db.query(Customer).filter(Customer.customer_id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_admin(current_user: Customer = Depends(get_current_user)):
    # Fix: Compare with Enum value or convert to string
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user

# ADD THIS FUNCTION - Customer-specific authentication
async def get_current_customer(current_user: Customer = Depends(get_current_user)):
    """Ensure the current user is a customer, not an admin"""
    if current_user.role != UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available for customers. Admin access not allowed."
        )
    return current_user