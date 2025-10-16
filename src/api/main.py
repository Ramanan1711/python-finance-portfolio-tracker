from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import schemas
from .models.database_session import engine, get_db
from .models.database import Base, User
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from . import crud

app = FastAPI(
    title="Portfolio Tracker API",
    description="API for tracking and managing stock portfolio with alerts and reporting capabilities",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Portfolio Tracker API is running"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login to get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.get("/portfolio", response_model=List[schemas.PortfolioResponse])
async def get_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current user's portfolio with real-time values"""
    try:
        return crud.get_user_portfolio(db=db, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/entry", response_model=schemas.PortfolioResponse)
async def add_portfolio_entry(
    entry: schemas.PortfolioEntry,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a new entry to the user's portfolio"""
    try:
        return crud.create_portfolio_entry(
            db=db,
            portfolio=entry,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/portfolio/{symbol}")
async def remove_portfolio_entry(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove an entry from the user's portfolio"""
    try:
        crud.delete_portfolio_entry(db=db, symbol=symbol, user_id=current_user.id)
        return {"status": "success", "message": f"Removed {symbol} from portfolio"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/alerts", response_model=schemas.AlertResponse)
async def create_alert(
    alert: schemas.AlertRule,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new price alert for the user"""
    try:
        return crud.create_alert(db=db, alert=alert, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/alerts", response_model=List[schemas.AlertResponse])
async def get_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all configured alerts for the user"""
    try:
        return crud.get_user_alerts(db=db, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/alerts/{alert_id}")
async def remove_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a price alert"""
    try:
        crud.delete_alert(db=db, alert_id=alert_id, user_id=current_user.id)
        return {"status": "success", "message": f"Removed alert {alert_id}"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/reports")
async def generate_report(
    report_config: schemas.PortfolioReport,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a portfolio report for the user"""
    try:
        # Generate report in the background
        background_tasks.add_task(
            crud.generate_report,
            db=db,
            user_id=current_user.id,
            format=report_config.format,
            include_charts=report_config.include_charts
        )
        return {
            "status": "success",
            "message": f"Report generation started. Format: {report_config.format}",
            "note": "Check the reports directory for the generated file."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{symbol}")
async def get_stock_analysis(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed analysis for a specific stock"""
    try:
        return crud.analyze_stock(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
