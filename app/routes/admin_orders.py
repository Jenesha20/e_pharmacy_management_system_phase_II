from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Order, OrderItem, Customer, Product, Prescription
from app.schemas.admin import (
    OrderResponse, OrderUpdate, OrderWithCustomer, OrderItemResponse
)

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])

@router.get("/", response_model=List[OrderWithCustomer])
def get_orders_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    order_type: Optional[str] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all orders with filters"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if order_type:
        query = query.filter(Order.order_type == order_type)
    
    orders = query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()
    
    # Add customer information to response
    result = []
    for order in orders:
        customer = db.query(Customer).filter(Customer.customer_id == order.customer_id).first()
        
        order_data = OrderWithCustomer(
            order_id=order.order_id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            order_date=order.order_date,
            total_amount=float(order.total_amount),
            shipping_charges=float(order.shipping_charges),
            tax_amount=float(order.tax_amount),
            discount_amount=float(order.discount_amount),
            final_amount=float(order.final_amount),
            order_type=order.order_type,
            payment_method=order.payment_method,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            customer_name=f"{customer.first_name} {customer.last_name}" if customer else "Unknown",
            customer_email=customer.email if customer else "Unknown"
        )
        result.append(order_data)
    
    return result

@router.get("/{order_id}", response_model=OrderWithCustomer)
def get_order_admin(
    order_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific order details"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    customer = db.query(Customer).filter(Customer.customer_id == order.customer_id).first()
    
    return OrderWithCustomer(
        order_id=order.order_id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=float(order.total_amount),
        shipping_charges=float(order.shipping_charges),
        tax_amount=float(order.tax_amount),
        discount_amount=float(order.discount_amount),
        final_amount=float(order.final_amount),
        order_type=order.order_type,
        payment_method=order.payment_method,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        customer_name=f"{customer.first_name} {customer.last_name}" if customer else "Unknown",
        customer_email=customer.email if customer else "Unknown"
    )

@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
def get_order_items(
    order_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get items for a specific order"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    # Add product information to response
    result = []
    for item in items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        
        item_data = OrderItemResponse(
            order_item_id=item.order_item_id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            requires_prescription=item.requires_prescription,
            prescription_verified=item.prescription_verified,
            created_at=item.created_at,
            product_name=product.name if product else "Unknown",
            product_image=product.image_url if product else None
        )
        result.append(item_data)
    
    return result

@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update order status"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["pending", "confirmed", "processing", "ready", "shipped", "delivered", "cancelled"]
    if order_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update timestamps based on status
    if order_update.status == "ready":
        order.ready_at = datetime.now()
    elif order_update.status == "cancelled":
        order.cancelled_at = datetime.now()
    
    order.status = order_update.status
    order.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": f"Order status updated to {order_update.status}",
        "order_id": order_id,
        "status": order_update.status
    }

@router.get("/stats/summary")
def get_orders_summary(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get orders statistics summary"""
    total_orders = db.query(Order).count()
    
    # Orders by status
    status_counts = db.query(
        Order.status,
        func.count(Order.order_id).label('count')
    ).group_by(Order.status).all()
    
    # Recent orders (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_orders = db.query(Order).filter(Order.order_date >= week_ago).count()
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.final_amount)).scalar() or 0
    
    # Today's orders
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = db.query(Order).filter(Order.order_date >= today_start).count()
    
    return {
        "total_orders": total_orders,
        "recent_orders_7_days": recent_orders,
        "today_orders": today_orders,
        "total_revenue": float(total_revenue),
        "status_distribution": [
            {"status": status, "count": count}
            for status, count in status_counts
        ]
    }