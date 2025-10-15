#!/usr/bin/env python3

import pandas as pd
from tabulate import tabulate
import argparse
import os

def load_portfolio(csv_path: str) -> pd.DataFrame:
    """Load portfolio data from CSV file"""
    if not os.path.exists(csv_path):
        print(f"Error: Portfolio file not found at {csv_path}")
        return pd.DataFrame()
    
    return pd.read_csv(csv_path)

def display_portfolio(df: pd.DataFrame):
    """Display portfolio in a formatted table"""
    if df.empty:
        print("No portfolio data available")
        return
    
    print("\nCurrent Portfolio:")
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

def main():
    parser = argparse.ArgumentParser(description='Portfolio Tracker CLI')
    parser.add_argument('--file', type=str, default='data/sample-portfolio.csv',
                      help='Path to portfolio CSV file')
    
    args = parser.parse_args()
    
    # Load and display portfolio
    portfolio_df = load_portfolio(args.file)
    display_portfolio(portfolio_df)

if __name__ == '__main__':
    main()
