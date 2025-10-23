from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func  # Import func from sqlalchemy
from typing import List, Optional
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Product, Category, Customer
from app.schemas.admin import ProductCreate, ProductUpdate, ProductResponse, ProductWithCategory

router = APIRouter(prefix="/admin/products", tags=["admin-products"])

@router.get("/", response_model=List[ProductWithCategory])
def get_products_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    requires_prescription: Optional[bool] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all products (admin view - includes filters)"""
    query = db.query(Product)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if requires_prescription is not None:
        query = query.filter(Product.requires_prescription == requires_prescription)
    
    products = query.offset(skip).limit(limit).all()
    
    # Build response with category name
    result = []
    for product in products:
        category = db.query(Category).filter(Category.category_id == product.category_id).first()
        
        # Create ProductWithCategory manually instead of using from_orm
        product_data = ProductWithCategory(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            sku=product.sku,
            category_id=product.category_id,
            manufacturer=product.manufacturer,
            requires_prescription=product.requires_prescription,
            hsn_code=float(product.hsn_code),
            gst_rate=float(product.gst_rate),
            price=float(product.price),
            cost_price=float(product.cost_price),
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=category.name if category else "Unknown"
        )
        result.append(product_data)
    
    return result

@router.get("/{product_id}", response_model=ProductWithCategory)
def get_product_admin(
    product_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific product details (admin view)"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = db.query(Category).filter(Category.category_id == product.category_id).first()
    
    # Create ProductWithCategory manually
    product_data = ProductWithCategory(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        sku=product.sku,
        category_id=product.category_id,
        manufacturer=product.manufacturer,
        requires_prescription=product.requires_prescription,
        hsn_code=float(product.hsn_code),
        gst_rate=float(product.gst_rate),
        price=float(product.price),
        cost_price=float(product.cost_price),
        image_url=product.image_url,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category_name=category.name if category else "Unknown"
    )
    
    return product_data

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_admin(
    product: ProductCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # Check if category exists and is active
    category = db.query(Category).filter(
        Category.category_id == product.category_id,
        Category.is_active == True
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid or inactive category")
    
    # Check if SKU already exists
    existing_product = db.query(Product).filter(Product.sku == product.sku).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product_admin(
    product_id: int,
    product_update: ProductUpdate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update product details"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    
    # If category_id is being updated, validate it
    if 'category_id' in update_data:
        category = db.query(Category).filter(
            Category.category_id == update_data['category_id'],
            Category.is_active == True
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
    
    # If SKU is being updated, check for duplicates
    if 'sku' in update_data and update_data['sku'] != product.sku:
        existing_product = db.query(Product).filter(
            Product.sku == update_data['sku'],
            Product.product_id != product_id
        ).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="SKU already exists")
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product_admin(
    product_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Soft delete a product"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete by setting is_active to False
    product.is_active = False
    db.commit()
    return {"message": "Product deleted successfully"}

@router.patch("/{product_id}/restore")
def restore_product_admin(
    product_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted product"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = True
    db.commit()
    return {"message": "Product restored successfully"}

@router.get("/stats/summary")
def get_products_summary(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get products statistics summary"""
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.is_active == True).count()
    prescription_products = db.query(Product).filter(Product.requires_prescription == True).count()
    inactive_products = total_products - active_products
    
    # Products by category - FIXED: Use func from sqlalchemy, not db.func
    categories_stats = db.query(
        Category.name,
        Category.category_id,
        func.count(Product.product_id).label('product_count')  # Use func directly
    ).join(Product, Category.category_id == Product.category_id)\
     .group_by(Category.category_id, Category.name)\
     .all()
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "inactive_products": inactive_products,
        "prescription_required_products": prescription_products,
        "categories_distribution": [
            {
                "category_id": cat.category_id,
                "category_name": cat.name,
                "product_count": cat.product_count
            }
            for cat in categories_stats
        ]
    }