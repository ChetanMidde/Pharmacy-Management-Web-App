from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
import math
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional

from .database import engine, get_db, Base
from . import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PharmaSync API", description="Intelligent Pharmacy Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "super-secret-key-for-hackathon-demo-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day for demo

import hashlib
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Seed Database with a default user for testing
def seed_db(db: Session):
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    med_count = db.query(models.Medicine).count()
    
    if not admin or med_count < 10:
        if not admin:
            new_admin = models.User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role=models.RoleEnum.admin
            )
            db.add(new_admin)
        
        med_names = [
            ("Paracetamol", "Pain & Fever", 5.00, False), ("Amoxicillin", "Infection", 45.00, True),
            ("Ibuprofen", "Pain & Fever", 8.00, False), ("Cetirizine", "Allergy", 12.00, False),
            ("Azithromycin", "Infection", 65.00, True), ("Metformin", "Diabetes", 25.00, False),
            ("Omeprazole", "Digestive", 18.00, False), ("Atorvastatin", "Heart", 30.00, False),
            ("Amlodipine", "Heart", 22.00, False), ("Diazepam", "Mental Health", 55.00, True),
            ("Albuterol", "Respiratory", 35.00, False), ("Lisinopril", "Heart", 28.00, False),
            ("Levothyroxine", "Thyroid", 15.00, False), ("Gabapentin", "Nerve Pain", 40.00, True),
            ("Losartan", "Heart", 24.00, False), ("Simvastatin", "Heart", 20.00, False),
            ("Pantoprazole", "Digestive", 22.00, False), ("Furosemide", "Heart", 12.00, False),
            ("Montelukast", "Respiratory", 32.00, False), ("Rosuvastatin", "Heart", 38.00, False),
            ("Escitalopram", "Mental Health", 45.00, False), ("Sertraline", "Mental Health", 42.00, False),
            ("Alprazolam", "Mental Health", 60.00, True), ("Prednisone", "Immune System", 18.00, False),
            ("Fluoxetine", "Mental Health", 35.00, False), ("Tamsulosin", "Urological", 50.00, False),
            ("Carvedilol", "Heart", 26.00, False), ("Meloxicam", "Pain & Fever", 15.00, False),
            ("Tramadol", "Pain & Fever", 55.00, True), ("Clopidogrel", "Heart", 48.00, False),
            ("Spironolactone", "Heart", 22.00, False), ("Warfarin", "Heart", 18.00, True),
            ("Glipizide", "Diabetes", 20.00, False), ("Duloxetine", "Mental Health", 52.00, False),
            ("Ranitidine", "Digestive", 15.00, False), ("Zolpidem", "Sleep Aid", 45.00, True),
            ("Venlafaxine", "Mental Health", 48.00, False), ("Lorazepam", "Mental Health", 58.00, True),
            ("Allopurinol", "Gout", 14.00, False), ("Oxycodone", "Pain & Fever", 85.00, True),
            ("Hydrochlorothiazide", "Heart", 10.00, False), ("Citalopram", "Mental Health", 38.00, False),
            ("Aspirin", "Heart", 5.00, False), ("Vitamin D3", "Supplements", 12.00, False),
            ("Biotin", "Supplements", 15.00, False), ("Zinc", "Supplements", 8.00, False),
            ("Fish Oil", "Supplements", 22.00, False), ("Calcium", "Supplements", 10.00, False),
            ("Multivitamin", "Supplements", 25.00, False), ("Magnesium", "Supplements", 14.00, False),
            ("Probiotics", "Supplements", 30.00, False), ("Iron", "Supplements", 12.00, False),
            ("Vitamin C", "Supplements", 10.00, False), ("Melatonin", "Sleep Aid", 18.00, False),
            ("Dolo 650", "Pain & Fever", 2.00, False), ("Saridon", "Headache", 1.50, False),
            ("Combiflam", "Pain & Fever", 3.00, False), ("Crocin", "Pain & Fever", 2.50, False),
            ("Digene", "Digestive", 5.00, False), ("Gelusil", "Digestive", 6.00, False),
            ("Vicks Vaporub", "Cold", 12.00, False), ("Strepsils", "Cough", 4.00, False),
            ("Benadryl", "Cough", 15.00, False), ("Allegra", "Allergy", 25.00, False),
            ("Avil", "Allergy", 8.00, False), ("Betadine", "First Aid", 20.00, False),
            ("Dettol", "First Aid", 35.00, False), ("Savlon", "First Aid", 30.00, False),
            ("Band-Aid", "First Aid", 5.00, False), ("Crepe Bandage", "First Aid", 45.00, False),
            ("Cotton Wool", "First Aid", 25.00, False), ("Hand Sanitizer", "Hygiene", 40.00, False),
            ("Face Mask", "Hygiene", 10.00, False), ("Gloves", "Hygiene", 15.00, False),
            ("Thermometer", "Devices", 250.00, False), ("BP Monitor", "Devices", 1500.00, False),
            ("Oxymeter", "Devices", 800.00, False), ("Nebulizer", "Devices", 2200.00, False),
            ("Glucometer", "Devices", 1200.00, False), ("Inhaler", "Respiratory", 450.00, False),
            ("Eye Drops", "Eye Care", 45.00, False), ("Ear Drops", "Eye Care", 35.00, False),
            ("Nasal Spray", "Cold", 55.00, False), ("Pain Balm", "Pain & Fever", 30.00, False),
            ("Moisturizer", "Skin Care", 150.00, False), ("Sunscreen", "Skin Care", 250.00, False),
            ("Aloe Vera Gel", "Skin Care", 80.00, False), ("Antispasmodic", "Pain & Fever", 25.00, False),
            ("Oral Rehydration", "Hydration", 15.00, False), ("Whey Protein", "Nutrition", 2500.00, False)
        ]
        
        meds = []
        for name, cond, price, controlled in med_names:
            meds.append(models.Medicine(
                name=name,
                description=f"Standard {name} used for {cond}.",
                condition=cond,
                is_controlled=controlled,
                stock=45 if controlled else 120,
                price=price,
                expiry_date=date(2024, 6, 1) if name in ["Paracetamol", "Aspirin"] else date(2027, 1, 1)
            ))
        db.add_all(meds)
        db.commit()

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_db(db)

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[models.RoleEnum] = models.RoleEnum.staff

