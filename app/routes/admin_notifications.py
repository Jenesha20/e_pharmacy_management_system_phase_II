from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Notification, Customer, Order
from app.schemas.admin import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])

@router.get("/", response_model=List[NotificationResponse])
def get_notifications_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    notification_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    recipient_customer_id: Optional[int] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all notifications with filters"""
    query = db.query(Notification)
    
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if recipient_customer_id:
        query = query.filter(Notification.recipient_customer_id == recipient_customer_id)
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification_admin(
    notification: NotificationCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new notification"""
    # Validate recipient if provided
    if notification.recipient_customer_id:
        customer = db.query(Customer).filter(
            Customer.customer_id == notification.recipient_customer_id
        ).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Invalid customer ID")
    
    # Validate order if provided
    if notification.order_id:
        order = db.query(Order).filter(Order.order_id == notification.order_id).first()
        if not order:
            raise HTTPException(status_code=400, detail="Invalid order ID")
    
    new_notification = Notification(**notification.dict())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

@router.post("/broadcast")
def broadcast_notification(
    notification: NotificationCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Send notification to all customers (broadcast)"""
    try:
        # Get all active customers
        customers = db.query(Customer).filter(Customer.role == "customer").all()
        
        notifications_created = 0
        for customer in customers:
            broadcast_notification = Notification(
                title=notification.title,
                message=notification.message,
                type=notification.type,
                recipient_customer_id=customer.customer_id,
                order_id=notification.order_id,
                action_url=notification.action_url
            )
            db.add(broadcast_notification)
            notifications_created += 1
        
        db.commit()
        
        return {
            "message": f"Notification broadcasted to {notifications_created} customers",
            "notifications_sent": notifications_created
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Broadcast failed: {str(e)}"
        )

@router.patch("/{notification_id}/mark-read")
def mark_notification_read(
    notification_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}

@router.get("/stats/summary")
def get_notifications_summary(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get notifications statistics summary"""
    total_notifications = db.query(Notification).count()
    unread_notifications = db.query(Notification).filter(Notification.is_read == False).count()
    read_notifications = total_notifications - unread_notifications
    
    # Notifications by type
    type_counts = db.query(
        Notification.type,
        func.count(Notification.notification_id).label('count')
    ).group_by(Notification.type).all()
    
    # Recent notifications (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_notifications = db.query(Notification).filter(
        Notification.created_at >= week_ago
    ).count()
    
    return {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "read_notifications": read_notifications,
        "recent_notifications_7_days": recent_notifications,
        "type_distribution": [
            {"type": notif_type, "count": count}
            for notif_type, count in type_counts
        ]
    }