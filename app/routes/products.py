from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Product, Category, PharmacyInventory
from app.schemas.products import ProductResponse, CategoryResponse, ProductDetailResponse

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Get all active categories"""
    return db.query(Category).filter(Category.is_active == True).all()

@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get specific category"""
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
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products with advanced filtering"""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if requires_prescription is not None:
        query = query.filter(Product.requires_prescription == requires_prescription)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get detailed product information with inventory"""
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get inventory information
    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.product_id == product_id,
        PharmacyInventory.is_available == True,
        PharmacyInventory.quantity_in_stock > 0
    ).first()
    
    # Get category name
    category = db.query(Category).filter(Category.category_id == product.category_id).first()
    
    return ProductDetailResponse(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        sku=product.sku,
        category_id=product.category_id,
        category_name=category.name if category else "Unknown",
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
        in_stock=inventory.quantity_in_stock if inventory else 0,
        stock_quantity=inventory.quantity_in_stock if inventory else 0,
        low_stock=inventory.quantity_in_stock <= inventory.low_stock_threshold if inventory else False
    )

@router.get("/featured/products")
def get_featured_products(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get featured products (could be based on sales, ratings, etc.)"""
    # For now, return recent products with stock
    featured_products = db.query(Product).filter(
        Product.is_active == True
    ).order_by(Product.created_at.desc()).limit(limit).all()
    
    return featured_products

@router.get("/search/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Get search suggestions for autocomplete"""
    if len(q) < 2:
        return []
    
    suggestions = db.query(Product).filter(
        Product.is_active == True,
        Product.name.ilike(f"%{q}%")
    ).limit(limit).all()
    
    return [
        {
            "product_id": product.product_id,
            "name": product.name,
            "image_url": product.image_url,
            "price": float(product.price)
        }
        for product in suggestions
    ]