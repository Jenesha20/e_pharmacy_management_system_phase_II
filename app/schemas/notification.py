# app/schemas/notifications.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class NotificationType(str, Enum):
    order_update = "order_update"
    prescription_status = "prescription_status"
    refund_update = "refund_update"
    payment_status = "payment_status"
    system = "system"

class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    type: NotificationType
    is_read: bool
    order_id: Optional[int]
    action_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    order_updates: bool = True
    prescription_updates: bool = True
    refund_updates: bool = True
    promotional: bool = False