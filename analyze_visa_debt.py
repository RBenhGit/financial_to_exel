#!/usr/bin/env python3

import sys
import pandas as pd
from financial_calculations import FinancialCalculator

def analyze_visa_debt_data():
    """Analyze Visa's debt financing data to understand FCFE calculation limitations"""
    
    # Initialize calculator for Visa
    calc = FinancialCalculator('V')
    calc.load_financial_statements()

    # Get the cash flow data
    cashflow_data = calc.financial_data.get('cashflow_fy', pd.DataFrame())
    print('=== VISA CASH FLOW STATEMENT DEBT METRICS ===')

    # Check what debt metrics are available
    debt_metrics = []
    for idx, row in cashflow_data.iterrows():
        metric_text = None
        if len(row) > 2 and pd.notna(row.iloc[2]):
            metric_text = str(row.iloc[2])
        elif pd.notna(row.iloc[0]):
            metric_text = str(row.iloc[0])
        
        if metric_text and 'debt' in metric_text.lower():
            print(f'Row {idx}: {metric_text}')
            # Show the values for this debt metric
            values = []
            for val in row.iloc[3:]:
                if pd.notna(val) and str(val).strip() != '':
                    values.append(val)
            print(f'  Values ({len(values)} years): {values}')
            debt_metrics.append((metric_text, values))
            print()

    # Check for financing-related metrics
    print('=== ALL FINANCING-RELATED METRICS ===')
    financing_terms = ['financing', 'borrow', 'repay', 'issuance', 'proceeds', 'payment']
    
    for idx, row in cashflow_data.iterrows():
        metric_text = None
        if len(row) > 2 and pd.notna(row.iloc[2]):
            metric_text = str(row.iloc[2])
        elif pd.notna(row.iloc[0]):
            metric_text = str(row.iloc[0])
        
        if metric_text and any(term in metric_text.lower() for term in financing_terms):
            print(f'Row {idx}: {metric_text}')
            values = []
            for val in row.iloc[3:]:
                if pd.notna(val) and str(val).strip() != '':
                    values.append(val)
            print(f'  Values ({len(values)} years): {values}')
            print()

    # Check specific metrics the app is looking for
    print('=== SPECIFIC METRIC SEARCH ===')
    specific_metrics = ["Long-Term Debt Issued", "Long-Term Debt Repaid"]
    for metric in specific_metrics:
        values = calc._extract_metric_values(cashflow_data, metric, reverse=True)
        print(f'{metric}: {len(values)} years - {values}')

    return debt_metrics

if __name__ == "__main__":
    analyze_visa_debt_data()