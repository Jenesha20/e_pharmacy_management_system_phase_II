from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Customer
from app.schemas.auth import CustomerCreate, CustomerLogin, Token, UserRole
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
def register(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_customer = db.query(Customer).filter(Customer.email == customer_data.email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new customer
    hashed_password = get_password_hash(customer_data.password)
    customer = Customer(
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        email=customer_data.email,
        password_hash=hashed_password,
        phone_number=customer_data.phone_number,
        role=UserRole.customer,
        date_of_birth=customer_data.date_of_birth,
        gender=customer_data.gender
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": customer.customer_id, "role": customer.role},
        expires_delta=timedelta(days=7)  # Longer expiry for better UX
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=customer.customer_id,
        role=customer.role
    )

@router.post("/login", response_model=Token)
def login(login_data: CustomerLogin, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.email == login_data.email).first()
    if not customer or not verify_password(login_data.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"user_id": customer.customer_id, "role": customer.role},
        expires_delta=timedelta(days=7)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=customer.customer_id,
        role=customer.role
    )