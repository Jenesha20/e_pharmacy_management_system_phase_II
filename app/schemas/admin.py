from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    category_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    category_id: int
    manufacturer: str
    requires_prescription: bool = False
    hsn_code: float
    gst_rate: float
    price: float
    cost_price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    manufacturer: Optional[str] = None
    requires_prescription: Optional[bool] = None
    hsn_code: Optional[float] = None
    gst_rate: Optional[float] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductWithCategory(ProductResponse):
    category_name: str
    
    class Config:
        from_attributes = True