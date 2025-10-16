from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PortfolioEntry(BaseModel):
    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: datetime

class AlertRule(BaseModel):
    symbol: str
    condition: str
    threshold: float
    email: str

class PortfolioReport(BaseModel):
    format: str = "pdf"  # pdf or xlsx
    include_charts: bool = True

class PortfolioResponse(BaseModel):
    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: datetime
    current_price: float
    total_value: float
    profit_loss: float
    profit_loss_percentage: float

class AlertResponse(BaseModel):
    id: str
    symbol: str
    condition: str
    threshold: float
    email: str
    status: str
    last_checked: Optional[datetime]
    last_triggered: Optional[datetime]
