# app/schemas/prescriptions.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PrescriptionUploadRequest(BaseModel):
    product_ids: List[int]  # List of product IDs for which prescription is being uploaded

class PrescriptionItemBase(BaseModel):
    product_id: int
    quantity: int

class PrescriptionItemCreate(PrescriptionItemBase):
    pass

class ProductInfo(BaseModel):
    product_id: int
    name: str
    requires_prescription: bool
    price: float
    
    class Config:
        from_attributes = True

class PrescriptionItemResponse(PrescriptionItemBase):
    prescription_item_id: int
    prescription_id: int
    product: ProductInfo
    created_at: datetime
    
    class Config:
        from_attributes = True

class PrescriptionBase(BaseModel):
    image_url: str

class PrescriptionCreate(PrescriptionBase):
    product_ids: List[int]

class PrescriptionResponse(PrescriptionBase):
    prescription_id: int
    customer_id: int
    status: str
    verified_by: Optional[int] = None
    verification_notes: Optional[str] = None
    uploaded_at: datetime
    verified_at: Optional[datetime] = None
    prescription_items: List[PrescriptionItemResponse] = []
    
    class Config:
        from_attributes = True