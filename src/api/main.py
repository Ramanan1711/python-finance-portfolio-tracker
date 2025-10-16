from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.portfolio import Portfolio
from api.models import (
    PortfolioEntry,
    AlertRule,
    PortfolioReport,
    PortfolioResponse,
    AlertResponse
)

app = FastAPI(
    title="Portfolio Tracker API",
    description="API for tracking and managing stock portfolio with alerts and reporting capabilities",
    version="1.0.0"
)

# Initialize portfolio
portfolio = Portfolio()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Portfolio Tracker API is running"}

@app.get("/portfolio", response_model=List[PortfolioResponse])
async def get_portfolio():
    """Get the current portfolio with real-time values"""
    try:
        portfolio_data = portfolio.get_portfolio()
        return [
            PortfolioResponse(
                symbol=entry["symbol"],
                quantity=entry["quantity"],
                purchase_price=entry["purchase_price"],
                purchase_date=entry["purchase_date"],
                current_price=entry["current_price"],
                total_value=entry["total_value"],
                profit_loss=entry["profit_loss"],
                profit_loss_percentage=entry["profit_loss_percentage"]
            )
            for entry in portfolio_data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/entry")
async def add_portfolio_entry(entry: PortfolioEntry):
    """Add a new entry to the portfolio"""
    try:
        portfolio.add_stock(
            entry.symbol,
            entry.quantity,
            entry.purchase_price,
            entry.purchase_date
        )
        return {"status": "success", "message": f"Added {entry.symbol} to portfolio"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/portfolio/{symbol}")
async def remove_portfolio_entry(symbol: str):
    """Remove an entry from the portfolio"""
    try:
        portfolio.remove_stock(symbol)
        return {"status": "success", "message": f"Removed {symbol} from portfolio"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/alerts")
async def create_alert(alert: AlertRule):
    """Create a new price alert"""
    try:
        portfolio.add_alert(
            alert.symbol,
            alert.condition,
            alert.threshold,
            alert.email
        )
        return {"status": "success", "message": f"Created alert for {alert.symbol}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """Get all configured alerts"""
    try:
        alerts = portfolio.get_alerts()
        return [
            AlertResponse(
                id=str(alert["id"]),
                symbol=alert["symbol"],
                condition=alert["condition"],
                threshold=alert["threshold"],
                email=alert["email"],
                status=alert["status"],
                last_checked=alert.get("last_checked"),
                last_triggered=alert.get("last_triggered")
            )
            for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/alerts/{alert_id}")
async def remove_alert(alert_id: str):
    """Remove a price alert"""
    try:
        portfolio.remove_alert(alert_id)
        return {"status": "success", "message": f"Removed alert {alert_id}"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/reports")
async def generate_report(report_config: PortfolioReport, background_tasks: BackgroundTasks):
    """Generate a portfolio report"""
    try:
        # Generate report in the background
        background_tasks.add_task(
            portfolio.generate_report,
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
async def get_stock_analysis(symbol: str):
    """Get detailed analysis for a specific stock"""
    try:
        analysis = portfolio.analyze_stock(symbol)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
