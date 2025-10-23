from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import (
    Order, OrderItem, Product, Category, Customer, 
    Prescription, PharmacyInventory
)
from app.schemas.admin import ReportRequest, SalesReport

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])

@router.post("/sales", response_model=SalesReport)
def generate_sales_report(
    report_request: ReportRequest,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate sales report with various metrics"""
    try:
        # Base query for orders
        query = db.query(Order)
        
        # Apply date filters if provided
        if report_request.start_date:
            query = query.filter(Order.order_date >= report_request.start_date)
        if report_request.end_date:
            query = query.filter(Order.order_date <= report_request.end_date)
        
        # Total sales metrics
        total_sales = db.query(func.sum(Order.final_amount)).scalar() or 0
        total_orders = query.count()
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Top selling products
        top_products = db.query(
            Product.name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.subtotal).label('total_revenue')
        ).join(OrderItem, Product.product_id == OrderItem.product_id)\
         .join(Order, OrderItem.order_id == Order.order_id)\
         .group_by(Product.product_id, Product.name)\
         .order_by(func.sum(OrderItem.subtotal).desc())\
         .limit(10)\
         .all()
        
        # Sales by date (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        sales_by_date = db.query(
            func.date(Order.order_date).label('date'),
            func.count(Order.order_id).label('order_count'),
            func.sum(Order.final_amount).label('daily_sales')
        ).filter(Order.order_date >= thirty_days_ago)\
         .group_by(func.date(Order.order_date))\
         .order_by(func.date(Order.order_date))\
         .all()
        
        return SalesReport(
            total_sales=float(total_sales),
            total_orders=total_orders,
            average_order_value=float(average_order_value),
            top_products=[
                {
                    "product_name": product.name,
                    "total_quantity": product.total_quantity,
                    "total_revenue": float(product.total_revenue)
                }
                for product in top_products
            ],
            sales_by_date=[
                {
                    "date": sale_date.date.isoformat(),
                    "order_count": sale_date.order_count,
                    "daily_sales": float(sale_date.daily_sales or 0)
                }
                for sale_date in sales_by_date
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

@router.get("/inventory")
def generate_inventory_report(
    low_stock_only: bool = Query(False),
    expiring_soon: bool = Query(False),
    days: int = Query(30, ge=1, le=365),
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate inventory report"""
    try:
        # Base inventory query
        query = db.query(PharmacyInventory)
        
        if low_stock_only:
            query = query.filter(
                PharmacyInventory.quantity_in_stock <= PharmacyInventory.low_stock_threshold
            )
        
        if expiring_soon:
            threshold_date = datetime.now().date() + timedelta(days=days)
            query = query.filter(
                PharmacyInventory.expiry_date <= threshold_date,
                PharmacyInventory.expiry_date >= datetime.now().date()
            )
        
        inventory_items = query.all()
        
        # Calculate inventory value
        total_inventory_value = db.query(
            func.sum(PharmacyInventory.quantity_in_stock * PharmacyInventory.cost_price)
        ).scalar() or 0
        
        # Low stock count
        low_stock_count = db.query(PharmacyInventory).filter(
            PharmacyInventory.quantity_in_stock <= PharmacyInventory.low_stock_threshold
        ).count()
        
        # Expired items count
        expired_count = db.query(PharmacyInventory).filter(
            PharmacyInventory.expiry_date < datetime.now().date()
        ).count()
        
        return {
            "total_inventory_items": len(inventory_items),
            "total_inventory_value": float(total_inventory_value),
            "low_stock_items": low_stock_count,
            "expired_items": expired_count,
            "inventory_details": [
                {
                    "inventory_id": item.inventory_id,
                    "product_id": item.product_id,
                    "batch_number": item.batch_number,
                    "quantity_in_stock": item.quantity_in_stock,
                    "low_stock_threshold": item.low_stock_threshold,
                    "expiry_date": item.expiry_date.isoformat(),
                    "cost_price": float(item.cost_price),
                    "selling_price": float(item.selling_price),
                    "is_available": item.is_available,
                    "days_until_expiry": (item.expiry_date - datetime.now().date()).days
                }
                for item in inventory_items
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inventory report generation failed: {str(e)}"
        )

@router.get("/customers")
def generate_customer_report(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate customer analytics report"""
    try:
        # Customer statistics
        total_customers = db.query(Customer).filter(Customer.role == "customer").count()
        
        # New customers (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_customers = db.query(Customer).filter(
            Customer.role == "customer",
            Customer.created_at >= thirty_days_ago
        ).count()
        
        # Customers with orders
        customers_with_orders = db.query(func.count(func.distinct(Order.customer_id))).scalar()
        
        # Top customers by spending
        top_customers = db.query(
            Customer.customer_id,
            Customer.first_name,
            Customer.last_name,
            Customer.email,
            func.count(Order.order_id).label('order_count'),
            func.sum(Order.final_amount).label('total_spent')
        ).join(Order, Customer.customer_id == Order.customer_id)\
         .group_by(Customer.customer_id, Customer.first_name, Customer.last_name, Customer.email)\
         .order_by(func.sum(Order.final_amount).desc())\
         .limit(10)\
         .all()
        
        return {
            "total_customers": total_customers,
            "new_customers_30_days": new_customers,
            "customers_with_orders": customers_with_orders,
            "customer_engagement_rate": round((customers_with_orders / total_customers * 100), 2) if total_customers > 0 else 0,
            "top_customers": [
                {
                    "customer_id": customer.customer_id,
                    "name": f"{customer.first_name} {customer.last_name}",
                    "email": customer.email,
                    "order_count": customer.order_count,
                    "total_spent": float(customer.total_spent or 0)
                }
                for customer in top_customers
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Customer report generation failed: {str(e)}"
        )

@router.get("/prescriptions")
def generate_prescription_report(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate prescription analytics report"""
    try:
        # Prescription statistics
        total_prescriptions = db.query(Prescription).count()
        
        # Status distribution
        status_counts = db.query(
            Prescription.status,
            func.count(Prescription.prescription_id).label('count')
        ).group_by(Prescription.status).all()
        
        # Approval rate
        approved_count = db.query(Prescription).filter(Prescription.status == "approved").count()
        approval_rate = round((approved_count / total_prescriptions * 100), 2) if total_prescriptions > 0 else 0
        
        # Average processing time (for approved prescriptions)
        processing_times = db.query(
            func.avg(
                func.extract('epoch', Prescription.verified_at - Prescription.uploaded_at) / 3600
            )
        ).filter(
            Prescription.status == "approved",
            Prescription.verified_at.isnot(None)
        ).scalar() or 0
        
        # Monthly trend (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_trend = db.query(
            func.date_trunc('month', Prescription.uploaded_at).label('month'),
            func.count(Prescription.prescription_id).label('count')
        ).filter(Prescription.uploaded_at >= six_months_ago)\
         .group_by(func.date_trunc('month', Prescription.uploaded_at))\
         .order_by(func.date_trunc('month', Prescription.uploaded_at))\
         .all()
        
        return {
            "total_prescriptions": total_prescriptions,
            "approval_rate": approval_rate,
            "average_processing_hours": round(float(processing_times), 2),
            "status_distribution": [
                {"status": status, "count": count}
                for status, count in status_counts
            ],
            "monthly_trend": [
                {
                    "month": trend.month.strftime('%Y-%m'),
                    "prescription_count": trend.count
                }
                for trend in monthly_trend
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prescription report generation failed: {str(e)}"
        )