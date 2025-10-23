# app/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Customer, Notification
from app.schemas.notification import NotificationResponse, NotificationPreferences
from app.middleware.auth import get_current_customer

router = APIRouter(prefix="/notifications", tags=["Customer Notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(
        Notification.recipient_customer_id == current_customer.customer_id
    )
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return notifications

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.recipient_customer_id == current_customer.customer_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.now()
    
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.put("/read-all")
async def mark_all_notifications_read(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.recipient_customer_id == current_customer.customer_id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.now()})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}

@router.get("/unread-count")
async def get_unread_count(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.recipient_customer_id == current_customer.customer_id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.recipient_customer_id == current_customer.customer_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}