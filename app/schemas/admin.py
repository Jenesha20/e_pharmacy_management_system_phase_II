from pydantic import BaseModel,ConfigDict
from typing import Optional, List,Dict, Any
from datetime import datetime, date

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    category_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    category_id: int
    manufacturer: str
    requires_prescription: bool = False
    hsn_code: float
    gst_rate: float
    price: float
    cost_price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    manufacturer: Optional[str] = None
    requires_prescription: Optional[bool] = None
    hsn_code: Optional[float] = None
    gst_rate: Optional[float] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductWithCategory(ProductResponse):
    category_name: str
    
    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    product_id: int
    batch_number: str
    quantity_in_stock: int
    low_stock_threshold: int = 5
    expiry_date: date
    cost_price: float
    selling_price: float

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity_in_stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    is_available: Optional[bool] = None

class InventoryResponse(InventoryBase):
    inventory_id: int
    is_available: bool
    last_restocked_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InventoryWithProduct(InventoryResponse):
    product_name: str
    product_requires_prescription: bool
    
    class Config:
        from_attributes = True


class PrescriptionBase(BaseModel):
    status: str
    verification_notes: Optional[str] = None

class PrescriptionUpdate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    prescription_id: int
    customer_id: int
    image_url: str
    verified_by: Optional[int] = None
    uploaded_at: datetime
    verified_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PrescriptionWithCustomer(PrescriptionResponse):
    customer_name: str
    customer_email: str
    
    model_config = ConfigDict(from_attributes=True)

class PrescriptionItemResponse(BaseModel):
    prescription_item_id: int
    prescription_id: int
    product_id: int
    quantity: int
    created_at: datetime
    product_name: str
    requires_prescription: bool
    
    model_config = ConfigDict(from_attributes=True)

# Order Schemas
class OrderUpdate(BaseModel):
    status: str

class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    customer_id: int
    order_date: datetime
    total_amount: float
    shipping_charges: float
    tax_amount: float
    discount_amount: float
    final_amount: float
    order_type: str
    payment_method: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OrderWithCustomer(OrderResponse):
    customer_name: str
    customer_email: str
    
    model_config = ConfigDict(from_attributes=True)

class OrderItemResponse(BaseModel):
    order_item_id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    requires_prescription: bool
    prescription_verified: bool
    created_at: datetime
    product_name: str
    product_image: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class BackupCreate(BaseModel):
    type: str
    data_list: Dict[str, Any]

class RestoreCreate(BaseModel):
    path: str
    type: str

class BackupResponse(BaseModel):
    backup_id: str
    file_name: str
    path: str
    type: str
    date: datetime
    data_list: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class RestoreResponse(BaseModel):
    restore_id: str
    file_name: str
    path: str
    type: str
    date: datetime
    data_list: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

# Notification Schemas (for future use)
class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str
    recipient_customer_id: Optional[int] = None
    order_id: Optional[int] = None
    action_url: Optional[str] = None

class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    type: str
    is_read: bool
    recipient_customer_id: Optional[int] = None
    order_id: Optional[int] = None
    action_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Report Schemas (for future use)
class ReportRequest(BaseModel):
    report_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None

class SalesReport(BaseModel):
    total_sales: float
    total_orders: int
    average_order_value: float
    top_products: List[Dict[str, Any]]
    sales_by_date: List[Dict[str, Any]]