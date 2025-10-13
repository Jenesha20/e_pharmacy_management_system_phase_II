from fastapi import APIRouter, Depends
from app.core.security import require_customer
from app.models.postgres_models import Customer

router = APIRouter(prefix="/orders", tags=["customer-orders"])

@router.get("/")
def get_my_orders(current_user: Customer = Depends(require_customer)):
    return {
        "message": f"Orders for customer {current_user.first_name}",
        "user_id": current_user.customer_id,
        "orders": []
    }