from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
from typing import List

from . import schemas
from .models.database import User, Portfolio, Alert
from .auth import get_password_hash
from api_fetcher import fetch_stock_data
from report_generator import ReportGenerator

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # Check if user already exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise ValueError(f"User with email {user.email} already exists")

    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_portfolio(db: Session, user_id: int) -> List[schemas.PortfolioResponse]:
    portfolio_entries = db.query(Portfolio).filter(
        Portfolio.owner_id == user_id
    ).all()
    
    # Update current prices
    for entry in portfolio_entries:
        try:
            current_price = fetch_stock_data(entry.symbol)['last_price']
            entry.current_price = current_price
            entry.last_updated = datetime.utcnow()
        except Exception as e:
            print(f"Error fetching price for {entry.symbol}: {e}")
    
    db.commit()
    return portfolio_entries

def create_portfolio_entry(
    db: Session, portfolio: schemas.PortfolioEntry, user_id: int
) -> schemas.PortfolioResponse:
    db_portfolio = Portfolio(
        **portfolio.dict(),
        owner_id=user_id
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

def delete_portfolio_entry(db: Session, symbol: str, user_id: int):
    db_entry = db.query(Portfolio).filter(
        Portfolio.symbol == symbol,
        Portfolio.owner_id == user_id
    ).first()
    if not db_entry:
        raise ValueError(f"Portfolio entry for symbol {symbol} not found")
    db.delete(db_entry)
    db.commit()

def create_alert(
    db: Session, alert: schemas.AlertRule, user_id: int
) -> schemas.AlertResponse:
    db_alert = Alert(
        **alert.dict(),
        owner_id=user_id
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_user_alerts(db: Session, user_id: int) -> List[schemas.AlertResponse]:
    return db.query(Alert).filter(
        Alert.owner_id == user_id
    ).all()

def delete_alert(db: Session, alert_id: int, user_id: int):
    db_alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.owner_id == user_id
    ).first()
    if not db_alert:
        raise ValueError(f"Alert with ID {alert_id} not found")
    db.delete(db_alert)
    db.commit()

def generate_report(
    db: Session,
    user_id: int,
    format: str = "pdf",
    include_charts: bool = True
):
    # Get user's portfolio
    portfolio_entries = get_user_portfolio(db, user_id)
    
    # Convert to pandas DataFrame for report generation
    portfolio_data = []
    for entry in portfolio_entries:
        portfolio_data.append({
            'symbol': entry.symbol,
            'quantity': entry.quantity,
            'buy_price': entry.buy_price,
            'purchase_date': entry.purchase_date,
            'current_price': entry.current_price
        })
    
    portfolio_df = pd.DataFrame(portfolio_data)
    report_generator = ReportGenerator(portfolio_df)
    return report_generator.generate_report(format, include_charts)

def analyze_stock(symbol: str):
    return fetch_stock_data(symbol)
