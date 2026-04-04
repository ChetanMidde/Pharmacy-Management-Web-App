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
from sqlalchemy.orm.session import Session
def seed_db(db: Session):
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        new_admin = models.User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role=models.RoleEnum.admin
        )
        db.add(new_admin)
        
        # Seed an expanded catalog of medicines for testing
        meds = [
            models.Medicine(name="Paracetamol 500mg", description="Pain reliever", condition="Fever & Pain", is_controlled=False, stock=150, price=15.00, expiry_date=date(2028,1,1)),
            models.Medicine(name="Amoxicillin 250mg", description="Antibiotic", condition="Infection", is_controlled=True, stock=8, price=45.00, expiry_date=date(2025,5,5)),
            models.Medicine(name="Ibuprofen 400mg", description="Anti-inflammatory", condition="Fever & Pain", is_controlled=False, stock=50, price=20.00, expiry_date=date(2026,10,1)),
            models.Medicine(name="Cetirizine 10mg", description="Antihistamine / Allergy", condition="Allergy", is_controlled=False, stock=200, price=10.00, expiry_date=date(2027,3,15)),
            
            # --- Added user-requested direct conditions ---
            models.Medicine(name="DayQuil Cold & Flu", description="Multi-symptom relief", condition="Cold", is_controlled=False, stock=40, price=25.00, expiry_date=date(2026,12,1)),
            models.Medicine(name="NyQuil Severe", description="Nighttime cold relief", condition="Cold", is_controlled=False, stock=35, price=26.50, expiry_date=date(2027,2,10)),
            models.Medicine(name="Robitussin DM", description="Cough suppressant", condition="Cough", is_controlled=False, stock=60, price=18.00, expiry_date=date(2026,5,20)),
            models.Medicine(name="Benadryl 25mg", description="Allergy & Cold relief", condition="Cold", is_controlled=False, stock=90, price=12.00, expiry_date=date(2028,8,15)),
            models.Medicine(name="Dolo 650", description="Fast Headache Relief", condition="Headache", is_controlled=False, stock=300, price=2.50, expiry_date=date(2029,1,1)),
            models.Medicine(name="Aspirin 81mg", description="Mild pain / Headache", condition="Headache", is_controlled=False, stock=110, price=8.00, expiry_date=date(2027,10,5)),
            models.Medicine(name="Tums Ultra Strength", description="Stomach ache relief", condition="Stomach Ache", is_controlled=False, stock=50, price=6.50, expiry_date=date(2028,4,12)),
            # ----------------------------------------------
            
            models.Medicine(name="Azithromycin 500mg", description="Broad-spectrum Antibiotic", condition="Infection", is_controlled=True, stock=15, price=65.00, expiry_date=date(2026,8,22)),
            models.Medicine(name="Metformin 500mg", description="Type 2 Diabetes", condition="Diabetes", is_controlled=False, stock=120, price=25.00, expiry_date=date(2028,6,30)),
            models.Medicine(name="Omeprazole 20mg", description="Antacid / Acid Reflux", condition="Digestive Health", is_controlled=False, stock=85, price=18.50, expiry_date=date(2026,11,1)),
            models.Medicine(name="Atorvastatin 20mg", description="Cholesterol management", condition="Heart Health", is_controlled=False, stock=60, price=30.00, expiry_date=date(2027,1,10)),
            models.Medicine(name="Diazepam 5mg", description="Anxiety medication", condition="Mental Health", is_controlled=True, stock=4, price=55.00, expiry_date=date(2025,9,14)),
            models.Medicine(name="Amlodipine 5mg", description="High blood pressure", condition="Heart Health", is_controlled=False, stock=75, price=22.00, expiry_date=date(2028,12,31))
        ]
        db.add_all(meds)
        db.commit()

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_db(db)

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
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

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
