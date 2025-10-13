from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None

class CustomerCreate(CustomerBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class CustomerResponse(CustomerBase):
    customer_id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: CustomerResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str