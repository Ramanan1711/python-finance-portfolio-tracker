#!/usr/bin/env python3

import pandas as pd
from tabulate import tabulate
import argparse
import os
from api_fetcher import fetch_stock_data
from analyzer import PortfolioAnalyzer
from alerts import AlertManager, start_alert_monitor
from report_generator import ReportGenerator
from rich.console import Console

console = Console()

def load_portfolio(csv_path: str) -> pd.DataFrame:
    """Load portfolio data from CSV file"""
    if not os.path.exists(csv_path):
        print(f"Error: Portfolio file not found at {csv_path}")
        return pd.DataFrame()
    
    return pd.read_csv(csv_path)

def enrich_portfolio_with_live_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add live market data to portfolio"""
    if df.empty:
        return df
    
    # Create new columns for live data
    df['current_price'] = 0.0
    
    # Fetch live data for each symbol
    for idx, row in df.iterrows():
        stock_data = fetch_stock_data(row['symbol'])
        if 'error' not in stock_data:
            df.at[idx, 'current_price'] = stock_data['current_price']
            df.at[idx, 'change_today'] = stock_data['change']
    
    return df

def handle_alerts(args):
    """Handle alert-related commands"""
    alert_manager = AlertManager()
    
    if args.add_alert:
        symbol, condition, price = args.add_alert
        try:
            price = float(price)
            if condition not in ['above', 'below']:
                raise ValueError("Condition must be 'above' or 'below'")
            
            if alert_manager.add_alert(symbol, condition, price):
                console.print(f"[green]Alert added for {symbol} {condition} ₹{price:,.2f}[/green]")
        except ValueError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    elif args.remove_alert:
        try:
            alert_id = int(args.remove_alert)
            if alert_manager.remove_alert(alert_id):
                console.print(f"[green]Alert {alert_id} removed successfully[/green]")
            else:
                console.print(f"[red]Alert {alert_id} not found[/red]")
        except ValueError:
            console.print("[red]Error: Alert ID must be a number[/red]")
    
    elif args.list_alerts:
        alert_manager.list_alerts()
    
    elif args.monitor_alerts:
        start_alert_monitor(check_interval=args.interval)

def main():
    parser = argparse.ArgumentParser(description='Portfolio Tracker CLI')
    parser.add_argument('--file', type=str, default='data/sample-portfolio.csv',
                      help='Path to portfolio CSV file')
    parser.add_argument('--analysis', action='store_true',
                      help='Show detailed portfolio analysis')
    
    # Alert related arguments
    alert_group = parser.add_argument_group('Price Alerts')
    alert_group.add_argument('--add-alert', nargs=3, metavar=('SYMBOL', 'CONDITION', 'PRICE'),
                          help='Add price alert. CONDITION must be "above" or "below"')
    alert_group.add_argument('--remove-alert', metavar='ALERT_ID',
                          help='Remove price alert by ID')
    alert_group.add_argument('--list-alerts', action='store_true',
                          help='List all active price alerts')
    alert_group.add_argument('--monitor-alerts', action='store_true',
                          help='Start alert monitoring service')
    alert_group.add_argument('--interval', type=int, default=60,
                          help='Alert check interval in seconds (default: 60)')
    
    # Export related arguments
    export_group = parser.add_argument_group('Export Options')
    export_group.add_argument('--export-pdf', action='store_true',
                           help='Export portfolio report as PDF')
    export_group.add_argument('--export-excel', action='store_true',
                           help='Export portfolio report as Excel')
    export_group.add_argument('--output', type=str,
                           help='Output filename for export')
    
    args = parser.parse_args()
    
    # Handle alert commands if any
    if any([args.add_alert, args.remove_alert, args.list_alerts, args.monitor_alerts]):
        handle_alerts(args)
        return
    
    # Load portfolio
    portfolio_df = load_portfolio(args.file)
    
    # Enrich with live data
    portfolio_df = enrich_portfolio_with_live_data(portfolio_df)
    
    # Create analyzer instance
    analyzer = PortfolioAnalyzer(portfolio_df)
    
    # Handle export options
    if args.export_pdf or args.export_excel:
        report_gen = ReportGenerator(portfolio_df)
        
        if args.export_pdf:
            filepath = report_gen.generate_pdf(args.output)
            console.print(f"\n[green]PDF report generated:[/green] {filepath}")
        
        if args.export_excel:
            filepath = report_gen.generate_excel(args.output)
            console.print(f"\n[green]Excel report generated:[/green] {filepath}")
    
    # Display portfolio information
    if args.analysis:
        # Show detailed analysis
        print(analyzer.generate_summary_report())
    else:
        # Show basic position metrics
        position_metrics = analyzer.calculate_position_metrics()
        basic_metrics = analyzer.calculate_basic_metrics()
        
        # Display current positions
        console.print("\n[bold]Current Portfolio Status:[/bold]")
        display_df = position_metrics[[
            'symbol', 'quantity', 'buy_price', 'current_price',
            'current_value', 'gain_loss', 'gain_loss_percent', 'change_today'
        ]].round(2)
        print(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))
        
        # Display basic summary
        console.print("\n[bold]Portfolio Summary:[/bold]")
        summary_data = [
            ["Total Investment", f"₹{basic_metrics['total_investment']:,.2f}"],
            ["Current Value", f"₹{basic_metrics['current_value']:,.2f}"],
            ["Total Gain/Loss", f"₹{basic_metrics['total_gain_loss']:,.2f}"],
            ["Total Return", f"{basic_metrics['gain_loss_percent']:.2f}%"]
        ]
        print(tabulate(summary_data, tablefmt='simple'))

if __name__ == '__main__':
    main()
