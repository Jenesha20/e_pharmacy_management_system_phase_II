from app.database import engine, SessionLocal
from app.models.models import Base, Category, Product, Customer
from app.utils.security import get_password_hash

def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create default categories
        categories = [
            Category(name="Pain Relief", description="Medicines for pain management"),
            Category(name="Antibiotics", description="Anti-bacterial medications"),
            Category(name="Vitamins", description="Vitamin and mineral supplements"),
            Category(name="First Aid", description="First aid supplies and equipment"),
            Category(name="Personal Care", description="Personal hygiene products"),
        ]
        
        for category in categories:
            existing = db.query(Category).filter(Category.name == category.name).first()
            if not existing:
                db.add(category)
        
        # Create a default admin user
        admin_user = db.query(Customer).filter(Customer.email == "admin@pharmacy.com").first()
        if not admin_user:
            admin = Customer(
                first_name="System",
                last_name="Admin",
                email="admin@pharmacy.com",
                password_hash=get_password_hash("admin123"),
                phone_number="+1234567890",
                role="admin"
            )
            db.add(admin)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()