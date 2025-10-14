from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from enum import Enum
import re

class UserRole(str, Enum):
    admin = "admin"
    customer = "customer"

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone_number: str
    date_of_birth: Optional[str] = None
    gender: Optional[Gender] = None

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    @validator('phone_number')
    def phone_validation(cls, v):
        if not re.match(r'^\+?1?\d{9,15}$', v):
            raise ValueError('Invalid phone number format')
        return v

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: UserRole

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None