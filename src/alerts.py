import json
import os
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from plyer import notification
from api_fetcher import fetch_stock_data

console = Console()

class AlertManager:
    def __init__(self, alerts_file: str = 'data/alerts.json'):
        """Initialize alert manager"""
        self.alerts_file = alerts_file
        self.alerts = self._load_alerts()
        
    def _load_alerts(self) -> Dict:
        """Load alerts from JSON file"""
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        return {'price_alerts': []}
    
    def _save_alerts(self):
        """Save alerts to JSON file"""
        os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=4)
    
    def add_alert(self, symbol: str, condition: str, target_price: float,
                  notification_type: str = 'desktop') -> bool:
        """
        Add a new price alert
        condition: 'above' or 'below'
        """
        alert = {
            'id': len(self.alerts['price_alerts']),
            'symbol': symbol.upper(),
            'condition': condition,
            'target_price': target_price,
            'notification_type': notification_type,
            'created_at': datetime.now().isoformat(),
            'triggered': False
        }
        
        self.alerts['price_alerts'].append(alert)
        self._save_alerts()
        return True
    
    def remove_alert(self, alert_id: int) -> bool:
        """Remove an alert by ID"""
        for i, alert in enumerate(self.alerts['price_alerts']):
            if alert['id'] == alert_id:
                del self.alerts['price_alerts'][i]
                self._save_alerts()
                return True
        return False
    
    def list_alerts(self) -> None:
        """Display all active alerts in a table"""
        table = Table(title="Active Price Alerts")
        
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Symbol", style="magenta")
        table.add_column("Condition", style="green")
        table.add_column("Target Price", justify="right", style="yellow")
        table.add_column("Created", style="blue")
        
        active_alerts = [a for a in self.alerts['price_alerts'] if not a['triggered']]
        
        for alert in active_alerts:
            table.add_row(
                str(alert['id']),
                alert['symbol'],
                alert['condition'],
                f"₹{alert['target_price']:,.2f}",
                datetime.fromisoformat(alert['created_at']).strftime('%Y-%m-%d %H:%M')
            )
        
        console.print(table)
    
    def check_alerts(self) -> None:
        """Check all active alerts against current prices"""
        active_alerts = [a for a in self.alerts['price_alerts'] if not a['triggered']]
        
        for alert in active_alerts:
            try:
                stock_data = fetch_stock_data(alert['symbol'])
                
                if 'error' in stock_data:
                    continue
                
                current_price = stock_data['current_price']
                triggered = False
                
                if alert['condition'] == 'below' and current_price <= alert['target_price']:
                    triggered = True
                elif alert['condition'] == 'above' and current_price >= alert['target_price']:
                    triggered = True
                
                if triggered:
                    self._trigger_alert(alert, current_price)
                    alert['triggered'] = True
                    self._save_alerts()
            
            except Exception as e:
                console.print(f"Error checking alert for {alert['symbol']}: {str(e)}", style="red")
    
    def _trigger_alert(self, alert: Dict, current_price: float) -> None:
        """Trigger the alert notification"""
        symbol = alert['symbol']
        condition = alert['condition']
        target = alert['target_price']
        
        title = f"Stock Price Alert - {symbol}"
        message = (f"{symbol} is now {'below' if condition == 'below' else 'above'} "
                  f"₹{target:,.2f}\nCurrent Price: ₹{current_price:,.2f}")
        
        # Desktop notification
        if alert['notification_type'] == 'desktop':
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=10
            )
        
        # Also print to console
        console.print(f"\n[bold red]{title}[/bold red]")
        console.print(f"[yellow]{message}[/yellow]")

def start_alert_monitor(check_interval: int = 60):
    """Start the alert monitoring service"""
    alert_manager = AlertManager()
    
    def check_job():
        console.print("\nChecking price alerts...", style="blue")
        alert_manager.check_alerts()
    
    # Schedule the check to run every minute
    schedule.every(check_interval).seconds.do(check_job)
    
    console.print(f"\n[green]Alert monitor started. Checking prices every {check_interval} seconds...[/green]")
    console.print("[yellow]Press Ctrl+C to stop monitoring.[/yellow]\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[red]Alert monitor stopped.[/red]")
