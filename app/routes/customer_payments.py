from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_customer
from app.models.models import Payment, Order, Customer
from app.schemas.payments import PaymentResponse, PaymentCreate

router = APIRouter(prefix="/customer/payments", tags=["customer-payments"])

@router.get("/", response_model=List[PaymentResponse])
def get_my_payments(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get payment history for the current customer - CUSTOMER ONLY"""
    payments = db.query(Payment).join(Order).filter(
        Order.customer_id == current_user.customer_id
    ).order_by(Payment.created_at.desc()).all()
    
    return payments

@router.get("/order/{order_id}", response_model=List[PaymentResponse])
def get_order_payments(
    order_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get payments for a specific order - CUSTOMER ONLY"""
    # Verify order belongs to current user
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    return payments

@router.post("/{order_id}/pay", response_model=PaymentResponse)
def process_payment(
    order_id: int,
    payment_data: PaymentCreate,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Process payment for an order - CUSTOMER ONLY"""
    # Verify order belongs to current user
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot pay for cancelled order")
    
    # Check if payment already exists and is completed
    existing_payment = db.query(Payment).filter(
        Payment.order_id == order_id,
        Payment.status == "completed"
    ).first()
    
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already completed for this order")
    
    try:
        # Simulate payment processing (in real app, integrate with payment gateway)
        # For demo purposes, we'll simulate successful payment 80% of the time
        import random
        payment_successful = random.random() < 0.8
        
        payment_status = "completed" if payment_successful else "failed"
        
        # Create payment record
        new_payment = Payment(
            order_id=order_id,
            payment_gateway=payment_data.payment_gateway,
            amount=order.final_amount,
            method=payment_data.method,
            status=payment_status,
            gateway_transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
            paid_at=datetime.now() if payment_successful else None
        )
        
        db.add(new_payment)
        
        # Update order status if payment successful
        if payment_successful:
            order.status = "confirmed"
            order.updated_at = datetime.now()
        
        db.commit()
        db.refresh(new_payment)
        
        return new_payment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_details(
    payment_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get specific payment details - CUSTOMER ONLY"""
    payment = db.query(Payment).join(Order).filter(
        Payment.payment_id == payment_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment