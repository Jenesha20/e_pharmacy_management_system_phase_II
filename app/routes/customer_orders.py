from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_customer
from app.models.models import Order, OrderItem, Customer, Product, CustomerAddress, CartItem, Prescription, PharmacyInventory
from app.schemas.orders import OrderResponse, OrderItemResponse, OrderCreate, OrderWithDetails

router = APIRouter(prefix="/customer/orders", tags=["customer-orders"])

@router.get("/", response_model=List[OrderResponse])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get orders for the current customer - CUSTOMER ONLY"""
    query = db.query(Order).filter(Order.customer_id == current_user.customer_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=OrderWithDetails)
def get_my_order(
    order_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get specific order with full details for the current customer - CUSTOMER ONLY"""
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get order items with product details
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    items_with_details = []
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        items_with_details.append(OrderItemResponse(
            order_item_id=item.order_item_id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            requires_prescription=item.requires_prescription,
            prescription_verified=item.prescription_verified,
            created_at=item.created_at,
            product_name=product.name if product else "Unknown",
            product_image=product.image_url if product else None
        ))
    
    # Get shipping address if available
    shipping_address = None
    if order.shipping_address_id:
        shipping_address = db.query(CustomerAddress).filter(
            CustomerAddress.address_id == order.shipping_address_id
        ).first()
    
    return OrderWithDetails(
        order_id=order.order_id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=float(order.total_amount),
        shipping_charges=float(order.shipping_charges),
        tax_amount=float(order.tax_amount),
        discount_amount=float(order.discount_amount),
        final_amount=float(order.final_amount),
        order_type=order.order_type,
        payment_method=order.payment_method,
        status=order.status,
        shipping_address=shipping_address,
        items=items_with_details,
        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create a new order from cart items - CUSTOMER ONLY"""
    try:
        print(f"🔍 DEBUG: Starting order creation for user {current_user.customer_id}")
        
        # Validate shipping address
        if order_data.shipping_address_id:
            address = db.query(CustomerAddress).filter(
                CustomerAddress.address_id == order_data.shipping_address_id,
                CustomerAddress.customer_id == current_user.customer_id
            ).first()
            if not address:
                raise HTTPException(status_code=400, detail="Invalid shipping address")
            print(f"🔍 DEBUG: Shipping address validated: {address.address_id}")

        # Get cart items for the current user
        cart_items = db.query(CartItem).filter(CartItem.customer_id == current_user.customer_id).all()
        print(f"🔍 DEBUG: Found {len(cart_items)} cart items")

        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Check prescription requirements
        prescription_required_items = []
        for cart_item in cart_items:
            product = db.query(Product).filter(Product.product_id == cart_item.product_id).first()
            if product and product.requires_prescription:
                print(f"🔍 DEBUG: Product {product.name} requires prescription")
                # Check if prescription is approved for this customer
                approved_prescription = db.query(Prescription).filter(
                    Prescription.customer_id == current_user.customer_id,
                    Prescription.status == "approved"
                ).first()
                
                if not approved_prescription:
                    prescription_required_items.append(product.name)
                    print(f"🔍 DEBUG: No approved prescription found for {product.name}")

        if prescription_required_items:
            raise HTTPException(
                status_code=400,
                detail=f"Prescription required for: {', '.join(prescription_required_items)}. Please upload and get approval first."
            )

        # Check inventory and calculate totals
        total_amount = 0.0
        order_items_data = []
        
        for cart_item in cart_items:
            product = db.query(Product).filter(Product.product_id == cart_item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product not found for cart item {cart_item.cart_item_id}")
            
            print(f"🔍 DEBUG: Processing product {product.name}, quantity {cart_item.quantity}")
            
            inventory = db.query(PharmacyInventory).filter(
                PharmacyInventory.product_id == cart_item.product_id,
                PharmacyInventory.is_available == True
            ).first()
            
            if not inventory:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {product.name} is out of stock"
                )
            
            if inventory.quantity_in_stock < cart_item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {inventory.quantity_in_stock} items available for {product.name}, but {cart_item.quantity} requested"
                )
            
            item_total = float(product.price) * cart_item.quantity
            total_amount += item_total
            
            order_items_data.append({
                'product_id': product.product_id,
                'quantity': cart_item.quantity,
                'unit_price': float(product.price),
                'subtotal': item_total,
                'requires_prescription': product.requires_prescription
            })
            
            print(f"🔍 DEBUG: Added item {product.name} to order data")

        # Calculate final amount
        shipping_charges = 50.0  # Fixed shipping for now
        tax_amount = total_amount * 0.18  # 18% GST
        final_amount = total_amount + shipping_charges + tax_amount
        
        print(f"🔍 DEBUG: Calculated totals - Subtotal: {total_amount}, Tax: {tax_amount}, Shipping: {shipping_charges}, Final: {final_amount}")

        # Generate order number
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.customer_id}"
        print(f"🔍 DEBUG: Generated order number: {order_number}")

        # Create order
        new_order = Order(
            order_number=order_number,
            customer_id=current_user.customer_id,
            total_amount=total_amount,
            shipping_charges=shipping_charges,
            tax_amount=tax_amount,
            discount_amount=0.0,
            final_amount=final_amount,
            order_type=order_data.order_type,
            shipping_address_id=order_data.shipping_address_id,
            payment_method=order_data.payment_method,
            status="pending"
        )
        
        db.add(new_order)
        db.flush()  # Get the order ID without committing
        print(f"🔍 DEBUG: Created order with ID: {new_order.order_id}")

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                subtotal=item_data['subtotal'],
                requires_prescription=item_data['requires_prescription'],
                prescription_verified=not item_data['requires_prescription']  # Auto-verify if no prescription needed
            )
            db.add(order_item)
            print(f"🔍 DEBUG: Created order item for product {item_data['product_id']}")
            
            # Update inventory
            inventory = db.query(PharmacyInventory).filter(
                PharmacyInventory.product_id == item_data['product_id'],
                PharmacyInventory.is_available == True
            ).first()
            if inventory:
                inventory.quantity_in_stock -= item_data['quantity']
                print(f"🔍 DEBUG: Updated inventory for product {item_data['product_id']}, new quantity: {inventory.quantity_in_stock}")
                if inventory.quantity_in_stock <= 0:
                    inventory.is_available = False
                    print(f"🔍 DEBUG: Marked product {item_data['product_id']} as out of stock")

        # Clear the cart
        cart_delete_count = db.query(CartItem).filter(CartItem.customer_id == current_user.customer_id).delete()
        print(f"🔍 DEBUG: Cleared {cart_delete_count} cart items")
        
        db.commit()
        print("🔍 DEBUG: Order creation completed successfully")

        return {
            "message": "Order created successfully",
            "order_id": new_order.order_id,
            "order_number": new_order.order_number,
            "final_amount": float(new_order.final_amount),
            "status": new_order.status
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR in order creation: {str(e)}")
        print(f"❌ ERROR type: {type(e)}")
        import traceback
        print(f"❌ ERROR traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")

@router.post("/{order_id}/cancel")
def cancel_my_order(
    order_id: int,
    reason: str,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Cancel an order - CUSTOMER ONLY"""
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order can be cancelled
    cancellable_statuses = ["pending", "confirmed"]
    if order.status not in cancellable_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status: {order.status}"
        )
    
    # Update order status and restore inventory
    order.status = "cancelled"
    order.cancellation_reason = reason
    order.cancelled_at = datetime.now()
    order.updated_at = datetime.now()
    
    # Restore inventory
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    for item in order_items:
        inventory = db.query(PharmacyInventory).filter(
            PharmacyInventory.product_id == item.product_id
        ).first()
        if inventory:
            inventory.quantity_in_stock += item.quantity
            if not inventory.is_available:
                inventory.is_available = True
    
    db.commit()
    
    return {"message": "Order cancelled successfully"}

@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
def get_my_order_items(
    order_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get items for a specific order - CUSTOMER ONLY"""
    # Verify order belongs to current user
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == current_user.customer_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    # Add product information to response
    result = []
    for item in items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        
        item_data = OrderItemResponse(
            order_item_id=item.order_item_id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            requires_prescription=item.requires_prescription,
            prescription_verified=item.prescription_verified,
            created_at=item.created_at,
            product_name=product.name if product else "Unknown",
            product_image=product.image_url if product else None
        )
        result.append(item_data)
    
    return result

