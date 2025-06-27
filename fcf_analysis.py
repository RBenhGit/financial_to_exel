import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import load_workbook
import logging
from datetime import datetime
from tkinter import filedialog, Tk
from scipy import stats

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FCFAnalyzer:
    """
    Analyzes Free Cash Flow using three different methods:
    1. Free Cash Flow to Firm (FCFF)
    2. Free Cash Flow to Equity (FCFE) 
    3. Levered Free Cash Flow (LFCF)
    """
    
    def __init__(self, company_folder):
        """
        Initialize FCF analyzer with company folder path
        
        Args:
            company_folder (str): Path to company folder containing FY and LTM subfolders
        """
        self.company_folder = company_folder
        self.company_name = os.path.basename(company_folder) if company_folder else "Unknown"
        self.financial_data = {}
        self.fcf_results = {}
        
    def load_financial_statements(self):
        """
        Load financial statements from Excel files
        """
        try:
            # Define file paths
            fy_folder = os.path.join(self.company_folder, 'FY')
            ltm_folder = os.path.join(self.company_folder, 'LTM')
            
            # Load FY statements
            for file_name in os.listdir(fy_folder):
                if 'Income Statement' in file_name:
                    self.financial_data['income_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
                elif 'Balance Sheet' in file_name:
                    self.financial_data['balance_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
                elif 'Cash Flow Statement' in file_name:
                    self.financial_data['cashflow_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
            
            # Load LTM statements
            for file_name in os.listdir(ltm_folder):
                if 'Income Statement' in file_name:
                    self.financial_data['income_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                elif 'Balance Sheet' in file_name:
                    self.financial_data['balance_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                elif 'Cash Flow Statement' in file_name:
                    self.financial_data['cashflow_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                    
            logger.info("Financial statements loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading financial statements: {e}")
            raise
    
    def _load_excel_data(self, file_path):
        """
        Load Excel data and convert to DataFrame
        
        Args:
            file_path (str): Path to Excel file
            
        Returns:
            pd.DataFrame: Financial data
        """
        try:
            wb = load_workbook(filename=file_path)
            sheet = wb.active
            
            # Convert to list of lists, then to DataFrame
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append(row)
            
            # Create DataFrame with first row as headers if possible
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data)
                
            return df
            
        except Exception as e:
            logger.error(f"Error loading Excel file {file_path}: {e}")
            raise
    
    def extract_financial_metrics(self):
        """
        Extract key financial metrics from statements
        """
        try:
            # Extract years from row 10 (Period End Date) columns 4-12
            years = []
            income_sheet = self.financial_data['income_fy']
            
            # Find the row with "Period End Date"
            period_row = None
            for row_idx in range(len(income_sheet)):
                if income_sheet.iloc[row_idx, 2] == 'Period End Date':
                    period_row = row_idx
                    break
            
            if period_row is None:
                raise ValueError("Could not find Period End Date row")
            
            # Extract years from columns 4-12 (corresponds to FY-8 to FY)
            for col_idx in range(4, 13):  # Columns 4-12
                if col_idx < len(income_sheet.columns):
                    year_val = income_sheet.iloc[period_row, col_idx]
                    if year_val and str(year_val) != 'nan':
                        # Extract year from date string like '2024-12-31'
                        year = str(year_val)[:4] if '-' in str(year_val) else str(year_val)
                        years.append(year)
            
            # Extract metrics for each year
            metrics = {}
            for year_idx, year in enumerate(years):
                col_idx = year_idx + 4  # Start from column 4
                year_metrics = {}
                
                # Extract from Income Statement
                year_metrics.update(self._extract_from_excel_sheet(
                    self.financial_data['income_fy'], col_idx, 'income'
                ))
                
                # Extract from Balance Sheet
                year_metrics.update(self._extract_from_excel_sheet(
                    self.financial_data['balance_fy'], col_idx, 'balance'
                ))
                
                # Extract from Cash Flow Statement
                year_metrics.update(self._extract_from_excel_sheet(
                    self.financial_data['cashflow_fy'], col_idx, 'cashflow'
                ))
                
                metrics[year] = year_metrics
            
            self.years = years
            self.metrics = metrics
            logger.info(f"Extracted metrics for years: {years}")
            logger.info(f"Sample metrics for {years[0] if years else 'N/A'}: {metrics.get(years[0], {}) if years else {}}")
            
        except Exception as e:
            logger.error(f"Error extracting financial metrics: {e}")
            raise
    
    def _extract_from_excel_sheet(self, df, col_idx, statement_type):
        """
        Extract specific metrics from a financial statement Excel sheet
        
        Args:
            df (pd.DataFrame): Financial statement data
            col_idx (int): Column index for the year
            statement_type (str): Type of statement ('income', 'balance', 'cashflow')
            
        Returns:
            dict: Extracted metrics
        """
        metrics = {}
        
        try:
            # Define metric mappings with partial string matching
            metric_mappings = {
                'income': {
                    'Net Income to Company': 'net_income',
                    'Operating Income': 'ebit',  # Use Operating Income as EBIT proxy
                    'Income Tax Expense': 'tax_expense',
                    'Net Interest Expenses': 'interest_expense',
                    'Revenue': 'revenue'
                },
                'balance': {
                    'Total Current Assets': 'current_assets',
                    'Total Current Liabilities': 'current_liabilities',
                    'Total Assets': 'total_assets',
                    'Total Debt': 'total_debt'
                },
                'cashflow': {
                    'Cash from Operations': 'operating_cash_flow',
                    'Capital Expenditures': 'capex',
                    'Depreciation': 'depreciation_amortization',
                    'Cash from Financing': 'financing_cash_flow'
                }
            }
            
            if statement_type in metric_mappings:
                for search_term, metric_name in metric_mappings[statement_type].items():
                    # Search for the metric in column 3 (index 2)
                    for idx, row in df.iterrows():
                        cell_value = row.iloc[2] if len(row) > 2 else None
                        if pd.notna(cell_value) and search_term in str(cell_value):
                            if col_idx < len(df.columns):
                                raw_value = row.iloc[col_idx]
                                if pd.notna(raw_value) and str(raw_value) not in ['None', 'nan', '']:
                                    try:
                                        # Handle string values like '74,989.0' or '-3,303.0'
                                        if isinstance(raw_value, str):
                                            # Remove commas and convert to float
                                            clean_value = raw_value.replace(',', '').replace('%', '')
                                            # Handle negative values in parentheses
                                            if '(' in clean_value and ')' in clean_value:
                                                clean_value = '-' + clean_value.replace('(', '').replace(')', '')
                                            metrics[metric_name] = float(clean_value)
                                        else:
                                            metrics[metric_name] = float(raw_value)
                                        
                                        logger.debug(f"Found {metric_name}: {metrics[metric_name]} for {search_term}")
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"Could not convert {raw_value} to float for {metric_name}: {e}")
                                        metrics[metric_name] = 0
                                break
                            
        except Exception as e:
            logger.warning(f"Error extracting from {statement_type} statement: {e}")
            
        return metrics
    
    def calculate_fcf_to_firm(self):
        """
        Calculate Free Cash Flow to Firm (FCFF)
        Formula: FCFF = EBIT(1 - Tax Rate) + Depreciation & Amortization - Changes in Working Capital - CapEx
        """
        fcff_values = []
        
        for year in self.years:
            try:
                metrics = self.metrics[year]
                
                # Calculate components
                ebit = metrics.get('ebit', 0)
                revenue = metrics.get('revenue', 0)
                tax_expense = metrics.get('tax_expense', 0)
                
                # Calculate tax rate from revenue and tax expense
                tax_rate = abs(tax_expense) / revenue if revenue != 0 else 0.25  # Default 25%
                
                depreciation = metrics.get('depreciation_amortization', 0)
                capex = abs(metrics.get('capex', 0))  # CapEx is usually negative
                
                # Calculate working capital change (simplified - assume 2% of revenue growth)
                wc_change = revenue * 0.02
                
                # Calculate FCFF (multiply by 1M since values are in millions)
                fcff = (ebit * (1 - tax_rate) + depreciation - wc_change - capex) * 1000000
                fcff_values.append(fcff)
                
                logger.debug(f"FCFF {year}: EBIT={ebit}, Tax Rate={tax_rate:.2%}, Dep={depreciation}, WC Change={wc_change}, CapEx={capex}, FCFF={fcff/1000000:.2f}M")
                
            except Exception as e:
                logger.warning(f"Error calculating FCFF for {year}: {e}")
                fcff_values.append(0)
        
        return fcff_values
    
    def calculate_fcf_to_equity(self):
        """
        Calculate Free Cash Flow to Equity (FCFE)
        Formula: FCFE = Net Income + Depreciation & Amortization - Changes in Working Capital - CapEx + Net Borrowing
        """
        fcfe_values = []
        
        for year in self.years:
            try:
                metrics = self.metrics[year]
                
                # Calculate components
                net_income = metrics.get('net_income', 0)
                depreciation = metrics.get('depreciation_amortization', 0)
                capex = abs(metrics.get('capex', 0))
                revenue = metrics.get('revenue', 0)
                
                # Calculate working capital change (simplified - assume 2% of revenue)
                wc_change = revenue * 0.02
                
                # Estimate net borrowing from financing cash flow
                financing_cf = metrics.get('financing_cash_flow', 0)
                net_borrowing = max(0, financing_cf)  # Only positive financing (new debt)
                
                # Calculate FCFE (multiply by 1M since values are in millions)
                fcfe = (net_income + depreciation - wc_change - capex + net_borrowing) * 1000000
                fcfe_values.append(fcfe)
                
                logger.debug(f"FCFE {year}: Net Income={net_income}, Dep={depreciation}, WC Change={wc_change}, CapEx={capex}, Net Borrowing={net_borrowing}, FCFE={fcfe/1000000:.2f}M")
                
            except Exception as e:
                logger.warning(f"Error calculating FCFE for {year}: {e}")
                fcfe_values.append(0)
        
        return fcfe_values
    
    def calculate_levered_fcf(self):
        """
        Calculate Levered Free Cash Flow (LFCF)
        Formula: LFCF = Cash Flow from Operations - CapEx
        """
        lfcf_values = []
        
        for year in self.years:
            try:
                metrics = self.metrics[year]
                
                # Calculate components
                operating_cf = metrics.get('operating_cash_flow', 0)
                capex = abs(metrics.get('capex', 0))
                
                # Calculate LFCF (multiply by 1M since values are in millions)
                lfcf = (operating_cf - capex) * 1000000
                lfcf_values.append(lfcf)
                
                logger.debug(f"LFCF {year}: Operating CF={operating_cf}, CapEx={capex}, LFCF={lfcf/1000000:.2f}M")
                
            except Exception as e:
                logger.warning(f"Error calculating LFCF for {year}: {e}")
                lfcf_values.append(0)
        
        return lfcf_values
    
    def calculate_all_fcf_types(self):
        """
        Calculate all three types of FCF
        """
        self.fcf_results['FCFF'] = self.calculate_fcf_to_firm()
        self.fcf_results['FCFE'] = self.calculate_fcf_to_equity()
        self.fcf_results['LFCF'] = self.calculate_levered_fcf()
        
        logger.info("All FCF calculations completed")
    
    def plot_fcf_comparison(self, interactive=True):
        """
        Create an interactive comparison plot of all three FCF types with linear fits and slope analysis
        
        Args:
            interactive (bool): If True, display interactive plot; if False, save as image
        """
        try:
            fig = plt.figure(figsize=(20, 12))
            ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2)  # FCF plot - spans full left vertical
            ax2 = plt.subplot2grid((2, 2), (0, 1), colspan=1)  # Slope table - top right
            ax3 = plt.subplot2grid((2, 2), (1, 1), colspan=1)  # Slope graph - bottom right
            
            # Convert values to millions for better readability
            fcff_millions = [x / 1000000 for x in self.fcf_results['FCFF']]
            fcfe_millions = [x / 1000000 for x in self.fcf_results['FCFE']]
            lfcf_millions = [x / 1000000 for x in self.fcf_results['LFCF']]
            
            # Create numeric x values for calculations
            x_numeric = np.arange(len(self.years))
            
            # Plot lines instead of bars
            ax1.plot(x_numeric, fcff_millions, marker='o', linewidth=2, markersize=8, 
                    label='FCFF (Free Cash Flow to Firm)', color='#1f77b4')
            ax1.plot(x_numeric, fcfe_millions, marker='s', linewidth=2, markersize=8, 
                    label='FCFE (Free Cash Flow to Equity)', color='#ff7f0e')
            ax1.plot(x_numeric, lfcf_millions, marker='^', linewidth=2, markersize=8, 
                    label='LFCF (Levered Free Cash Flow)', color='#2ca02c')
            
            # Add linear fits
            fcf_data = {'FCFF': fcff_millions, 'FCFE': fcfe_millions, 'LFCF': lfcf_millions}
            colors = {'FCFF': '#1f77b4', 'FCFE': '#ff7f0e', 'LFCF': '#2ca02c'}
            slope_data = {}
            
            for fcf_type, values in fcf_data.items():
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, values)
                line = slope * x_numeric + intercept
                ax1.plot(x_numeric, line, '--', color=colors[fcf_type], alpha=0.7, linewidth=1.5)
                
                # Calculate relative slopes for different periods
                slope_data[fcf_type] = self._calculate_relative_slopes(x_numeric, values)
                
            # Customize plot
            ax1.set_xlabel('Year', fontsize=12)
            ax1.set_ylabel('Free Cash Flow (Millions USD)', fontsize=12)
            ax1.set_title(f'Free Cash Flow Analysis with Linear Fits - {self.company_name}', fontsize=16, fontweight='bold')
            ax1.set_xticks(x_numeric)
            ax1.set_xticklabels(self.years, rotation=45)
            ax1.legend(fontsize=11)
            ax1.grid(True, alpha=0.3)
            
            # Create slope analysis table
            self._create_slope_table(ax2, slope_data)
            
            # Create slope analysis graph
            self._create_slope_graph(ax3, slope_data)
            
            plt.tight_layout(pad=3.0)
            
            if interactive:
                plt.show()
                logger.info("Interactive plot displayed")
            else:
                plot_path = f"fcf_comparison_{self.company_name}.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                logger.info(f"Plot saved to {plot_path}")
                
        except Exception as e:
            logger.error(f"Error creating plot: {e}")
            raise
    
    def _calculate_relative_slopes(self, x_values, y_values):
        """
        Calculate relative slopes for 1-10 year periods
        
        Args:
            x_values (array): X coordinates
            y_values (array): Y coordinates
            
        Returns:
            dict: Relative slopes in percentage
        """
        slopes = {}
        n = len(x_values)
        
        # Define periods from 1 to 10 years (or max available data)
        for period_years in range(1, min(11, n + 1)):
            period_name = f'{period_years}y'
            
            if period_years == 1:
                # For 1-year, calculate year-over-year change if we have at least 2 points
                if n >= 2:
                    # Use last two points for 1-year change
                    current_value = y_values[-1]
                    previous_value = y_values[-2]
                    if previous_value != 0:
                        yoy_change = ((current_value - previous_value) / abs(previous_value)) * 100
                        slopes[period_name] = yoy_change
                    else:
                        slopes[period_name] = 0
                else:
                    slopes[period_name] = 0
            else:
                # For multi-year periods, use linear regression
                if period_years <= n:
                    # Take the last period_years points
                    period_x = x_values[-period_years:]
                    period_y = y_values[-period_years:]
                    
                    if len(period_x) >= 2:
                        slope, _, _, _, _ = stats.linregress(period_x, period_y)
                        
                        # Calculate annualized relative slope as percentage
                        initial_value = period_y[0] if period_y[0] != 0 else 1
                        # Annualize the slope (slope per year)
                        annualized_slope = slope / abs(initial_value) * 100
                        slopes[period_name] = annualized_slope
                    else:
                        slopes[period_name] = 0
                else:
                    slopes[period_name] = 0
                
        return slopes
    
    def _create_slope_table(self, ax, slope_data):
        """
        Create a table showing relative slopes for each FCF type from 1-10 years
        
        Args:
            ax: Matplotlib axis for the table
            slope_data (dict): Slope data for each FCF type
        """
        ax.axis('off')
        ax.set_title('Annualized Slope Analysis (%)', fontsize=14, fontweight='bold', pad=20)
        
        # Get all available periods dynamically (1y to 10y)
        all_periods = set()
        for fcf_type in slope_data:
            all_periods.update(slope_data[fcf_type].keys())
        
        # Sort periods numerically (1y, 2y, 3y, etc.)
        periods = sorted(all_periods, key=lambda x: int(x.replace('y', '')))
        
        # Prepare table data
        table_data = []
        for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
            row = [fcf_type]
            for period in periods:
                slope_val = slope_data[fcf_type].get(period, 0)
                if slope_val == 0:
                    row.append("N/A")
                else:
                    row.append(f"{slope_val:.1f}%")
            table_data.append(row)
        
        # Add average row
        avg_row = ["Average"]
        for period in periods:
            period_slopes = []
            for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
                slope_val = slope_data[fcf_type].get(period, 0)
                if slope_val != 0:  # Only include valid slopes
                    period_slopes.append(slope_val)
            
            if period_slopes:
                avg_slope = sum(period_slopes) / len(period_slopes)
                avg_row.append(f"{avg_slope:.1f}%")
            else:
                avg_row.append("N/A")
        
        table_data.append(avg_row)
        
        # Create table with dynamic column count
        headers = ['FCF Type'] + periods
        table = ax.table(cellText=table_data,
                        colLabels=headers,
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0.1, 1, 0.8])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)  # Smaller font for more columns
        table.scale(1.0, 1.8)  # Adjust scaling for more columns
        
        # Color code the cells based on slope values
        for i in range(len(table_data)):
            for j in range(1, len(headers)):
                cell_val = table_data[i][j-1]  # Get the actual cell value
                if j > 0 and cell_val != "N/A":  # Skip FCF Type column and N/A values
                    try:
                        slope_val = float(cell_val.replace('%', ''))
                        if i == len(table_data) - 1:  # Average row
                            if slope_val > 0:
                                table[(i+1, j)].set_facecolor('#FFD700')  # Gold for positive average
                            elif slope_val < 0:
                                table[(i+1, j)].set_facecolor('#FFA500')  # Orange for negative average
                            else:
                                table[(i+1, j)].set_facecolor('#F0F0F0')  # Light gray for zero
                        else:  # Regular FCF rows
                            if slope_val > 0:
                                table[(i+1, j)].set_facecolor('#90EE90')  # Light green for positive
                            elif slope_val < 0:
                                table[(i+1, j)].set_facecolor('#FFB6C1')  # Light red for negative
                            else:
                                table[(i+1, j)].set_facecolor('#F0F0F0')  # Light gray for zero
                    except ValueError:
                        table[(i+1, j)].set_facecolor('#F0F0F0')  # Light gray for N/A
                elif cell_val == "N/A":
                    if i == len(table_data) - 1:  # Average row
                        table[(i+1, j)].set_facecolor('#E0E0E0')  # Darker gray for N/A in average
                    else:
                        table[(i+1, j)].set_facecolor('#E0E0E0')  # Darker gray for N/A
        
        # Style header row
        for j in range(len(headers)):
            table[(0, j)].set_facecolor('#4472C4')
            table[(0, j)].set_text_props(weight='bold', color='white')
        
        # Style average row label
        table[(len(table_data), 0)].set_text_props(weight='bold')
        table[(len(table_data), 0)].set_facecolor('#D3D3D3')  # Light gray background for average row label
            
        # Add explanation text
        ax.text(0.5, 0.05, '1y = Year-over-Year change, 2y+ = Annualized linear regression slope', 
                ha='center', va='bottom', fontsize=10, style='italic', transform=ax.transAxes)
    
    def _create_slope_graph(self, ax, slope_data):
        """
        Create a graph showing annualized slopes and their average
        
        Args:
            ax: Matplotlib axis for the graph
            slope_data (dict): Slope data for each FCF type
        """
        # Get all available periods dynamically (excluding 1y since it's YoY change, not annualized slope)
        all_periods = set()
        for fcf_type in slope_data:
            all_periods.update(slope_data[fcf_type].keys())
        
        # Sort periods numerically and exclude 1y for slope analysis
        periods = sorted([p for p in all_periods if p != '1y'], key=lambda x: int(x.replace('y', '')))
        
        if not periods:
            ax.text(0.5, 0.5, 'Insufficient data for slope analysis', 
                   ha='center', va='center', fontsize=14, transform=ax.transAxes)
            ax.axis('off')
            return
        
        # Extract period numbers for x-axis
        period_numbers = [int(p.replace('y', '')) for p in periods]
        
        # Plot slopes for each FCF type
        colors = {'FCFF': '#1f77b4', 'FCFE': '#ff7f0e', 'LFCF': '#2ca02c'}
        markers = {'FCFF': 'o', 'FCFE': 's', 'LFCF': '^'}
        
        avg_slopes = []
        
        for period in periods:
            period_slopes = []
            for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
                slope_val = slope_data[fcf_type].get(period, 0)
                if slope_val != 0:  # Only include valid slopes
                    period_slopes.append(slope_val)
            
            # Calculate average for this period
            if period_slopes:
                avg_slopes.append(sum(period_slopes) / len(period_slopes))
            else:
                avg_slopes.append(0)
        
        # Plot individual FCF slopes
        for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
            y_values = []
            for period in periods:
                slope_val = slope_data[fcf_type].get(period, 0)
                y_values.append(slope_val if slope_val != 0 else None)
            
            # Plot line, handling None values
            valid_indices = [i for i, val in enumerate(y_values) if val is not None]
            if valid_indices:
                valid_x = [period_numbers[i] for i in valid_indices]
                valid_y = [y_values[i] for i in valid_indices]
                
                ax.plot(valid_x, valid_y, marker=markers[fcf_type], linewidth=2, 
                       markersize=8, label=fcf_type, color=colors[fcf_type], alpha=0.8)
        
        # Plot average line
        valid_avg_indices = [i for i, val in enumerate(avg_slopes) if val != 0]
        if valid_avg_indices:
            valid_avg_x = [period_numbers[i] for i in valid_avg_indices]
            valid_avg_y = [avg_slopes[i] for i in valid_avg_indices]
            
            ax.plot(valid_avg_x, valid_avg_y, marker='D', linewidth=3, 
                   markersize=10, label='Average', color='red', alpha=0.9, linestyle='--')
        
        # Customize the graph
        ax.set_xlabel('Time Period (Years)', fontsize=12)
        ax.set_ylabel('Annualized Slope (%)', fontsize=12)
        ax.set_title('Annualized Linear Regression Slopes by Time Period', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Set x-axis ticks to show all available periods
        ax.set_xticks(period_numbers)
        ax.set_xticklabels([f'{p}y' for p in period_numbers])
        
        # Add horizontal line at y=0 for reference
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    
    def print_fcf_summary(self):
        """
        Print a summary of FCF calculations
        """
        print("\n" + "="*60)
        print("FREE CASH FLOW ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\nYears analyzed: {', '.join(self.years)}")
        
        for fcf_type, values in self.fcf_results.items():
            print(f"\n{fcf_type} (in millions):")
            for year, value in zip(self.years, values):
                print(f"  {year}: ${value/1000000:.2f}M")
        
        # Calculate averages
        print(f"\nAverage FCF (in millions):")
        for fcf_type, values in self.fcf_results.items():
            avg_value = sum(values) / len(values) if values else 0
            print(f"  {fcf_type}: ${avg_value/1000000:.2f}M")

def select_company_folder():
    """
    Allow user to select company folder containing financial statements
    
    Returns:
        str: Selected folder path
    """
    root = Tk()
    root.withdraw()  # Hide the main window
    
    folder_path = filedialog.askdirectory(
        title="Select Company Folder (containing FY and LTM subfolders)",
        initialdir=os.getcwd()
    )
    
    if not folder_path:
        logger.warning("No folder selected")
        return None
        
    # Validate folder structure
    fy_folder = os.path.join(folder_path, 'FY')
    ltm_folder = os.path.join(folder_path, 'LTM')
    
    if not os.path.exists(fy_folder):
        logger.error(f"FY subfolder not found in {folder_path}")
        return None
        
    if not os.path.exists(ltm_folder):
        logger.error(f"LTM subfolder not found in {folder_path}")
        return None
        
    logger.info(f"Selected company folder: {folder_path}")
    return folder_path

def main():
    """
    Main function to run FCF analysis
    """
    try:
        print("Free Cash Flow Analysis Tool")
        print("="*40)
        
        # Select company folder
        company_folder = select_company_folder()
        if not company_folder:
            print("No valid company folder selected. Exiting.")
            return
            
        # Initialize analyzer
        analyzer = FCFAnalyzer(company_folder)
        
        # Load and analyze financial data
        logger.info("Starting FCF analysis...")
        print(f"\nAnalyzing {analyzer.company_name}...")
        
        analyzer.load_financial_statements()
        analyzer.extract_financial_metrics()
        analyzer.calculate_all_fcf_types()
        
        # Display results
        analyzer.print_fcf_summary()
        
        # Create interactive plot
        print("\nGenerating interactive plot...")
        analyzer.plot_fcf_comparison(interactive=True)
        
        logger.info("FCF analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()