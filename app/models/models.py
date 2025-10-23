from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, Date, DateTime, Boolean,
    Enum, ForeignKey, JSON, TIMESTAMP, CHAR, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum as PyEnum
from sqlalchemy import DateTime
from datetime import datetime


Base = declarative_base()

# -------------------------------
# ENUM DEFINITIONS
# -------------------------------

class UserRole(PyEnum):
    admin = "admin"
    customer = "customer"

class Gender(PyEnum):
    male = "male"
    female = "female"
    other = "other"

class AddressType(PyEnum):
    home = "home"
    work = "work"
    other = "other"

class PrescriptionStatus(PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class OrderType(PyEnum):
    delivery = "delivery"
    pickup = "pickup"

class PaymentStatus(PyEnum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class RefundPolicy(PyEnum):
    full = "full"
    partial = "partial"
    no_refund = "no refund"

class RefundStatus(PyEnum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class NotificationType(PyEnum):
    info = "info"
    warning = "warning"
    alert = "alert"
    success = "success"


# -------------------------------
# TABLE DEFINITIONS
# -------------------------------

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Enum(Gender))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    addresses = relationship("CustomerAddress", back_populates="customer")
    prescriptions = relationship("Prescription", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    cart_items = relationship("CartItem", back_populates="customer")


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    address_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    address_type = Column(Enum(AddressType), server_default="home")
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())  # Use DateTime instead of TIMESTAMP
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Use DateTime instead of TIMESTAMP

    customer = relationship("Customer", back_populates="addresses")


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    sku = Column(String(100), unique=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    requires_prescription = Column(Boolean, default=False)
    hsn_code = Column(DECIMAL(10, 2), nullable=False)
    gst_rate = Column(DECIMAL(10, 2), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    prescription_items = relationship("PrescriptionItem", back_populates="product") 
    inventory_items = relationship("PharmacyInventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")



class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    quantity_in_stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    expiry_date = Column(Date, nullable=False)
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    is_available = Column(Boolean, default=True)
    last_restocked_date = Column(DateTime)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="inventory_items")
    order_item_batches = relationship("OrderItemBatch", back_populates="inventory")



class Prescription(Base):
    __tablename__ = "prescriptions"

    prescription_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    status = Column(Enum(PrescriptionStatus), server_default="pending")
    verified_by = Column(Integer, nullable=True)
    verification_notes = Column(Text)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    verified_at = Column(TIMESTAMP)

    #new field
    is_used = Column(Boolean, default=False)  # ✅ once used in an order, mark True
    used_in_order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)  # link to order for audit

    customer = relationship("Customer", back_populates="prescriptions")
    prescription_items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan") 


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    prescription_item_id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.prescription_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    prescription = relationship("Prescription", back_populates="prescription_items")  # Add back_populates
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(TIMESTAMP, server_default=func.now())
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    shipping_charges = Column(DECIMAL(10, 2), default=0)
    tax_amount = Column(DECIMAL(10, 2), default=0)
    discount_amount = Column(DECIMAL(10, 2), default=0)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    order_type = Column(Enum(OrderType), server_default="delivery")
    shipping_address_id = Column(Integer, ForeignKey("customer_addresses.address_id"))
    pickup_time = Column(DateTime)
    prescription_id = Column(Integer, ForeignKey("prescriptions.prescription_id"))
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), server_default="pending")
    cancellation_fee_percentage = Column(DECIMAL(5, 2), default=10.00)
    ready_at = Column(TIMESTAMP)
    picked_up_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)
    cancellation_reason = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    order_taxes = relationship("OrderTaxDetail", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="order", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="order", cascade="all, delete-orphan")
    prescription = relationship("Prescription", foreign_keys=[prescription_id])



class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    requires_prescription = Column(Boolean, default=False)
    prescription_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    order_item_batches = relationship("OrderItemBatch", back_populates="order_item")



class OrderItemBatch(Base):
    __tablename__ = "order_item_batches"

    order_item_batch_id = Column(Integer, primary_key=True, autoincrement=True)
    order_item_id = Column(Integer, ForeignKey("order_items.order_item_id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("pharmacy_inventory.inventory_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    expiry_date = Column(Date, nullable=False)
    batch_number = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    order_item = relationship("OrderItem", back_populates="order_item_batches")
    inventory = relationship("PharmacyInventory", back_populates="order_item_batches")



class OrderTaxDetail(Base):
    __tablename__ = "order_tax_details"

    tax_detail_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    hsn_code = Column(DECIMAL(10, 2), nullable=False)
    taxable_amount = Column(DECIMAL(10, 2), nullable=False)
    gst_rate = Column(DECIMAL(10, 2), nullable=False)
    gst_amount = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    order = relationship("Order", back_populates="order_taxes")



class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    payment_gateway = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(Enum(PaymentStatus), server_default="pending")
    gateway_transaction_id = Column(String(255))
    paid_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="payments")



class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    cancellation_fee = Column(DECIMAL(10, 2), default=10.00)
    refund_policy = Column(Enum(RefundPolicy), nullable=False)
    reason = Column(Text)
    status = Column(Enum(RefundStatus), server_default="pending")
    refund_method = Column(String(50))
    refund_upi_id = Column(String(255))
    bank_account_last4 = Column(CHAR(4))
    bank_name = Column(String(255))
    account_holder_name = Column(String(255))
    processed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    order = relationship("Order", back_populates="refunds")



class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    file_path = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())

    order = relationship("Order", back_populates="invoices")



class CartItem(Base):
    __tablename__ = "cart_items"

    cart_item_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    is_read = Column(Boolean, default=False)
    recipient_customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    action_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    read_at = Column(TIMESTAMP)
    
    customer = relationship("Customer")
    order = relationship("Order", back_populates="notifications")


class Backup(Base):
    __tablename__ = "backup"

    backup_id = Column(String(20), primary_key=True)
    file_name = Column(String(50), nullable=False)
    path = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    date = Column(Date, server_default=func.now())
    data_list = Column(JSON, nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('Auto','Manual')", name="check_backup_type"),
    )


class Restore(Base):
    __tablename__ = "restore"

    restore_id = Column(String(20), primary_key=True)
    file_name = Column(String(50), nullable=False)
    path = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    date = Column(Date, server_default=func.now())
    data_list = Column(JSON, nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('Auto','Manual')", name="check_restore_type"),
    )
