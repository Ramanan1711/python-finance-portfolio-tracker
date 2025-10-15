import pandas as pd
from fpdf import FPDF
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import tempfile
from analyzer import PortfolioAnalyzer

class ReportGenerator:
    def __init__(self, portfolio_df, report_dir='reports'):
        """Initialize report generator with portfolio data"""
        self.portfolio_df = portfolio_df
        self.analyzer = PortfolioAnalyzer(portfolio_df)
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
        
        # Initialize Jinja2 environment for HTML templates
        self.env = Environment(loader=FileSystemLoader('templates'))
    
    def _generate_plots(self):
        """Generate plots for the report"""
        # Portfolio composition pie chart
        composition_fig = px.pie(
            self.portfolio_df,
            values='market_value',
            names='symbol',
            title='Portfolio Composition'
        )
        
        # Performance bar chart
        performance_df = self.portfolio_df.sort_values('gain_loss_percent', ascending=True)
        performance_fig = px.bar(
            performance_df,
            x='symbol',
            y='gain_loss_percent',
            title='Performance by Stock',
            labels={'gain_loss_percent': 'Return (%)'}
        )
        
        return {
            'composition': composition_fig,
            'performance': performance_fig
        }
    
    def generate_excel(self, filename=None):
        """Generate Excel report with multiple sheets"""
        if filename is None:
            filename = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = os.path.join(self.report_dir, filename)
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Portfolio Holdings Sheet
            holdings_df = self.portfolio_df[[
                'symbol', 'quantity', 'buy_price', 'current_price',
                'market_value', 'gain_loss', 'gain_loss_percent'
            ]].copy()
            
            holdings_df.to_excel(
                writer,
                sheet_name='Holdings',
                index=False
            )
            
            # Portfolio Summary Sheet
            metrics = self.analyzer.calculate_basic_metrics()
            risk_metrics = self.analyzer.calculate_risk_metrics()
            
            summary_data = {
                'Metric': [
                    'Total Investment',
                    'Current Value',
                    'Total Gain/Loss',
                    'Total Return (%)',
                    'Profit Factor',
                    'Winning Positions',
                    'Losing Positions',
                    'Highest Concentration'
                ],
                'Value': [
                    metrics['total_investment'],
                    metrics['current_value'],
                    metrics['total_gain_loss'],
                    metrics['gain_loss_percent'],
                    risk_metrics['profit_factor'],
                    risk_metrics['winning_positions'],
                    risk_metrics['losing_positions'],
                    f"{risk_metrics['concentration_stock']} ({risk_metrics['max_weight']:.1f}%)"
                ]
            }
            
            pd.DataFrame(summary_data).to_excel(
                writer,
                sheet_name='Summary',
                index=False
            )
            
            # Position Analysis Sheet
            analysis_df = self.portfolio_df[[
                'symbol', 'quantity', 'buy_price', 'current_price',
                'market_value', 'gain_loss', 'gain_loss_percent'
            ]].copy()
            
            analysis_df['weight'] = (
                analysis_df['market_value'] / analysis_df['market_value'].sum() * 100
            )
            
            analysis_df.to_excel(
                writer,
                sheet_name='Analysis',
                index=False
            )
        
        return filepath
    
    def generate_pdf(self, filename=None):
        """Generate PDF report using WeasyPrint"""
        if filename is None:
            filename = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filepath = os.path.join(self.report_dir, filename)
        
        # Generate plots
        plots = self._generate_plots()
        
        # Save plots as temporary files
        temp_files = []
        plot_paths = {}
        
        for name, fig in plots.items():
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            fig.write_image(temp.name)
            temp_files.append(temp)
            plot_paths[name] = temp.name
        
        try:
            # Get portfolio metrics
            metrics = self.analyzer.calculate_basic_metrics()
            risk_metrics = self.analyzer.calculate_risk_metrics()
            
            # Prepare template data
            template_data = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metrics': metrics,
                'risk_metrics': risk_metrics,
                'holdings': self.portfolio_df.to_dict('records'),
                'plot_paths': plot_paths
            }
            
            # Render HTML template
            template = self.env.get_template('portfolio_report.html')
            html_content = template.render(**template_data)
            
            # Convert HTML to PDF
            HTML(string=html_content).write_pdf(
                filepath,
                stylesheets=[CSS(string='''
                    @page { margin: 1cm; }
                    body { font-family: Arial, sans-serif; }
                    .header { text-align: center; margin-bottom: 20px; }
                    .section { margin: 20px 0; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 8px; border: 1px solid #ddd; }
                    th { background-color: #f5f5f5; }
                    .plot { margin: 20px 0; }
                ''')]
            )
            
        finally:
            # Clean up temporary files
            for temp in temp_files:
                os.unlink(temp.name)
        
        return filepath
