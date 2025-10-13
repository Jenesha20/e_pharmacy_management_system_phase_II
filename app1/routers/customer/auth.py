from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.schemas.auth import CustomerCreate, CustomerResponse, Token, LoginRequest
from app.models.postgres_models import Customer, UserRole
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
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
        date_of_birth=customer_data.date_of_birth,
        gender=customer_data.gender,
        role=UserRole.CUSTOMER
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Find customer by email
    customer = db.query(Customer).filter(Customer.email == login_data.email).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(login_data.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(subject=customer.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": customer
    }