from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .database_session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    portfolios = relationship("Portfolio", back_populates="owner")
    alerts = relationship("Alert", back_populates="owner")

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Integer)
    buy_price = Column(Float)
    purchase_date = Column(DateTime)
    current_price = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="portfolios")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    condition = Column(String)  # "above" or "below"
    threshold = Column(Float)
    email = Column(String)
    status = Column(String, default="active")
    last_checked = Column(DateTime)
    last_triggered = Column(DateTime)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="alerts")
