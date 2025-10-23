from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.users import AddressResponse

class OrderItemResponse(BaseModel):
    order_item_id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    requires_prescription: bool
    prescription_verified: bool
    created_at: datetime
    product_name: str
    product_image: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    customer_id: int
    order_date: datetime
    total_amount: float
    shipping_charges: float
    tax_amount: float
    discount_amount: float
    final_amount: float
    order_type: str
    payment_method: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderWithDetails(OrderResponse):
    shipping_address: Optional[AddressResponse] = None
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    shipping_address_id: int
    order_type: str = "delivery"
    payment_method: str

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None

