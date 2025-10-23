from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta  # Add timedelta import
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Prescription, PrescriptionItem, Customer, Product
from app.schemas.admin import (
    PrescriptionResponse, PrescriptionUpdate, PrescriptionWithCustomer,
    PrescriptionItemResponse
)

router = APIRouter(prefix="/admin/prescriptions", tags=["admin-prescriptions"])

@router.get("/", response_model=List[PrescriptionWithCustomer])
def get_prescriptions_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all prescriptions with filters"""
    query = db.query(Prescription)
    
    if status:
        query = query.filter(Prescription.status == status)
    if customer_id:
        query = query.filter(Prescription.customer_id == customer_id)
    
    prescriptions = query.order_by(Prescription.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    # Add customer information to response
    result = []
    for prescription in prescriptions:
        customer = db.query(Customer).filter(Customer.customer_id == prescription.customer_id).first()
        
        prescription_data = PrescriptionWithCustomer(
            prescription_id=prescription.prescription_id,
            customer_id=prescription.customer_id,
            image_url=prescription.image_url,
            status=prescription.status,
            verified_by=prescription.verified_by,
            verification_notes=prescription.verification_notes,
            uploaded_at=prescription.uploaded_at,
            verified_at=prescription.verified_at,
            customer_name=f"{customer.first_name} {customer.last_name}" if customer else "Unknown",
            customer_email=customer.email if customer else "Unknown"
        )
        result.append(prescription_data)
    
    return result

@router.get("/{prescription_id}", response_model=PrescriptionWithCustomer)
def get_prescription_admin(
    prescription_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific prescription details"""
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    customer = db.query(Customer).filter(Customer.customer_id == prescription.customer_id).first()
    
    return PrescriptionWithCustomer(
        prescription_id=prescription.prescription_id,
        customer_id=prescription.customer_id,
        image_url=prescription.image_url,
        status=prescription.status,
        verified_by=prescription.verified_by,
        verification_notes=prescription.verification_notes,
        uploaded_at=prescription.uploaded_at,
        verified_at=prescription.verified_at,
        customer_name=f"{customer.first_name} {customer.last_name}" if customer else "Unknown",
        customer_email=customer.email if customer else "Unknown"
    )

@router.get("/{prescription_id}/items", response_model=List[PrescriptionItemResponse])
def get_prescription_items(
    prescription_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get items for a specific prescription"""
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    items = db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id == prescription_id
    ).all()
    
    # Add product information to response
    result = []
    for item in items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        
        item_data = PrescriptionItemResponse(
            prescription_item_id=item.prescription_item_id,
            prescription_id=item.prescription_id,
            product_id=item.product_id,
            quantity=item.quantity,
            created_at=item.created_at,
            product_name=product.name if product else "Unknown",
            requires_prescription=product.requires_prescription if product else False
        )
        result.append(item_data)
    
    return result

@router.put("/{prescription_id}/verify")
def verify_prescription(
    prescription_id: int,
    prescription_update: PrescriptionUpdate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Verify/approve/reject a prescription"""
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # if prescription.status != "pending":
    #     raise HTTPException(
    #         status_code=400, 
    #         detail=f"Prescription is already {prescription.status}"
    #     )
    
    # Update prescription status
    prescription.status = prescription_update.status
    prescription.verified_by = current_admin.customer_id
    prescription.verification_notes = prescription_update.verification_notes
    prescription.verified_at = datetime.now()
    
    db.commit()
    
    return {
        "message": f"Prescription {prescription_update.status} successfully",
        "prescription_id": prescription_id,
        "status": prescription_update.status
    }

@router.get("/stats/summary")
def get_prescriptions_summary(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get prescriptions statistics summary"""
    total_prescriptions = db.query(Prescription).count()
    pending_prescriptions = db.query(Prescription).filter(Prescription.status == "pending").count()
    approved_prescriptions = db.query(Prescription).filter(Prescription.status == "approved").count()
    rejected_prescriptions = db.query(Prescription).filter(Prescription.status == "rejected").count()
    
    # Recent prescriptions (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_prescriptions = db.query(Prescription).filter(
        Prescription.uploaded_at >= week_ago
    ).count()
    
    return {
        "total_prescriptions": total_prescriptions,
        "pending_prescriptions": pending_prescriptions,
        "approved_prescriptions": approved_prescriptions,
        "rejected_prescriptions": rejected_prescriptions,
        "recent_prescriptions_7_days": recent_prescriptions,
        "approval_rate": round((approved_prescriptions / total_prescriptions * 100), 2) if total_prescriptions > 0 else 0
    }