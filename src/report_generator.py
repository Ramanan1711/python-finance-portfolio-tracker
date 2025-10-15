import pandas as pd
from fpdf import FPDF
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import tempfile
from analyzer import PortfolioAnalyzer

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Portfolio Report', 0, 1, 'C')
        # Line break
        self.ln(10)
    
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)
    
    def section_title(self, title):
        # Arial 11
        self.set_font('Arial', 'B', 11)
        # Title
        self.cell(0, 6, title, 0, 1, 'L')
        # Line break
        self.ln(4)

class ReportGenerator:
    def __init__(self, portfolio_df, report_dir='reports'):
        """Initialize report generator with portfolio data"""
        self.portfolio_df = portfolio_df
        self.analyzer = PortfolioAnalyzer(portfolio_df)
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
    
    def _generate_plots(self):
        """Generate plots for the report"""
        plots = {}
        
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
        
        # Save plots to temporary files
        for name, fig in {'composition': composition_fig, 'performance': performance_fig}.items():
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            fig.write_image(temp.name)
            plots[name] = temp.name
        
        return plots
    
    def generate_excel(self, filename=None):
        """Generate Excel report with multiple sheets"""
        if filename is None:
            filename = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = os.path.join(self.report_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Portfolio Holdings Sheet
            holdings_df = self.portfolio_df[[
                'symbol', 'quantity', 'buy_price', 'current_price',
                'market_value', 'gain_loss', 'gain_loss_percent'
            ]].copy()
            
            holdings_df.to_excel(writer, sheet_name='Holdings', index=False)
            
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
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        return filepath
    
    def generate_pdf(self, filename=None):
        """Generate PDF report"""
        if filename is None:
            filename = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filepath = os.path.join(self.report_dir, filename)
        
        # Generate plots
        plot_files = self._generate_plots()
        
        try:
            # Get metrics
            metrics = self.analyzer.calculate_basic_metrics()
            risk_metrics = self.analyzer.calculate_risk_metrics()
            
            # Create PDF
            pdf = PDF()
            pdf.add_page()
            
            # Date
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
            pdf.ln(5)
            
            # Portfolio Summary
            pdf.chapter_title('Portfolio Summary')
            pdf.set_font('Arial', '', 10)
            
            summary_data = [
                ['Total Investment', f"₹{metrics['total_investment']:,.2f}"],
                ['Current Value', f"₹{metrics['current_value']:,.2f}"],
                ['Total Gain/Loss', f"₹{metrics['total_gain_loss']:,.2f}"],
                ['Total Return', f"{metrics['gain_loss_percent']:.2f}%"]
            ]
            
            for item in summary_data:
                pdf.cell(60, 6, item[0], 0, 0)
                pdf.cell(0, 6, item[1], 0, 1)
            pdf.ln(5)
            
            # Risk Analysis
            pdf.chapter_title('Risk Analysis')
            pdf.set_font('Arial', '', 10)
            
            risk_data = [
                ['Profit Factor', f"{risk_metrics['profit_factor']:.2f}"],
                ['Winning Positions', str(risk_metrics['winning_positions'])],
                ['Losing Positions', str(risk_metrics['losing_positions'])],
                ['Highest Concentration', 
                 f"{risk_metrics['concentration_stock']} ({risk_metrics['max_weight']:.1f}%)"]
            ]
            
            for item in risk_data:
                pdf.cell(60, 6, item[0], 0, 0)
                pdf.cell(0, 6, item[1], 0, 1)
            pdf.ln(5)
            
            # Holdings Table
            pdf.add_page()
            pdf.chapter_title('Portfolio Holdings')
            pdf.set_font('Arial', '', 9)
            
            # Table headers
            headers = ['Symbol', 'Quantity', 'Buy Price', 'Current', 'Value', 'Gain/Loss', 'Return']
            col_widths = [20, 20, 25, 25, 30, 30, 20]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
            pdf.ln()
            
            # Table data
            for _, row in self.portfolio_df.iterrows():
                pdf.cell(20, 6, row['symbol'], 1, 0)
                pdf.cell(20, 6, f"{row['quantity']:.0f}", 1, 0, 'R')
                pdf.cell(25, 6, f"₹{row['buy_price']:,.2f}", 1, 0, 'R')
                pdf.cell(25, 6, f"₹{row['current_price']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"₹{row['market_value']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"₹{row['gain_loss']:,.2f}", 1, 0, 'R')
                pdf.cell(20, 6, f"{row['gain_loss_percent']:.1f}%", 1, 1, 'R')
            
            # Charts
            pdf.add_page()
            pdf.chapter_title('Portfolio Visualization')
            
            # Add composition chart
            pdf.image(plot_files['composition'], x=10, w=190)
            pdf.ln(5)
            
            # Add performance chart
            pdf.image(plot_files['performance'], x=10, w=190)
            
            # Save PDF
            pdf.output(filepath)
            
        finally:
            # Clean up temporary plot files
            for plot_file in plot_files.values():
                os.unlink(plot_file)
        
        return filepath

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
