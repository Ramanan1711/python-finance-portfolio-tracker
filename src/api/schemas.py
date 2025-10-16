from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class PortfolioEntryBase(BaseModel):
    symbol: str
    shares: float
    purchase_price: float


class PortfolioEntry(PortfolioEntryBase):
    pass


class PortfolioResponse(PortfolioEntryBase):
    id: int
    owner_id: int
    current_price: Optional[float]
    last_updated: Optional[datetime]

    class Config:
        orm_mode = True


class AlertRuleBase(BaseModel):
    symbol: str
    price_threshold: float
    condition: str  # 'above' or 'below'


class AlertRule(AlertRuleBase):
    pass


class AlertResponse(AlertRuleBase):
    id: int
    owner_id: int
    last_triggered: Optional[datetime]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    

class PortfolioReport(BaseModel):
    format: str = "pdf"  # pdf or excel
    include_charts: bool = True
