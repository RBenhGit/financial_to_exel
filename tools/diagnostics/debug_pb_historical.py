#!/usr/bin/env python3
"""
Debug script to investigate P/B historical analysis calculation failure.

DEPRECATION WARNING: This diagnostic tool uses direct yfinance imports for debugging purposes.
This is intentionally preserved for diagnostic use only. Production code should use VarInputData
for all data access. See Task 233 for details on the centralized data infrastructure migration.
"""

import sys
import os
import logging
import warnings
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# Issue deprecation warning when this module is imported
warnings.warn(
    "This diagnostic tool uses direct yfinance imports and is preserved for debugging purposes only. "
    "Production code must use VarInputData for all data access. "
    "See .taskmaster/docs/task_233_migration_strategy.md for details.",
    DeprecationWarning,
    stacklevel=2
)

# Add project path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_pb_historical_calculation(ticker_symbol='AAPL'):
    """Debug P/B historical calculation for a specific ticker."""
    logger.info(f"Starting debug for {ticker_symbol}")
    
    try:
        # Create yfinance ticker
        ticker = yf.Ticker(ticker_symbol)
        
        # Get historical price data (5 years quarterly)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)
        
        logger.info(f"Fetching price data from {start_date} to {end_date}")
        hist_prices = ticker.history(start=start_date, end=end_date, interval='3mo')
        logger.info(f"Price data shape: {hist_prices.shape}")
        logger.info(f"Price data columns: {hist_prices.columns.tolist()}")
        
        if hist_prices.empty:
            logger.error("No historical price data available!")
            return False
        
        # Get quarterly balance sheet
        logger.info("Fetching quarterly balance sheet...")
        quarterly_bs = ticker.quarterly_balance_sheet
        logger.info(f"Quarterly balance sheet shape: {quarterly_bs.shape}")
        logger.info(f"Quarterly balance sheet columns: {quarterly_bs.columns.tolist()}")
        
        if quarterly_bs.empty:
            logger.error("No quarterly balance sheet data available!")
            return False
        
        # Check balance sheet fields
        logger.info("Available balance sheet fields:")
        for i, field in enumerate(quarterly_bs.index):
            logger.info(f"  {i}: {field}")
        
        # Get shares outstanding history
        logger.info("Fetching shares outstanding...")
        try:
            shares_info = ticker.get_shares_full()
            logger.info(f"Shares info type: {type(shares_info)}")
            logger.info(f"Shares info shape: {shares_info.shape}")
            if hasattr(shares_info, 'columns'):
                logger.info(f"Shares info columns: {shares_info.columns.tolist()}")
            else:
                logger.info("Shares info is a Series")
            logger.info(f"Sample shares data:\n{shares_info.head()}")
        except Exception as e:
            logger.error(f"Error getting shares outstanding: {e}")
            shares_info = pd.DataFrame()
        
        # Try to calculate one data point manually
        logger.info("Attempting manual P/B calculation for one data point...")
        
        # Get first price date
        if not hist_prices.empty:
            first_date = hist_prices.index[0]
            first_price = hist_prices.loc[first_date, 'Close']
            logger.info(f"First price date: {first_date}, price: {first_price}")
            
            # Find closest balance sheet date (fix timezone issue)
            # Use a more recent price date to test - try the latest date
            test_date = hist_prices.index[-1]  # Most recent date
            test_price = hist_prices.loc[test_date, 'Close']
            logger.info(f"Using latest price date for testing: {test_date}, price: {test_price}")
            
            test_date_naive = test_date.tz_localize(None) if test_date.tz is not None else test_date
            closest_bs_date = None
            for bs_date in quarterly_bs.columns:
                bs_date_naive = bs_date.tz_localize(None) if bs_date.tz is not None else bs_date
                if bs_date_naive <= test_date_naive:
                    if closest_bs_date is None or bs_date_naive > (closest_bs_date.tz_localize(None) if closest_bs_date.tz is not None else closest_bs_date):
                        closest_bs_date = bs_date
            
            logger.info(f"Closest balance sheet date: {closest_bs_date}")
            
            if closest_bs_date is not None:
                bs_data = quarterly_bs[closest_bs_date]
                logger.info(f"Balance sheet data for {closest_bs_date}:")
                
                # Look for equity fields
                equity_fields = [
                    'Total Stockholder Equity',
                    'Stockholders Equity', 
                    'Total Equity',
                    'Common Stock Equity',
                    'Total Shareholders Equity'
                ]
                
                equity = None
                for field in equity_fields:
                    if field in bs_data.index and pd.notna(bs_data[field]):
                        equity = bs_data[field]
                        logger.info(f"Found equity field '{field}': {equity}")
                        break
                
                if equity is None:
                    logger.error("No equity field found in balance sheet")
                    # List available fields that might be equity
                    potential_equity_fields = [field for field in bs_data.index if 'equity' in field.lower() or 'stockholder' in field.lower()]
                    logger.info(f"Potential equity fields: {potential_equity_fields}")
                    
                    # Check if any field with 'equity' exists
                    for field in bs_data.index:
                        if 'equity' in field.lower():
                            logger.info(f"Potential equity field: {field} = {bs_data[field]}")
                else:
                    logger.info(f"Equity found: {equity}")
                    
                    # Get shares outstanding
                    shares = None
                    if not shares_info.empty:
                        # Handle both Series and DataFrame formats
                        if isinstance(shares_info, pd.Series):
                            shares_df = pd.DataFrame({'BasicShares': shares_info})
                        else:
                            shares_df = shares_info
                        
                        # Find closest shares date
                        shares_dates = shares_df.index
                        closest_shares_date = None
                        for shares_date in shares_dates:
                            shares_date_naive = shares_date.tz_localize(None) if shares_date.tz is not None else shares_date
                            if shares_date_naive <= test_date_naive:
                                if closest_shares_date is None or shares_date_naive > (closest_shares_date.tz_localize(None) if closest_shares_date.tz is not None else closest_shares_date):
                                    closest_shares_date = shares_date
                        
                        if closest_shares_date is not None:
                            # Try different column names
                            shares_columns = ['BasicShares', 'Shares', 'SharesOutstanding']
                            if hasattr(shares_df, 'columns') and len(shares_df.columns) > 0:
                                shares_columns.append(shares_df.columns[0])
                            
                            for col in shares_columns:
                                if hasattr(shares_df, 'columns') and col in shares_df.columns:
                                    shares_raw = shares_df.loc[closest_shares_date, col]
                                    logger.info(f"Raw shares data from column '{col}': {shares_raw}")
                                    # If it's a Series, take the first/most recent value
                                    if isinstance(shares_raw, pd.Series):
                                        shares = shares_raw.iloc[0] if len(shares_raw) > 0 else None
                                        logger.info(f"Extracted shares value from Series: {shares}")
                                    else:
                                        shares = shares_raw
                                    logger.info(f"Final shares outstanding from column '{col}': {shares}")
                                    if shares is not None:
                                        break
                            
                            # If still no shares and it's originally a Series
                            if shares is None and isinstance(shares_info, pd.Series):
                                shares = shares_info.loc[closest_shares_date] if closest_shares_date in shares_info.index else None
                                logger.info(f"Shares outstanding from Series: {shares}")
                        else:
                            logger.info("No shares data found for the date range")
                    
                    # Handle case where shares might still be a Series
                    if isinstance(shares, pd.Series):
                        shares = shares.iloc[0] if len(shares) > 0 else None
                        logger.info(f"Converted Series shares to scalar: {shares}")
                    
                    if shares and shares > 0 and equity > 0:
                        book_value_per_share = equity / shares
                        pb_ratio = test_price / book_value_per_share
                        logger.info(f"Calculated BVPS: {book_value_per_share}")
                        logger.info(f"Calculated P/B: {pb_ratio}")
                        return True
                    else:
                        logger.error(f"Invalid shares ({shares}) or equity ({equity})")
        
        return False
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test with a few different tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    for ticker in tickers:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing ticker: {ticker}")
        logger.info(f"{'='*50}")
        
        success = debug_pb_historical_calculation(ticker)
        logger.info(f"Result for {ticker}: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            break  # Stop at first success