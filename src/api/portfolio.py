import pandas as pd
from analyzer import PortfolioAnalyzer
from api_fetcher import fetch_stock_data
from alerts import AlertManager
from report_generator import ReportGenerator

class Portfolio:
    def __init__(self):
        # Try to load existing portfolio from CSV
        try:
            self.portfolio_df = pd.read_csv('/app/data/portfolio.csv')
            self.portfolio_df['purchase_date'] = pd.to_datetime(self.portfolio_df['purchase_date'])
        except FileNotFoundError:
            self.portfolio_df = pd.DataFrame(columns=['symbol', 'quantity', 'buy_price', 'purchase_date'])
            self.portfolio_df.to_csv('/app/data/portfolio.csv', index=False)
        
        # Initialize current_price column
        if 'current_price' not in self.portfolio_df.columns:
            self.portfolio_df['current_price'] = 0.0
            
        self.analyzer = PortfolioAnalyzer(self.portfolio_df)
        self.alert_manager = AlertManager()
        self.report_generator = ReportGenerator(self.portfolio_df)
        
    def get_portfolio(self):
        # Update current prices
        for symbol in self.portfolio_df['symbol'].unique():
            try:
                current_price = fetch_stock_data(symbol)['last_price']
                self.portfolio_df.loc[self.portfolio_df['symbol'] == symbol, 'current_price'] = current_price
            except Exception as e:
                print(f"Error fetching price for {symbol}: {e}")
                
        # Calculate metrics manually to handle division by zero
        portfolio_data = []
        
        for _, row in self.portfolio_df.iterrows():
            total_value = row['quantity'] * row['current_price']
            investment = row['quantity'] * row['buy_price']
            profit_loss = total_value - investment
            try:
                profit_loss_percentage = (profit_loss / investment) * 100 if investment != 0 else 0.0
            except ZeroDivisionError:
                profit_loss_percentage = 0.0
                
            portfolio_data.append({
                'symbol': row['symbol'],
                'quantity': row['quantity'],
                'purchase_price': row['buy_price'],
                'purchase_date': row['purchase_date'],
                'current_price': row['current_price'],
                'total_value': total_value,
                'profit_loss': profit_loss,
                'profit_loss_percentage': profit_loss_percentage
            })
            
        # Save updated prices to CSV
        self.portfolio_df.to_csv('/app/data/portfolio.csv', index=False)
            
        return portfolio_data
        
    def add_stock(self, symbol, quantity, purchase_price, purchase_date):
        # Add new row to portfolio_df
        new_row = pd.DataFrame({
            'symbol': [symbol],
            'quantity': [quantity],
            'buy_price': [purchase_price],
            'purchase_date': [purchase_date],
            'current_price': [0.0]
        })
        self.portfolio_df = pd.concat([self.portfolio_df, new_row], ignore_index=True)
        self.analyzer = PortfolioAnalyzer(self.portfolio_df)
        self.report_generator = ReportGenerator(self.portfolio_df)
        
        # Save to CSV
        self.portfolio_df.to_csv('/app/data/portfolio.csv', index=False)
        
        return {"status": "success", "message": f"Added {symbol} to portfolio"}
        
    def remove_stock(self, symbol):
        return self.analyzer.remove_stock(symbol)
        
    def add_alert(self, symbol, condition, threshold, email):
        return self.alert_manager.add_alert(symbol, condition, threshold, email)
        
    def get_alerts(self):
        return self.alert_manager.get_alerts()
        
    def remove_alert(self, alert_id):
        return self.alert_manager.remove_alert(alert_id)
        
    def generate_report(self, format="pdf", include_charts=True):
        portfolio_data = self.analyzer.get_portfolio_status()
        return self.report_generator.generate_report(portfolio_data, format, include_charts)
        
    def analyze_stock(self, symbol):
        return fetch_stock_data(symbol)
