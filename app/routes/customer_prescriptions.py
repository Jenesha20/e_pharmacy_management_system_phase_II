# app/routes/customer_prescription.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
import os
import json
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_customer
from app.models.models import Prescription, PrescriptionItem, Customer, Product
from app.schemas.prescriptions import PrescriptionResponse, PrescriptionCreate

router = APIRouter(prefix="/customer/prescriptions", tags=["customer-prescriptions"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[PrescriptionResponse])
def get_my_prescriptions(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get prescriptions for the CURRENT USER ONLY with their items"""
    prescriptions = db.query(Prescription).\
        options(
            joinedload(Prescription.prescription_items).
            joinedload(PrescriptionItem.product)
        ).\
        filter(Prescription.customer_id == current_user.customer_id).\
        order_by(Prescription.uploaded_at.desc()).\
        all()
    
    return prescriptions

@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_my_prescription(
    prescription_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get specific prescription for the CURRENT USER ONLY with items"""
    prescription = db.query(Prescription).\
        options(
            joinedload(Prescription.prescription_items).
            joinedload(PrescriptionItem.product)
        ).\
        filter(
            Prescription.prescription_id == prescription_id,
            Prescription.customer_id == current_user.customer_id
        ).\
        first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    return prescription

@router.post("/upload", response_model=PrescriptionResponse)
async def upload_prescription_simple(
    image: UploadFile = File(...),
    product_ids: str = Form(...),  # Comma-separated product IDs: "1,2,3"
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Upload prescription using comma-separated product IDs"""
    # Validate file type
    allowed_content_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    if image.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, and PDF files are allowed."
        )
    
    try:
        # Parse comma-separated product IDs
        try:
            product_ids_list = [int(pid.strip()) for pid in product_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid product IDs format. Use comma-separated numbers: 1,2,3"
            )
        
        # Remove duplicates
        product_ids_list = list(set(product_ids_list))
        
        # Validate product IDs
        validated_products = []
        for product_id in product_ids_list:
            product = db.query(Product).filter(
                Product.product_id == product_id,
                Product.is_active == True
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found"
                )
            
            if not product.requires_prescription:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product '{product.name}' does not require a prescription"
                )
            
            validated_products.append(product)
        
        if not validated_products:
            raise HTTPException(
                status_code=400,
                detail="At least one valid product ID is required"
            )
        
        # Generate unique filename and save file
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{current_user.customer_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Create prescription record
        prescription = Prescription(
            customer_id=current_user.customer_id,
            image_url=file_path,
            status="pending"
        )
        
        db.add(prescription)
        db.flush()
        
        # Create prescription items (default quantity: 1)
        for product in validated_products:
            prescription_item = PrescriptionItem(
                prescription_id=prescription.prescription_id,
                product_id=product.product_id,
                quantity=1
            )
            db.add(prescription_item)
        
        db.commit()
        
        # Load prescription with relationships
        prescription_with_items = db.query(Prescription).\
            options(
                joinedload(Prescription.prescription_items).
                joinedload(PrescriptionItem.product)
            ).\
            filter(Prescription.prescription_id == prescription.prescription_id).\
            first()
        
        return prescription_with_items
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload prescription: {str(e)}"
        )
@router.get("/{prescription_id}/items")
def get_prescription_items(
    prescription_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get prescription items for a specific prescription"""
    # Verify prescription belongs to current user
    prescription = db.query(Prescription).filter(
        Prescription.prescription_id == prescription_id,
        Prescription.customer_id == current_user.customer_id
    ).first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Get prescription items with product details using joinedload
    items = db.query(PrescriptionItem).\
        options(joinedload(PrescriptionItem.product)).\
        filter(PrescriptionItem.prescription_id == prescription_id).\
        all()
    
    result = []
    for item in items:
        item_dict = {
            "prescription_item_id": item.prescription_item_id,
            "prescription_id": item.prescription_id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else "Unknown Product",
            "quantity": item.quantity,
            "created_at": item.created_at
        }
        result.append(item_dict)
    
    return result

@router.get("/{prescription_id}/status")
def get_prescription_status(
    prescription_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get prescription status for the CURRENT USER ONLY"""
    prescription = db.query(Prescription).filter(
        Prescription.prescription_id == prescription_id,
        Prescription.customer_id == current_user.customer_id
    ).first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Get items count for the response
    items_count = db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id == prescription_id
    ).count()
    
    return {
        "prescription_id": prescription.prescription_id,
        "status": prescription.status,
        "verification_notes": prescription.verification_notes,
        "uploaded_at": prescription.uploaded_at,
        "verified_at": prescription.verified_at,
        "items_count": items_count
    }


# app/routes/customer_prescription.py - Updated for order context
@router.post("/upload-for-order", response_model=PrescriptionResponse)
async def upload_prescription_for_order(
    image: UploadFile = File(...),
    product_ids: str = Form(...),  # Products from cart that need prescription
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Upload prescription specifically for order creation"""
    try:
        # Validate file type
        allowed_content_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if image.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG, PNG, and PDF files are allowed."
            )
        
        # Parse product IDs from cart
        try:
            product_ids_list = [int(pid.strip()) for pid in product_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid product IDs format. Use comma-separated numbers: 1,2,3"
            )
        
        # Remove duplicates and validate products
        product_ids_list = list(set(product_ids_list))
        validated_products = []
        
        for product_id in product_ids_list:
            product = db.query(Product).filter(
                Product.product_id == product_id,
                Product.is_active == True,
                Product.requires_prescription == True  # Only prescription-required products
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Prescription-required product with ID {product_id} not found"
                )
            
            validated_products.append(product)
        
        if not validated_products:
            raise HTTPException(
                status_code=400,
                detail="No valid prescription-required products found"
            )
        
        # Generate unique filename and save file
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{current_user.customer_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Create prescription record
        prescription = Prescription(
            customer_id=current_user.customer_id,
            image_url=file_path,
            status="pending"  # Will be verified by admin
        )
        
        db.add(prescription)
        db.flush()
        
        # Create prescription items for each product
        for product in validated_products:
            prescription_item = PrescriptionItem(
                prescription_id=prescription.prescription_id,
                product_id=product.product_id,
                quantity=1  # Default quantity
            )
            db.add(prescription_item)
        
        db.commit()
        
        return {
            "message": "Prescription uploaded successfully. Please wait for admin verification before placing order.",
            "prescription_id": prescription.prescription_id,
            "status": prescription.status,
            "products_covered": [p.name for p in validated_products]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload prescription: {str(e)}")