from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class CustomerProfile(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: Optional[date] = None  # Changed from str to date
    gender: Optional[str] = None

class CustomerProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None  # Changed from str to date
    gender: Optional[str] = None

class CustomerResponse(CustomerProfile):
    customer_id: int
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AddressBase(BaseModel):
    address_type: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    address_type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None

class AddressResponse(AddressBase):
    address_id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True