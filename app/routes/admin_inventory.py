from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func  # Import func from sqlalchemy
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import PharmacyInventory, Product, Customer
from app.schemas.admin import InventoryCreate, InventoryUpdate, InventoryResponse

router = APIRouter(prefix="/admin/inventory", tags=["admin-inventory"])

@router.get("/", response_model=List[InventoryResponse])
def get_inventory_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_id: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(None),
    is_available: Optional[bool] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get inventory with filters"""
    query = db.query(PharmacyInventory)
    
    if product_id:
        query = query.filter(PharmacyInventory.product_id == product_id)
    if low_stock is not None:
        if low_stock:
            query = query.filter(
                PharmacyInventory.quantity_in_stock <= PharmacyInventory.low_stock_threshold
            )
    if is_available is not None:
        query = query.filter(PharmacyInventory.is_available == is_available)
    
    inventory = query.offset(skip).limit(limit).all()
    return inventory

@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def add_inventory_batch(
    inventory: InventoryCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Add new inventory batch"""
    # Check if product exists
    product = db.query(Product).filter(
        Product.product_id == inventory.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=400, detail="Invalid product")
    
    # Check if batch number already exists for this product
    existing_batch = db.query(PharmacyInventory).filter(
        PharmacyInventory.product_id == inventory.product_id,
        PharmacyInventory.batch_number == inventory.batch_number
    ).first()
    if existing_batch:
        raise HTTPException(status_code=400, detail="Batch number already exists for this product")
    
    # Check if expiry date is in the future
    if inventory.expiry_date <= datetime.now().date():
        raise HTTPException(status_code=400, detail="Expiry date must be in the future")
    
    new_inventory = PharmacyInventory(**inventory.dict())
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory

@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory_batch(
    inventory_id: int,
    inventory_update: InventoryUpdate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update inventory batch"""
    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.inventory_id == inventory_id
    ).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    
    update_data = inventory_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(inventory, field, value)
    
    db.commit()
    db.refresh(inventory)
    return inventory

@router.get("/low-stock", response_model=List[InventoryResponse])
def get_low_stock_items(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all low stock items"""
    low_stock_items = db.query(PharmacyInventory).filter(
        PharmacyInventory.quantity_in_stock <= PharmacyInventory.low_stock_threshold,
        PharmacyInventory.is_available == True
    ).all()
    return low_stock_items

@router.get("/expiring-soon", response_model=List[InventoryResponse])
def get_expiring_soon_items(
    days: int = Query(30, ge=1, le=365),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get items expiring within specified days"""
    threshold_date = datetime.now().date() + timedelta(days=days)
    
    expiring_items = db.query(PharmacyInventory).filter(
        PharmacyInventory.expiry_date <= threshold_date,
        PharmacyInventory.expiry_date >= datetime.now().date(),
        PharmacyInventory.is_available == True
    ).all()
    return expiring_items

@router.get("/stats/summary")
def get_inventory_summary(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get inventory statistics summary"""
    total_items = db.query(PharmacyInventory).count()
    available_items = db.query(PharmacyInventory).filter(
        PharmacyInventory.is_available == True
    ).count()
    
    low_stock_count = db.query(PharmacyInventory).filter(
        PharmacyInventory.quantity_in_stock <= PharmacyInventory.low_stock_threshold,
        PharmacyInventory.is_available == True
    ).count()
    
    expired_items = db.query(PharmacyInventory).filter(
        PharmacyInventory.expiry_date < datetime.now().date()
    ).count()
    
    # FIXED: Use func from sqlalchemy, not db.func
    total_stock_value = db.query(
        func.sum(PharmacyInventory.quantity_in_stock * PharmacyInventory.cost_price)
    ).scalar() or 0
    
    return {
        "total_inventory_items": total_items,
        "available_items": available_items,
        "low_stock_items": low_stock_count,
        "expired_items": expired_items,
        "total_stock_value": float(total_stock_value)
    }