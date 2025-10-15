import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from tabulate import tabulate

class PortfolioAnalyzer:
    def __init__(self, portfolio_df: pd.DataFrame):
        """Initialize analyzer with portfolio dataframe"""
        self.portfolio = portfolio_df
        
    def calculate_basic_metrics(self) -> Dict[str, float]:
        """Calculate basic portfolio metrics"""
        total_investment = (self.portfolio['quantity'] * self.portfolio['buy_price']).sum()
        current_value = (self.portfolio['quantity'] * self.portfolio['current_price']).sum()
        total_gain_loss = current_value - total_investment
        gain_loss_percent = (total_gain_loss / total_investment) * 100 if total_investment != 0 else 0
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'total_gain_loss': total_gain_loss,
            'gain_loss_percent': gain_loss_percent
        }
    
    def calculate_position_metrics(self) -> pd.DataFrame:
        """Calculate metrics for each position"""
        df = self.portfolio.copy()
        
        # Calculate position-wise metrics
        df['investment'] = df['quantity'] * df['buy_price']
        df['current_value'] = df['quantity'] * df['current_price']
        df['gain_loss'] = df['current_value'] - df['investment']
        df['gain_loss_percent'] = (df['gain_loss'] / df['investment']) * 100
        df['weight'] = df['current_value'] / df['current_value'].sum() * 100
        
        return df
    
    def get_best_worst_performers(self) -> Tuple[pd.Series, pd.Series]:
        """Get best and worst performing stocks"""
        position_metrics = self.calculate_position_metrics()
        best_performer = position_metrics.nlargest(1, 'gain_loss_percent').iloc[0]
        worst_performer = position_metrics.nsmallest(1, 'gain_loss_percent').iloc[0]
        
        return best_performer, worst_performer
    
    def calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate risk-related metrics"""
        position_metrics = self.calculate_position_metrics()
        
        # Calculate concentration risk
        max_weight = position_metrics['weight'].max()
        concentration_stock = position_metrics.loc[position_metrics['weight'].idxmax(), 'symbol']
        
        # Calculate profit factor (sum of gains / sum of losses)
        gains = position_metrics[position_metrics['gain_loss'] > 0]['gain_loss'].sum()
        losses = abs(position_metrics[position_metrics['gain_loss'] < 0]['gain_loss'].sum())
        profit_factor = gains / losses if losses != 0 else float('inf')
        
        return {
            'max_weight': max_weight,
            'concentration_stock': concentration_stock,
            'profit_factor': profit_factor,
            'winning_positions': len(position_metrics[position_metrics['gain_loss'] > 0]),
            'losing_positions': len(position_metrics[position_metrics['gain_loss'] < 0])
        }
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive portfolio analysis report"""
        basic_metrics = self.calculate_basic_metrics()
        position_metrics = self.calculate_position_metrics()
        best_performer, worst_performer = self.get_best_worst_performers()
        risk_metrics = self.calculate_risk_metrics()
        
        # Format basic metrics
        basic_summary = [
            ["Total Investment", f"₹{basic_metrics['total_investment']:,.2f}"],
            ["Current Value", f"₹{basic_metrics['current_value']:,.2f}"],
            ["Total Gain/Loss", f"₹{basic_metrics['total_gain_loss']:,.2f}"],
            ["Total Return", f"{basic_metrics['gain_loss_percent']:.2f}%"]
        ]
        
        # Format position-wise analysis
        position_summary = position_metrics[[
            'symbol', 'quantity', 'buy_price', 'current_price',
            'investment', 'current_value', 'gain_loss', 'gain_loss_percent', 'weight'
        ]].round(2)
        
        # Format performance analysis
        performance_summary = [
            ["Best Performer", f"{best_performer['symbol']} ({best_performer['gain_loss_percent']:.2f}%)"],
            ["Worst Performer", f"{worst_performer['symbol']} ({worst_performer['gain_loss_percent']:.2f}%)"],
            ["Winning Positions", f"{risk_metrics['winning_positions']}"],
            ["Losing Positions", f"{risk_metrics['losing_positions']}"],
            ["Profit Factor", f"{risk_metrics['profit_factor']:.2f}"],
            ["Highest Concentration", f"{risk_metrics['concentration_stock']} ({risk_metrics['max_weight']:.2f}%)"]
        ]
        
        # Build the report
        report = "\n=== Portfolio Analysis Report ===\n\n"
        report += "Basic Metrics:\n"
        report += tabulate(basic_summary, tablefmt='simple') + "\n\n"
        
        report += "Position-wise Analysis:\n"
        report += tabulate(position_summary, headers='keys', tablefmt='psql', showindex=False) + "\n\n"
        
        report += "Performance Analysis:\n"
        report += tabulate(performance_summary, tablefmt='simple')
        
        return report
