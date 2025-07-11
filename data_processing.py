"""
Data Processing Module

This module handles data loading, processing, and visualization utilities for financial analysis.
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Handles data processing and visualization for financial analysis
    """
    
    def __init__(self):
        """Initialize data processor"""
        pass
    
    def validate_company_folder(self, company_folder):
        """
        Validate that company folder has the required structure
        
        Args:
            company_folder (str): Path to company folder
            
        Returns:
            dict: Validation results
        """
        validation = {
            'is_valid': False,
            'missing_folders': [],
            'missing_files': [],
            'warnings': []
        }
        
        try:
            if not os.path.exists(company_folder):
                validation['warnings'].append(f"Company folder does not exist: {company_folder}")
                return validation
            
            # Check for required subfolders
            required_folders = ['FY', 'LTM']
            for folder in required_folders:
                folder_path = os.path.join(company_folder, folder)
                if not os.path.exists(folder_path):
                    validation['missing_folders'].append(folder)
            
            # Check for required files in each subfolder
            required_files = {
                'FY': ['Income Statement', 'Balance Sheet', 'Cash Flow Statement'],
                'LTM': ['Income Statement', 'Balance Sheet', 'Cash Flow Statement']
            }
            
            for folder, file_patterns in required_files.items():
                folder_path = os.path.join(company_folder, folder)
                if os.path.exists(folder_path):
                    files_in_folder = os.listdir(folder_path)
                    for pattern in file_patterns:
                        found = any(pattern in file_name for file_name in files_in_folder)
                        if not found:
                            validation['missing_files'].append(f"{folder}/{pattern}")
            
            # Mark as valid if no missing critical components
            validation['is_valid'] = (len(validation['missing_folders']) == 0 and 
                                    len(validation['missing_files']) == 0)
            
        except Exception as e:
            validation['warnings'].append(f"Error validating folder: {e}")
            
        return validation
    
    def create_fcf_comparison_plot(self, fcf_results, company_name="Company"):
        """
        Create interactive FCF comparison plot using Plotly
        
        Args:
            fcf_results (dict): FCF calculation results
            company_name (str): Company name for title
            
        Returns:
            plotly.graph_objects.Figure: Interactive FCF plot
        """
        fig = go.Figure()
        
        # Get years for x-axis (assuming most recent years)
        if fcf_results and any(fcf_results.values()):
            max_years = max(len(values) for values in fcf_results.values() if values)
            years = list(range(2024 - max_years + 1, 2025))  # Adjust based on actual data
        else:
            years = []
        
        # Add traces for each FCF type
        colors = {'FCFF': '#1f77b4', 'FCFE': '#ff7f0e', 'LFCF': '#2ca02c'}
        
        for fcf_type, values in fcf_results.items():
            if values:
                # Ensure we have the right number of years
                fcf_years = years[-len(values):]
                
                # Convert to millions for better readability
                values_millions = [v / 1000000 for v in values]
                
                fig.add_trace(go.Scatter(
                    x=fcf_years,
                    y=values_millions,
                    mode='lines+markers',
                    name=fcf_type,
                    line=dict(color=colors.get(fcf_type, '#000000'), width=3),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{fcf_type}</b><br>' +
                                  'Year: %{x}<br>' +
                                  'FCF: $%{y:.1f}M<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title=f'{company_name} - Free Cash Flow Analysis',
            xaxis_title='Year',
            yaxis_title='Free Cash Flow ($ Millions)',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=600,
            showlegend=True
        )
        
        # Add zero line for reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        return fig
    
    def create_slope_analysis_plot(self, fcf_results, company_name="Company"):
        """
        Create slope analysis visualization
        
        Args:
            fcf_results (dict): FCF calculation results
            company_name (str): Company name for title
            
        Returns:
            plotly.graph_objects.Figure: Slope analysis plot
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Growth Rate Analysis', 'FCF Trend Comparison'),
            row_heights=[0.4, 0.6]
        )
        
        # Calculate growth rates for different periods
        periods = list(range(1, 11))  # 1-10 years
        colors = {'FCFF': '#1f77b4', 'FCFE': '#ff7f0e', 'LFCF': '#2ca02c'}
        
        for fcf_type, values in fcf_results.items():
            if values and len(values) > 1:
                growth_rates = []
                valid_periods = []
                
                for period in periods:
                    if len(values) >= period + 1:
                        start_val = values[-(period + 1)]
                        end_val = values[-1]
                        
                        if start_val != 0:
                            growth_rate = (abs(end_val) / abs(start_val)) ** (1 / period) - 1
                            if end_val < 0 and start_val > 0:
                                growth_rate = -growth_rate
                            elif end_val > 0 and start_val < 0:
                                growth_rate = abs(growth_rate)
                            
                            growth_rates.append(growth_rate * 100)  # Convert to percentage
                            valid_periods.append(period)
                
                # Add growth rate trace
                if growth_rates:
                    fig.add_trace(
                        go.Scatter(
                            x=valid_periods,
                            y=growth_rates,
                            mode='lines+markers',
                            name=f'{fcf_type} Growth',
                            line=dict(color=colors.get(fcf_type, '#000000')),
                            hovertemplate=f'<b>{fcf_type}</b><br>' +
                                          'Period: %{x} years<br>' +
                                          'CAGR: %{y:.1f}%<extra></extra>'
                        ),
                        row=1, col=1
                    )
        
        # Add FCF comparison in second subplot
        if fcf_results and any(fcf_results.values()):
            max_years = max(len(values) for values in fcf_results.values() if values)
            years = list(range(2024 - max_years + 1, 2025))
            
            for fcf_type, values in fcf_results.items():
                if values:
                    fcf_years = years[-len(values):]
                    values_millions = [v / 1000000 for v in values]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=fcf_years,
                            y=values_millions,
                            mode='lines+markers',
                            name=fcf_type,
                            line=dict(color=colors.get(fcf_type, '#000000')),
                            showlegend=False,  # Already shown in first subplot
                            hovertemplate=f'<b>{fcf_type}</b><br>' +
                                          'Year: %{x}<br>' +
                                          'FCF: $%{y:.1f}M<extra></extra>'
                        ),
                        row=2, col=1
                    )
        
        # Update layout
        fig.update_layout(
            title=f'{company_name} - FCF Growth Analysis',
            height=800,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Years", row=1, col=1)
        fig.update_yaxes(title_text="Growth Rate (%)", row=1, col=1)
        fig.update_xaxes(title_text="Year", row=2, col=1)
        fig.update_yaxes(title_text="FCF ($ Millions)", row=2, col=1)
        
        # Add zero line for growth rates
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)
        
        return fig
    
    def create_dcf_waterfall_chart(self, dcf_results):
        """
        Create DCF waterfall chart showing value breakdown
        
        Args:
            dcf_results (dict): DCF calculation results
            
        Returns:
            plotly.graph_objects.Figure: Waterfall chart
        """
        if not dcf_results or 'pv_fcf' not in dcf_results:
            return go.Figure()
        
        # Prepare data for waterfall
        categories = []
        values = []
        
        # Add projected FCF values
        pv_fcf = dcf_results.get('pv_fcf', [])
        for i, pv in enumerate(pv_fcf):
            categories.append(f'Year {i+1}')
            values.append(pv / 1000000)  # Convert to millions
        
        # Add terminal value
        pv_terminal = dcf_results.get('pv_terminal', 0)
        categories.append('Terminal Value')
        values.append(pv_terminal / 1000000)
        
        # Add total enterprise value
        enterprise_value = dcf_results.get('enterprise_value', 0)
        categories.append('Enterprise Value')
        values.append(enterprise_value / 1000000)
        
        # Create waterfall chart
        fig = go.Figure(go.Waterfall(
            name="DCF Waterfall",
            orientation="v",
            measure=["relative"] * (len(categories) - 1) + ["total"],
            x=categories,
            textposition="outside",
            text=[f"${v:.1f}M" for v in values],
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        
        fig.update_layout(
            title="DCF Valuation Waterfall",
            xaxis_title="Components",
            yaxis_title="Value ($ Millions)",
            height=500
        )
        
        return fig
    
    def create_sensitivity_heatmap(self, sensitivity_results):
        """
        Create sensitivity analysis heatmap
        
        Args:
            sensitivity_results (dict): Results from sensitivity analysis
            
        Returns:
            plotly.graph_objects.Figure: Sensitivity heatmap
        """
        if not sensitivity_results or 'valuations' not in sensitivity_results:
            return go.Figure()
        
        discount_rates = sensitivity_results['discount_rates']
        terminal_growth_rates = sensitivity_results['terminal_growth_rates']
        valuations = sensitivity_results['valuations']
        
        fig = go.Figure(data=go.Heatmap(
            z=valuations,
            x=[f"{rate:.1%}" for rate in terminal_growth_rates],
            y=[f"{rate:.1%}" for rate in discount_rates],
            colorscale='RdYlGn',
            hovertemplate='<b>Sensitivity Analysis</b><br>' +
                          'Terminal Growth: %{x}<br>' +
                          'Discount Rate: %{y}<br>' +
                          'Value per Share: $%{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='DCF Sensitivity Analysis',
            xaxis_title='Terminal Growth Rate',
            yaxis_title='Discount Rate',
            height=500
        )
        
        return fig
    
    def format_financial_table(self, data, title="Financial Data"):
        """
        Format financial data for display in Streamlit
        
        Args:
            data (dict or pd.DataFrame): Financial data to format
            title (str): Table title
            
        Returns:
            pd.DataFrame: Formatted DataFrame for display
        """
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Format monetary values
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                # Check if values are large (likely monetary)
                if df[col].abs().max() > 1000:
                    df[col] = df[col].apply(lambda x: f"${x/1000000:.1f}M" if pd.notna(x) else "N/A")
                else:
                    df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
        
        return df