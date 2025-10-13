from fastapi import APIRouter, Depends
from app.core.security import require_admin
from app.models.postgres_models import Customer

router = APIRouter(prefix="/products", tags=["admin-products"])

@router.get("/")
def get_all_products(current_user: Customer = Depends(require_admin)):
    return {
        "message": f"Admin {current_user.first_name} accessing products",
        "products": []
    }