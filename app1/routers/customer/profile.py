from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres import get_db
from app.models.postgres_models import Customer, CustomerAddress
from app.schemas.customer import (
    CustomerResponse, CustomerUpdate, AddressResponse, 
    AddressCreate, AddressUpdate
)
# Fix the import - use get_current_customer from security instead
from app.core.security import get_current_customer

router = APIRouter(prefix="/customer", tags=["customer"])

# All these endpoints require authentication
@router.get("/profile", response_model=CustomerResponse)
def get_profile(current_customer: Customer = Depends(get_current_customer)):
    """Get current customer profile - Requires authentication"""
    return current_customer

@router.put("/profile", response_model=CustomerResponse)
def update_profile(
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Update customer profile - Requires authentication"""
    update_data = customer_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_customer, field, value)
    
    db.commit()
    db.refresh(current_customer)
    
    return current_customer

@router.get("/addresses", response_model=List[AddressResponse])
def get_addresses(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Get customer addresses - Requires authentication"""
    addresses = db.query(CustomerAddress).filter(
        CustomerAddress.customer_id == current_customer.customer_id
    ).all()
    return addresses

@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Create new address - Requires authentication"""
    # If this is set as default, unset other defaults
    if address_data.is_default:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.customer_id,
            CustomerAddress.is_default == True
        ).update({"is_default": False})
    
    db_address = CustomerAddress(
        customer_id=current_customer.customer_id,
        **address_data.dict()
    )
    
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    
    return db_address

@router.get("/addresses/{address_id}", response_model=AddressResponse)
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Get specific address - Requires authentication"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_customer.customer_id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return address

@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Update address - Requires authentication"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_customer.customer_id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    update_data = address_data.dict(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get('is_default') == True:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.customer_id,
            CustomerAddress.is_default == True,
            CustomerAddress.address_id != address_id
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    
    return address

@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    """Delete address - Requires authentication"""
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_customer.customer_id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    db.delete(address)
    db.commit()
    
    return {"message": "Address deleted successfully"}