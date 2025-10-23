# app/services/notification_service.py (Updated)
from sqlalchemy.orm import Session
from app.models.models import Notification, RefundPolicy, RefundStatus
from datetime import datetime

class NotificationService:
    
    @staticmethod
    async def create_refund_notification(refund, db: Session):
        """
        Create notification for refund status updates using your ENUM
        """
        title = "Refund Update"
        
        # Map refund policy to user-friendly messages
        policy_messages = {
            RefundPolicy.full: "full refund",
            RefundPolicy.partial: "partial refund",
            RefundPolicy.no_refund: "no refund"
        }
        
        status_messages = {
            RefundStatus.pending: "is pending review",
            RefundStatus.completed: "has been processed",
            RefundStatus.failed: "has failed"
        }
        
        policy_message = policy_messages.get(refund.refund_policy, "refund")
        status_message = status_messages.get(refund.status, "is being processed")
        
        message = (
            f"Your {policy_message} request for Order #{refund.order_id} "
            f"{status_message}. Amount: ${refund.amount:.2f}"
        )
        
        # Create the notification
        notification = Notification(
            title=title,
            message=message,
            type="refund_update",
            recipient_customer_id=refund.order.customer_id,
            order_id=refund.order_id,
            created_at=datetime.now()
        )
        
        db.add(notification)
        db.commit()
    
    @staticmethod
    async def create_order_notification(order, status: str, db: Session):
        """
        Create notification for order status updates
        """
        title = "Order Update"
        status_messages = {
            "confirmed": "has been confirmed",
            "processing": "is being processed", 
            "ready": "is ready for pickup/delivery",
            "shipped": "has been shipped",
            "delivered": "has been delivered",
            "cancelled": "has been cancelled"
        }
        
        message = f"Your order #{order.order_number} {status_messages.get(status, 'has been updated')}"
        
        notification = Notification(
            title=title,
            message=message,
            type="order_update",
            recipient_customer_id=order.customer_id,
            order_id=order.order_id,
            created_at=datetime.now()
        )
        
        db.add(notification)
        db.commit()

# Helper function
async def create_refund_notification(refund, db: Session):
    await NotificationService.create_refund_notification(refund, db)