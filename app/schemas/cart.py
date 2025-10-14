from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(CartItemBase):
    cart_item_id: int
    customer_id: int
    added_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CartItemWithProduct(CartItemResponse):
    product_name: str
    product_price: float
    requires_prescription: bool
    image_url: Optional[str]
    stock_quantity: int

    class Config:
        from_attributes = True