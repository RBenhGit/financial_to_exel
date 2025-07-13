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
        # Cache for processed FCF data to avoid redundant calculations
        self._cached_fcf_data = None
        self._cached_company_folder = None
    
    def prepare_fcf_data(self, fcf_results, force_refresh=False):
        """
        Centralized FCF data preparation to avoid redundant calculations
        
        Args:
            fcf_results (dict): Raw FCF calculation results
            force_refresh (bool): Force recalculation even if cached
            
        Returns:
            dict: Processed FCF data with years, padded values, and averages
        """
        # Return cached data if available and not forcing refresh
        if not force_refresh and self._cached_fcf_data is not None:
            return self._cached_fcf_data
        
        if not fcf_results:
            return {}
        
        # Get maximum years and calculate year range
        valid_fcf_data = [values for values in fcf_results.values() if values]
        if not valid_fcf_data:
            return {}
            
        max_years = max(len(values) for values in valid_fcf_data)
        years = list(range(2024 - max_years + 1, 2025))
        
        # Prepare data for each FCF type with consistent padding
        all_fcf_data = {}
        padded_fcf_data = {}
        
        for fcf_type, values in fcf_results.items():
            if values:
                # Calculate years for this FCF type
                fcf_years = years[-len(values):]
                all_fcf_data[fcf_type] = {'years': fcf_years, 'values': values}
                
                # Pad values to match the year range length
                values_length = len(values)
                if values_length < max_years:
                    padded_values = [None] * (max_years - values_length) + values
                else:
                    padded_values = values[-max_years:]
                
                padded_fcf_data[fcf_type] = padded_values
        
        # Calculate average FCF for each year
        average_fcf = []
        for year_idx in range(max_years):
            year_values = []
            for fcf_type, values in padded_fcf_data.items():
                if values[year_idx] is not None:
                    year_values.append(values[year_idx])
            
            if year_values:
                avg_value = sum(year_values) / len(year_values)
                average_fcf.append(avg_value)
            else:
                average_fcf.append(None)
        
        # Find common years across all FCF types for plots
        all_years_sets = [set(data['years']) for data in all_fcf_data.values()]
        common_years = sorted(list(set.intersection(*all_years_sets))) if all_years_sets else []
        
        # Calculate average values for common years only (for plots)
        common_average_values = []
        if common_years:
            for year in common_years:
                year_values = []
                for fcf_type, data in all_fcf_data.items():
                    if year in data['years']:
                        year_idx = data['years'].index(year)
                        year_values.append(data['values'][year_idx])
                
                if year_values:
                    common_average_values.append(sum(year_values) / len(year_values))
                else:
                    common_average_values.append(None)
        
        # Calculate growth rates for each FCF type and periods
        growth_rates = self._calculate_growth_rates(all_fcf_data, common_years, common_average_values)
        
        # Cache the processed data
        processed_data = {
            'years': years[-max_years:],  # Full year range
            'max_years': max_years,
            'all_fcf_data': all_fcf_data,  # Original data with individual year ranges
            'padded_fcf_data': padded_fcf_data,  # Padded to same length
            'average_fcf': average_fcf,  # Average for full year range
            'common_years': common_years,  # Years common to all FCF types
            'common_average_values': common_average_values,  # Average for common years only
            'growth_rates': growth_rates  # Pre-calculated growth rates
        }
        
        self._cached_fcf_data = processed_data
        return processed_data
    
    def _calculate_growth_rates(self, all_fcf_data, common_years, common_average_values):
        """
        Calculate growth rates for all FCF types and periods
        
        Args:
            all_fcf_data (dict): FCF data by type
            common_years (list): Common years across FCF types
            common_average_values (list): Average FCF values for common years
            
        Returns:
            dict: Growth rates by FCF type and period
        """
        growth_rates = {}
        periods = list(range(1, 10))  # 1yr to 9yr to match FCF Analysis tab
        
        # Calculate growth rates for each FCF type
        for fcf_type, data in all_fcf_data.items():
            type_rates = {}
            values = data['values']
            
            for period in periods:
                if len(values) >= period + 1:
                    start_value = values[-(period + 1)]
                    end_value = values[-1]
                    
                    if start_value != 0 and start_value is not None and end_value is not None:
                        # Calculate annualized growth rate
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        # Handle sign: negative if end_value has different sign than start_value
                        if (start_value > 0 and end_value < 0) or (start_value < 0 and end_value > 0):
                            growth_rate = -growth_rate
                        elif start_value < 0 and end_value < 0:
                            growth_rate = abs(growth_rate)
                        
                        type_rates[f'{period}yr'] = growth_rate
                    else:
                        type_rates[f'{period}yr'] = None
                else:
                    type_rates[f'{period}yr'] = None
            
            growth_rates[fcf_type] = type_rates
        
        # Calculate growth rates for average FCF
        if common_average_values and len(common_average_values) >= 2:
            avg_rates = {}
            for period in periods:
                if len(common_average_values) >= period + 1:
                    start_value = common_average_values[-(period + 1)]
                    end_value = common_average_values[-1]
                    
                    if start_value != 0 and start_value is not None and end_value is not None:
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        if (start_value > 0 and end_value < 0) or (start_value < 0 and end_value > 0):
                            growth_rate = -growth_rate
                        elif start_value < 0 and end_value < 0:
                            growth_rate = abs(growth_rate)
                        
                        avg_rates[f'{period}yr'] = growth_rate
                    else:
                        avg_rates[f'{period}yr'] = None
                else:
                    avg_rates[f'{period}yr'] = None
            
            growth_rates['Average'] = avg_rates
        
        return growth_rates
    
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
        Uses centralized data preparation to avoid redundant calculations
        
        Args:
            fcf_results (dict): FCF calculation results
            company_name (str): Company name for title
            
        Returns:
            plotly.graph_objects.Figure: Interactive FCF plot
        """
        fig = go.Figure()
        
        # Use centralized data preparation
        fcf_data = self.prepare_fcf_data(fcf_results)
        if not fcf_data:
            fig.add_annotation(
                text="No FCF data available",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Colors for each FCF type
        colors = {'FCFF': '#1f77b4', 'FCFE': '#ff7f0e', 'LFCF': '#2ca02c', 'Average': '#d62728'}
        
        # Add traces for each FCF type using pre-calculated data
        for fcf_type, data in fcf_data['all_fcf_data'].items():
            color = colors.get(fcf_type, '#000000')
            fig.add_trace(go.Scatter(
                x=data['years'],
                y=data['values'],
                mode='lines+markers',
                name=fcf_type,
                line=dict(color=color, width=3),
                marker=dict(size=8),
                hovertemplate=f'<b>{fcf_type}</b><br>' +
                              'Year: %{x}<br>' +
                              'FCF: $%{y:.1f}M<extra></extra>'
            ))
        
        # Add average FCF line using pre-calculated data
        if fcf_data['common_years'] and fcf_data['common_average_values']:
            fig.add_trace(go.Scatter(
                x=fcf_data['common_years'],
                y=fcf_data['common_average_values'],
                mode='lines+markers',
                name='Average FCF',
                line=dict(color='#ff4500', width=5, dash='dash'),  # Bright orange, thicker line
                marker=dict(size=12, symbol='diamond', color='#ff4500', line=dict(width=2, color='#000000')),
                hovertemplate='<b>Average FCF</b><br>' +
                              'Year: %{x}<br>' +
                              'Avg FCF: $%{y:.1f}M<br>' +
                              '<i>Average of all FCF types</i><extra></extra>'
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
    
    def create_average_fcf_plot(self, fcf_results, company_name="Company"):
        """
        Create a dedicated plot for Average FCF trend
        Uses centralized data preparation to avoid redundant calculations
        
        Args:
            fcf_results (dict): FCF calculation results
            company_name (str): Company name for title
            
        Returns:
            plotly.graph_objects.Figure: Average FCF trend plot
        """
        fig = go.Figure()
        
        # Use centralized data preparation
        fcf_data = self.prepare_fcf_data(fcf_results)
        if not fcf_data or not fcf_data['common_years']:
            fig.add_annotation(
                text="No average FCF data available",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Add average FCF line using pre-calculated data
        fig.add_trace(go.Scatter(
            x=fcf_data['common_years'],
            y=fcf_data['common_average_values'],
            mode='lines+markers',
            name='Average FCF',
            line=dict(color='#d62728', width=4),
            marker=dict(size=10, symbol='diamond'),
            fill='tonexty',
            fillcolor='rgba(214, 39, 40, 0.1)',
            hovertemplate='<b>Average FCF</b><br>' +
                          'Year: %{x}<br>' +
                          'Avg FCF: $%{y:.1f}M<br>' +
                          '<i>Average of FCFF, FCFE, LFCF</i><extra></extra>'
        ))
        
        # Add trend line using pre-calculated data
        if len(fcf_data['common_years']) > 1:
            import numpy as np
            from scipy import stats
            
            # Calculate linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(fcf_data['common_years'], fcf_data['common_average_values'])
            trend_line = [slope * year + intercept for year in fcf_data['common_years']]
            
            fig.add_trace(go.Scatter(
                x=fcf_data['common_years'],
                y=trend_line,
                mode='lines',
                name=f'Trend (R²={r_value**2:.3f})',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='<b>Trend Line</b><br>' +
                              'Year: %{x}<br>' +
                              'Trend: $%{y:.1f}M<br>' +
                              f'Slope: ${slope:.1f}M/year<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=f'{company_name} - Average Free Cash Flow Trend',
            xaxis_title='Year',
            yaxis_title='Average FCF ($ Millions)',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=500,
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
        valid_fcf_data_slope = [values for values in fcf_results.values() if values] if fcf_results else []
        if valid_fcf_data_slope:
            max_years = max(len(values) for values in valid_fcf_data_slope)
            years = list(range(2024 - max_years + 1, 2025))
            
            for fcf_type, values in fcf_results.items():
                if values:
                    fcf_years = years[-len(values):]
                    values_millions = values  # Values already in millions
                    
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
            values.append(pv)  # Already in millions
        
        # Add terminal value
        pv_terminal = dcf_results.get('pv_terminal', 0)
        categories.append('Terminal Value')
        values.append(pv_terminal)  # Already in millions
        
        # Add total enterprise value
        enterprise_value = dcf_results.get('enterprise_value', 0)
        categories.append('Enterprise Value')
        values.append(enterprise_value)  # Already in millions
        
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
        Create sensitivity analysis heatmap showing upside/downside percentages
        
        Args:
            sensitivity_results (dict): Results from sensitivity analysis
            
        Returns:
            plotly.graph_objects.Figure: Sensitivity heatmap
        """
        if not sensitivity_results:
            return go.Figure()
        
        discount_rates = sensitivity_results['discount_rates']
        terminal_growth_rates = sensitivity_results['terminal_growth_rates']
        current_price = sensitivity_results.get('current_price', 0)
        
        # Use upside/downside data if available and current price exists
        if 'upside_downside' in sensitivity_results and current_price > 0:
            upside_data = sensitivity_results['upside_downside']
            
            # Convert to percentages for display
            upside_percentages = [[val * 100 for val in row] for row in upside_data]
            
            fig = go.Figure(data=go.Heatmap(
                z=upside_percentages,
                x=[f"{rate:.1%}" for rate in terminal_growth_rates],
                y=[f"{rate:.1%}" for rate in discount_rates],
                colorscale='RdYlGn',
                zmid=0,  # Center colorscale at 0%
                text=[[f"{val:.1f}%" for val in row] for row in upside_percentages],
                texttemplate="%{text}",
                textfont={"size": 10},
                hovertemplate='<b>Price-Based Sensitivity</b><br>' +
                              'Growth Rate: %{x}<br>' +
                              'Discount Rate: %{y}<br>' +
                              'Upside/Downside: %{z:.1f}%<br>' +
                              f'Current Price: ${current_price:.2f}<extra></extra>'
            ))
            
            title_text = f'DCF Sensitivity Analysis - Upside/Downside vs Current Price (${current_price:.2f})'
            
        else:
            # Fallback to absolute valuations if no current price
            valuations = sensitivity_results.get('valuations', [])
            
            fig = go.Figure(data=go.Heatmap(
                z=valuations,
                x=[f"{rate:.1%}" for rate in terminal_growth_rates],
                y=[f"{rate:.1%}" for rate in discount_rates],
                colorscale='RdYlGn',
                hovertemplate='<b>Sensitivity Analysis</b><br>' +
                              'Growth Rate: %{x}<br>' +
                              'Discount Rate: %{y}<br>' +
                              'Value per Share: $%{z:.2f}<extra></extra>'
            ))
            
            title_text = 'DCF Sensitivity Analysis - Fair Value per Share'
        
        fig.update_layout(
            title=title_text,
            xaxis_title='Growth Rate',
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
                # Check if values are large (likely monetary values already in millions)
                if df[col].abs().max() > 1000:
                    df[col] = df[col].apply(lambda x: f"${x:.1f}M" if pd.notna(x) else "N/A")
                else:
                    df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
        
        return df