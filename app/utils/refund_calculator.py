# app/utils/refund_calculator.py
from app.models.models import Order, RefundPolicy
from datetime import datetime

def determine_refund_policy(order: Order) -> RefundPolicy:
    """
    Determine refund policy based on order status and conditions
    """
    # Full refund for orders cancelled before processing
    if order.status == "cancelled":
        order_age_hours = (datetime.now() - order.created_at).total_seconds() / 3600
        
        if order_age_hours < 1:  # Cancelled within 1 hour
            return RefundPolicy.full
        elif order_age_hours < 24:  # Cancelled within 24 hours
            return RefundPolicy.partial
        else:
            return RefundPolicy.no_refund
    
    # Partial refund for returned orders
    elif order.status == "returned":
        delivery_time = order.ready_at or order.created_at
        days_since_delivery = (datetime.now() - delivery_time).days
        
        if days_since_delivery <= 7:  # Returned within 7 days
            return RefundPolicy.partial
        else:
            return RefundPolicy.no_refund
    
    # No refund for other cases
    return RefundPolicy.no_refund

def calculate_refund_amount(order: Order, refund_policy: RefundPolicy) -> float:
    """
    Calculate refund amount based on refund policy
    """
    base_amount = order.final_amount
    
    if refund_policy == RefundPolicy.full:
        return base_amount
    
    elif refund_policy == RefundPolicy.partial:
        # Apply cancellation fee for partial refunds
        cancellation_fee_percentage = order.cancellation_fee_percentage or 10.00
        cancellation_fee = (cancellation_fee_percentage / 100) * base_amount
        return base_amount - cancellation_fee
    
    elif refund_policy == RefundPolicy.no_refund:
        return 0.0
    
    return 0.0

def is_refund_eligible(order: Order) -> bool:
    """
    Check if order is eligible for refund based on your business rules
    """
    # Only cancelled or returned orders are eligible
    if order.status not in ["cancelled", "returned"]:
        return False
    
    # Check time constraints
    if order.status == "cancelled":
        order_age_hours = (datetime.now() - order.created_at).total_seconds() / 3600
        return order_age_hours <= 24  # Only within 24 hours
    
    elif order.status == "returned":
        delivery_time = order.ready_at or order.created_at
        days_since_delivery = (datetime.now() - delivery_time).days
        return days_since_delivery <= 7  # Only within 7 days
    
    return False