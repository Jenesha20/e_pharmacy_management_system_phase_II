# app/routes/refunds.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.models import Customer, Order, Refund, Payment, RefundPolicy, RefundStatus
from app.schemas.refund import RefundRequest, RefundResponse
from app.middleware.auth import get_current_customer
from app.utils.refund_calculator import calculate_refund_amount, determine_refund_policy

router = APIRouter(prefix="/refunds", tags=["Customer Refunds"])

# Update the refund request endpoint to use the new eligibility check
@router.post("/request", response_model=RefundResponse)
async def request_refund(
    refund_request: RefundRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    # Verify order belongs to customer
    order = db.query(Order).filter(
        Order.order_id == refund_request.order_id,
        Order.customer_id == current_customer.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is eligible for refund using the new function
    from app.utils.refund_calculator import is_refund_eligible
    if not is_refund_eligible(order):
        raise HTTPException(
            status_code=400, 
            detail="Order is not eligible for refund based on our policy"
        )
    
    # Check if refund already exists
    existing_refund = db.query(Refund).filter(Refund.order_id == refund_request.order_id).first()
    if existing_refund:
        raise HTTPException(status_code=400, detail="Refund already requested for this order")
    
    # Rest of the implementation remains the same...
    refund_policy = determine_refund_policy(order)
    refund_amount = calculate_refund_amount(order, refund_policy)
    
    refund = Refund(
        order_id=refund_request.order_id,
        amount=refund_amount,
        cancellation_fee=order.cancellation_fee_percentage or 10.00,
        refund_policy=refund_policy,
        reason=refund_request.reason,
        status=RefundStatus.pending,
        created_at=datetime.now()
    )
    
    db.add(refund)
    db.commit()
    db.refresh(refund)
    
    await create_refund_notification(refund, db)
    
    return refund

@router.get("/my-refunds", response_model=List[RefundResponse])
async def get_my_refunds(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    # Get all refunds for customer's orders
    refunds = db.query(Refund).join(Order).filter(
        Order.customer_id == current_customer.customer_id
    ).order_by(Refund.created_at.desc()).all()
    
    return refunds

@router.get("/{refund_id}", response_model=RefundResponse)
async def get_refund_details(
    refund_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    refund = db.query(Refund).join(Order).filter(
        Refund.refund_id == refund_id,
        Order.customer_id == current_customer.customer_id
    ).first()
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    return refund