import yfinance as yf
from typing import Dict, Optional, Any
import pandas as pd
from datetime import datetime, timedelta

def fetch_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch current stock data for the given symbol using Yahoo Finance API.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        dict: Dictionary containing current stock data
            - current_price: Current stock price
            - change: Price change
            - change_percent: Percentage change
            - volume: Trading volume
            - market_cap: Market capitalization
    """
    try:
        # Add .NS suffix for NSE stocks
        if not symbol.endswith('.NS') and not any(c.islower() for c in symbol):
            symbol = f"{symbol}.NS"
        
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get the latest price data
        current_data = stock.history(period='1d')
        if current_data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        current_price = current_data['Close'].iloc[-1]
        prev_close = info.get('previousClose', current_data['Open'].iloc[0])
        
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', 'INR' if symbol.endswith('.NS') else 'USD')
        }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return {
            'symbol': symbol,
            'error': str(e)
        }

def fetch_historical_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Fetch historical stock data for the given symbol and date range.
    
    Args:
        symbol (str): Stock symbol
        days (int): Number of days of historical data to fetch
        
    Returns:
        pd.DataFrame: DataFrame containing historical price data
    """
    try:
        if not symbol.endswith('.NS') and not any(c.islower() for c in symbol):
            symbol = f"{symbol}.NS"
            
        stock = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = stock.history(start=start_date, end=end_date)
        return df
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {str(e)}")
        return pd.DataFrame()
