from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import models
from app.routes import auth, products, cart, users, admin_products, admin_categories,admin_inventory,admin_prescriptions, admin_orders, admin_backup,admin_notifications, admin_reports,customer_orders, customer_prescriptions, customer_payments,refund,notification

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Pharmacy Management System",
    description="A comprehensive e-pharmacy backend system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(users.router)
app.include_router(customer_orders.router)
app.include_router(customer_prescriptions.router)
app.include_router(customer_payments.router)  
app.include_router(refund.router)
app.include_router(notification.router)


app.include_router(admin_categories.router)
app.include_router(admin_products.router)
app.include_router(admin_inventory.router)
app.include_router(admin_prescriptions.router)
app.include_router(admin_orders.router)
app.include_router(admin_backup.router)
app.include_router(admin_notifications.router)
app.include_router(admin_reports.router)

# @app.get("/")
# def root():
#     return {"message": "E-Pharmacy Management System API", "status": "running"}

# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "service": "e-pharmacy-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

