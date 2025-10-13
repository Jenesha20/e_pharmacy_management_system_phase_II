from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import models
from app.routes import auth, products

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
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)

@app.get("/")
def root():
    return {"message": "E-Pharmacy Management System API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "e-pharmacy-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)