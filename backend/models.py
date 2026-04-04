from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
import datetime
from .database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    pharmacist = "pharmacist"
    staff = "staff"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.staff)

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    condition = Column(String, default="General Health")
    is_controlled = Column(Boolean, default=False)
    stock = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    expiry_date = Column(Date)

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    seller = relationship("User")
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer)
    price_at_time = Column(Float)
    prescription_info = Column(String, nullable=True)
    
    sale = relationship("Sale", back_populates="items")
    medicine = relationship("Medicine")
