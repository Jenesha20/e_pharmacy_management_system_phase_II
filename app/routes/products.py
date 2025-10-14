from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Product, Category
from app.schemas.products import ProductResponse, CategoryResponse

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()

@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(
        Category.category_id == category_id,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category

@router.get("/", response_model=List[ProductResponse])
def get_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    requires_prescription: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if requires_prescription is not None:
        query = query.filter(Product.requires_prescription == requires_prescription)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product