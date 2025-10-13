from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import create_tables

# Import routers
from app.routers.customer.auth import router as customer_auth_router
from app.routers.customer.orders import router as customer_orders_router
from app.routers.admin.products import router as admin_products_router

# Create tables on startup
create_tables()

app = FastAPI(
    title="E-Pharmacy Backend API",
    description="Backend API for E-Pharmacy Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customer_auth_router, prefix="/api/v1/customer")
app.include_router(customer_orders_router, prefix="/api/v1/customer")
app.include_router(admin_products_router, prefix="/api/v1/admin")

@app.get("/")
def read_root():
    return {"message": "Welcome to E-Pharmacy Backend API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "E-Pharmacy API is running"}