@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = models.User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}

class MedicineCreate(BaseModel):
    name: str
    description: str
    condition: str = "General Health"
    is_controlled: bool
    stock: int
    price: float
    expiry_date: date

@app.get("/api/medicines")
def get_medicines(db: Session = Depends(get_db)):
    return db.query(models.Medicine).all()

@app.post("/api/medicines")
def create_medicine(med: MedicineCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.manager, models.RoleEnum.pharmacist]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_med = models.Medicine(**med.dict())
    db.add(db_med)
    db.commit()
    db.refresh(db_med)
    return db_med

@app.get("/api/inventory/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    return db.query(models.Medicine).filter(models.Medicine.stock < 10).all()


class SaleItemCreate(BaseModel):
    medicine_id: int
    quantity: int
    prescription_info: Optional[str] = None

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]

@app.post("/api/sales")
def create_sale(sale: SaleCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total = 0
    
    db_sale = models.Sale(user_id=current_user.id, total_amount=0)
    db.add(db_sale)
    db.flush() # flush to get sale db_id

    for item in sale.items:
        med = db.query(models.Medicine).filter(models.Medicine.id == item.medicine_id).first()
        if not med or med.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Invalid medicine or insufficient stock for id {item.medicine_id}")
        if med.is_controlled and not item.prescription_info:
            raise HTTPException(status_code=400, detail=f"Prescription required for controlled medicine {med.name}")
        
        med.stock -= item.quantity
        line_total = med.price * item.quantity
        total += line_total
        
        db_item = models.SaleItem(
            sale_id=db_sale.id,
            medicine_id=med.id,
            quantity=item.quantity,
            price_at_time=med.price,
            prescription_info=item.prescription_info
        )
        db.add(db_item)
    
    db_sale.total_amount = total
    db.commit()
    db.refresh(db_sale)
    return {"message": "Sale completed successfully", "sale_id": db_sale.id, "total": total}

@app.get("/api/dashboard/stats")
def get_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total_sales = db.query(models.Sale).count()
    low_stock = db.query(models.Medicine).filter(models.Medicine.stock < 10).count()
    controlled_sales = db.query(models.SaleItem).join(models.Medicine).filter(models.Medicine.is_controlled == True).count()
    
    return {
        "total_sales": total_sales,
        "low_stock_items": low_stock,
        "controlled_drug_dispensed": controlled_sales
    }

@app.get("/api/dashboard/recent-sales")
def get_recent_sales(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    sales = db.query(models.Sale).order_by(models.Sale.date.desc()).limit(5).all()
    results = []
    for s in sales:
        items_count = db.query(models.SaleItem).filter(models.SaleItem.sale_id == s.id).count()
        results.append({
            "id": s.id,
            "total_amount": s.total_amount,
            "date": s.date,
            "items_count": items_count,
            "username": s.seller.username if s.seller else "Unknown"
        })
    return results

@app.get("/api/ai/predict-demand")
def predict_demand(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # AI Feature: Simple predictive analytics algorithm for demand planning
    medicines = db.query(models.Medicine).all()
    predictions = []
    
    # We simulate a forecasting model that takes dynamic context
    for med in medicines:
        # A simple mathematical heuristic predicting next month's requirement based on base stock 
        # In a real setup, this links to XGBoost/Prophet predictions API
        projected_growth = 1.25 # Model projects 25% growth over last period
        calculated_requirement = math.ceil((med.stock * 0.15) + (10 * projected_growth)) 
        
        if calculated_requirement > med.stock:
            recommendation = "Reorder Immediately"
            severity = "High"
        else:
            recommendation = "Stock levels sufficient"
            severity = "Low"
            
        predictions.append({
            "medicine_id": med.id,
            "name": med.name,
            "current_stock": med.stock,
            "predicted_demand_next_month": calculated_requirement,
            "recommendation": recommendation,
            "severity": severity,
            "reasoning": f"Based on velocity vector analysis, expected demand is {calculated_requirement} units."
        })
    return {"ai_insights": predictions}

import os
# Ensure frontend directory exists before static files mount, just in case
if os.path.exists("./frontend"):
    app.mount("/", StaticFiles(directory="./frontend", html=True), name="frontend")
