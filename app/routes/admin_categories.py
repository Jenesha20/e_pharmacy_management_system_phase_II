from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Category, Product, Customer
from app.schemas.admin import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all categories (admin view - includes inactive)"""
    query = db.query(Category)
    
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_admin(
    category_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific category details (admin view)"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_admin(
    category: CategoryCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # Check if category name already exists
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(
            status_code=400, 
            detail="Category name already exists"
        )
    
    new_category = Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category_admin(
    category_id: int,
    category_update: CategoryUpdate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update category details"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_update.dict(exclude_unset=True)
    
    # If name is being updated, check for duplicates
    if 'name' in update_data and update_data['name'] != category.name:
        existing_category = db.query(Category).filter(
            Category.name == update_data['name'],
            Category.category_id != category_id
        ).first()
        if existing_category:
            raise HTTPException(
                status_code=400, 
                detail="Category name already exists"
            )
    
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category_admin(
    category_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Soft delete a category"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has active products
    active_products = db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).count()
    
    if active_products > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete category with {active_products} active products. Deactivate products first."
        )
    
    # Soft delete by setting is_active to False
    category.is_active = False
    db.commit()
    return {"message": "Category deleted successfully"}

@router.patch("/{category_id}/restore")
def restore_category_admin(
    category_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted category"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category.is_active = True
    db.commit()
    return {"message": "Category restored successfully"}

@router.get("/{category_id}/products/count")
def get_category_products_count(
    category_id: int,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get count of active products in a category"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    active_products_count = db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).count()
    
    total_products_count = db.query(Product).filter(
        Product.category_id == category_id
    ).count()
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "active_products": active_products_count,
        "total_products": total_products_count
    }