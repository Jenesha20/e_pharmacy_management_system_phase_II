from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import Customer, CustomerAddress
from app.schemas.users import CustomerResponse, CustomerProfileUpdate, AddressResponse, AddressCreate, AddressUpdate
from app.utils.security import get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["users"])

# Profile Management
@router.get("/profile", response_model=CustomerResponse)
def get_profile(current_user: Customer = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=CustomerResponse)
def update_profile(
    profile_update: CustomerProfileUpdate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

# Address Management
@router.get("/addresses", response_model=List[AddressResponse])
def get_addresses(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all addresses for current user"""
    addresses = db.query(CustomerAddress).filter(
        CustomerAddress.customer_id == current_user.customer_id
    ).all()
    return addresses

@router.get("/addresses/{address_id}", response_model=AddressResponse)
def get_address(
    address_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific address"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    return address

@router.post("/addresses", response_model=AddressResponse)
def create_address(
    address: AddressCreate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new address"""
    # If setting as default, unset other defaults
    if address.is_default:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_user.customer_id
        ).update({"is_default": False})
    
    new_address = CustomerAddress(
        customer_id=current_user.customer_id,
        **address.dict()
    )
    
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_update: AddressUpdate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update address"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = address_update.dict(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get('is_default'):
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_user.customer_id
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    return address

@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete address"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}

@router.get("/dashboard")
def get_customer_dashboard(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer dashboard data"""
    from app.models.models import Order, Prescription
    
    # Get order statistics
    total_orders = db.query(Order).filter(Order.customer_id == current_user.customer_id).count()
    pending_orders = db.query(Order).filter(
        Order.customer_id == current_user.customer_id,
        Order.status.in_(["pending", "confirmed", "processing"])
    ).count()
    
    # Get prescription statistics
    total_prescriptions = db.query(Prescription).filter(
        Prescription.customer_id == current_user.customer_id
    ).count()
    pending_prescriptions = db.query(Prescription).filter(
        Prescription.customer_id == current_user.customer_id,
        Prescription.status == "pending"
    ).count()
    
    # Get recent orders
    recent_orders = db.query(Order).filter(
        Order.customer_id == current_user.customer_id
    ).order_by(Order.order_date.desc()).limit(5).all()
    
    return {
        "customer_id": current_user.customer_id,
        "customer_name": f"{current_user.first_name} {current_user.last_name}",
        "order_stats": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": total_orders - pending_orders
        },
        "prescription_stats": {
            "total_prescriptions": total_prescriptions,
            "pending_prescriptions": pending_prescriptions,
            "approved_prescriptions": db.query(Prescription).filter(
                Prescription.customer_id == current_user.customer_id,
                Prescription.status == "approved"
            ).count()
        },
        "recent_orders": [
            {
                "order_id": order.order_id,
                "order_number": order.order_number,
                "status": order.status,
                "final_amount": float(order.final_amount),
                "order_date": order.order_date
            }
            for order in recent_orders
        ]
    }