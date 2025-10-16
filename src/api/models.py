from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class PortfolioEntry(BaseModel):
    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: datetime

class AlertRule(BaseModel):
    symbol: str
    condition: str
    threshold: float
    email: EmailStr

class PortfolioReport(BaseModel):
    format: str = "pdf"  # pdf or xlsx
    include_charts: bool = True

class PortfolioResponse(BaseModel):
    id: int
    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: datetime
    current_price: float
    total_value: float
    profit_loss: float
    profit_loss_percentage: float
    owner_id: int

    class Config:
        orm_mode = True

class AlertResponse(BaseModel):
    id: int
    symbol: str
    condition: str
    threshold: float
    email: str
    status: str
    last_checked: Optional[datetime]
    last_triggered: Optional[datetime]
    owner_id: int

    class Config:
        orm_mode = True
