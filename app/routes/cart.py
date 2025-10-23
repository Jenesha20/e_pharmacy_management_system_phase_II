from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.middleware.auth import get_current_customer as get_current_user
from app.models.models import CartItem, Product, Customer, PharmacyInventory
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse, CartItemWithProduct

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=List[CartItemWithProduct])
def get_cart_items(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cart items for the CURRENT USER ONLY"""
    cart_items = db.query(CartItem).filter(CartItem.customer_id == current_user.customer_id).all()
    
    result = []
    for item in cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if not product:
            continue
            
        inventory = db.query(PharmacyInventory).filter(
            PharmacyInventory.product_id == item.product_id,
            PharmacyInventory.is_available == True
        ).first()
        
        stock_quantity = inventory.quantity_in_stock if inventory else 0
        
        result.append(CartItemWithProduct(
            cart_item_id=item.cart_item_id,
            customer_id=item.customer_id,
            product_id=item.product_id,
            quantity=item.quantity,
            added_at=item.added_at,
            updated_at=item.updated_at,
            product_name=product.name,
            product_price=float(product.price),
            requires_prescription=product.requires_prescription,
            image_url=product.image_url,
            stock_quantity=stock_quantity
        ))
    
    return result

@router.get("/summary")
def get_cart_summary(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cart summary for the CURRENT USER ONLY"""
    cart_items = db.query(CartItem).filter(CartItem.customer_id == current_user.customer_id).all()
    
    total_items = 0
    total_price = 0.0
    
    for item in cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if product:
            total_items += item.quantity
            total_price += float(product.price) * item.quantity
    
    return {
        "total_items": total_items,
        "total_price": round(total_price, 2),
        "item_count": len(cart_items)
    }

@router.post("/", response_model=CartItemResponse)
def add_to_cart(
    cart_item: CartItemCreate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart for the CURRENT USER ONLY"""
    # Check if product exists and is active
    product = db.query(Product).filter(
        Product.product_id == cart_item.product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check inventory stock
    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.product_id == cart_item.product_id,
        PharmacyInventory.is_available == True,
        PharmacyInventory.quantity_in_stock >= cart_item.quantity
    ).first()
    
    if not inventory:
        raise HTTPException(
            status_code=400, 
            detail="Product is out of stock or insufficient quantity available"
        )
    
    # Check if item already in cart FOR CURRENT USER
    existing_item = db.query(CartItem).filter(
        CartItem.customer_id == current_user.customer_id,  # Ensure user-specific
        CartItem.product_id == cart_item.product_id
    ).first()
    
    if existing_item:
        # Check if updated quantity exceeds stock
        new_quantity = existing_item.quantity + cart_item.quantity
        if new_quantity > inventory.quantity_in_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Only {inventory.quantity_in_stock} items available in stock"
            )
        
        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Create cart item FOR CURRENT USER ONLY
        new_item = CartItem(
            customer_id=current_user.customer_id,  # Always use current user's ID
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item

@router.put("/{cart_item_id}", response_model=CartItemResponse)
def update_cart_item(
    cart_item_id: int,
    cart_item_update: CartItemUpdate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item for the CURRENT USER ONLY"""
    cart_item = db.query(CartItem).filter(
        CartItem.cart_item_id == cart_item_id,
        CartItem.customer_id == current_user.customer_id  # Ensure user owns this cart item
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Check inventory stock
    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.product_id == cart_item.product_id,
        PharmacyInventory.is_available == True,
        PharmacyInventory.quantity_in_stock >= cart_item_update.quantity
    ).first()
    
    if not inventory:
        raise HTTPException(
            status_code=400, 
            detail="Insufficient stock available"
        )
    
    cart_item.quantity = cart_item_update.quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.delete("/{cart_item_id}")
def remove_from_cart(
    cart_item_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart for the CURRENT USER ONLY"""
    cart_item = db.query(CartItem).filter(
        CartItem.cart_item_id == cart_item_id,
        CartItem.customer_id == current_user.customer_id  # Ensure user owns this cart item
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart successfully"}

@router.delete("/")
def clear_cart(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear entire cart for the CURRENT USER ONLY"""
    cart_items = db.query(CartItem).filter(CartItem.customer_id == current_user.customer_id).all()
    
    for item in cart_items:
        db.delete(item)
    
    db.commit()
    return {"message": "Cart cleared successfully"}