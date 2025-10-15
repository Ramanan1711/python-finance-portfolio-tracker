import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import time

from api_fetcher import fetch_stock_data, fetch_historical_data
from analyzer import PortfolioAnalyzer
from alerts import AlertManager

# Page config
st.set_page_config(
    page_title="Portfolio Tracker Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize components
alert_manager = AlertManager()

def load_portfolio():
    """Load and process portfolio data"""
    df = pd.read_csv('data/sample-portfolio.csv')
    
    # Add live data
    df['current_price'] = 0.0
    df['market_value'] = 0.0
    df['gain_loss'] = 0.0
    df['gain_loss_percent'] = 0.0
    df['change_today'] = 0.0
    
    # Fetch live data
    for idx, row in df.iterrows():
        stock_data = fetch_stock_data(row['symbol'])
        if 'error' not in stock_data:
            current_price = stock_data['current_price']
            df.at[idx, 'current_price'] = current_price
            df.at[idx, 'market_value'] = current_price * row['quantity']
            df.at[idx, 'gain_loss'] = (current_price - row['buy_price']) * row['quantity']
            df.at[idx, 'gain_loss_percent'] = ((current_price - row['buy_price']) / row['buy_price']) * 100
            df.at[idx, 'change_today'] = stock_data['change']
    
    return df

def create_portfolio_summary(portfolio_df):
    """Create portfolio summary metrics"""
    analyzer = PortfolioAnalyzer(portfolio_df)
    metrics = analyzer.calculate_basic_metrics()
    risk_metrics = analyzer.calculate_risk_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Investment",
            f"₹{metrics['total_investment']:,.2f}",
            f"₹{metrics['total_gain_loss']:,.2f}"
        )
    
    with col2:
        st.metric(
            "Current Value",
            f"₹{metrics['current_value']:,.2f}",
            f"{metrics['gain_loss_percent']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Profit Factor",
            f"{risk_metrics['profit_factor']:.2f}",
            f"{risk_metrics['winning_positions']} winning positions"
        )
    
    with col4:
        st.metric(
            "Max Position",
            f"{risk_metrics['concentration_stock']}",
            f"{risk_metrics['max_weight']:.1f}% of portfolio"
        )

def plot_portfolio_composition(portfolio_df):
    """Create portfolio composition pie chart"""
    fig = px.pie(
        portfolio_df,
        values='market_value',
        names='symbol',
        title='Portfolio Composition',
        hole=0.4
    )
    st.plotly_chart(fig)

def plot_stock_performance(portfolio_df):
    """Create stock performance comparison chart"""
    fig = go.Figure()
    
    for _, row in portfolio_df.iterrows():
        hist_data = fetch_historical_data(row['symbol'], days=30)
        if not hist_data.empty:
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                name=row['symbol'],
                mode='lines'
            ))
    
    fig.update_layout(
        title='30-Day Stock Performance',
        xaxis_title='Date',
        yaxis_title='Price (₹)',
        hovermode='x unified'
    )
    st.plotly_chart(fig)

def display_alerts_section():
    """Display and manage price alerts"""
    st.subheader("Price Alerts")
    
    # Add new alert form
    with st.form("new_alert"):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Symbol").upper()
        with col2:
            condition = st.selectbox("Condition", ["above", "below"])
        with col3:
            price = st.number_input("Price", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Add Alert"):
            if symbol and price > 0:
                alert_manager.add_alert(symbol, condition, price)
                st.success(f"Alert added for {symbol} {condition} ₹{price:,.2f}")
    
    # Display active alerts
    active_alerts = pd.DataFrame(
        [a for a in alert_manager.alerts['price_alerts'] if not a['triggered']]
    )
    
    if not active_alerts.empty:
        st.dataframe(
            active_alerts[['symbol', 'condition', 'target_price', 'created_at']],
            hide_index=True
        )
    else:
        st.info("No active alerts")

def main():
    st.title("📈 Portfolio Tracker Dashboard")
    
    # Load data
    with st.spinner("Fetching latest market data..."):
        portfolio_df = load_portfolio()
    
    # Portfolio Summary
    st.subheader("Portfolio Overview")
    create_portfolio_summary(portfolio_df)
    
    # Portfolio Details
    st.subheader("Holdings")
    st.dataframe(
        portfolio_df[[
            'symbol', 'quantity', 'buy_price', 'current_price',
            'market_value', 'gain_loss', 'gain_loss_percent', 'change_today'
        ]].round(2),
        hide_index=True
    )
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        plot_portfolio_composition(portfolio_df)
    with col2:
        plot_stock_performance(portfolio_df)
    
    # Alerts Section
    display_alerts_section()
    
    # Auto-refresh
    st.sidebar.title("Settings")
    try:
        if st.sidebar.checkbox("Auto-refresh"):
            refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds)",
                min_value=5,
                max_value=300,
                value=60
            )
            st.empty()  # Clear any previous content
            time.sleep(refresh_interval)
            st.rerun()
    except Exception as e:
        st.error(f"Auto-refresh error: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        raise e
