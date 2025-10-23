from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

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

class ProductResponse(ProductBase):
    product_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductDetailResponse(ProductResponse):
    category_name: str
    in_stock: int
    stock_quantity: int
    low_stock: bool

    class Config:
        from_attributes = True