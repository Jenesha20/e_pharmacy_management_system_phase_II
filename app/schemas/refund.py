# app/schemas/refunds.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional
from app.models.models import RefundPolicy  # Import your existing ENUM

class RefundStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class RefundRequest(BaseModel):
    order_id: int
    reason: str

class RefundResponse(BaseModel):
    refund_id: int
    order_id: int
    amount: float
    cancellation_fee: float
    refund_policy: RefundPolicy
    reason: Optional[str]
    status: RefundStatus
    refund_method: Optional[str]
    refund_upi_id: Optional[str]
    bank_account_last4: Optional[str]
    bank_name: Optional[str]
    account_holder_name: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True