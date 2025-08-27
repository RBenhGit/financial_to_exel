"""
P/B Calculation Engine for Generalized Data Responses
====================================================

This module provides a unified P/B (Price-to-Book) ratio calculation engine that processes
DataSourceResponse objects from various financial data providers for historical analysis.

Key Features:
- Parse DataSourceResponse objects for P/B calculation data
- Extract book value, shares outstanding, and historical prices
- Data consistency validation using existing patterns
- Multi-source data reconciliation and unit conversions
- Quarterly P/B ratio calculation from historical data
- Support for multiple data source formats (Alpha Vantage, FMP, Polygon, yfinance)

Classes:
--------
PBCalculationEngine
    Main engine class for processing DataSourceResponse objects and calculating P/B ratios

Usage Example:
--------------
>>> from pb_calculation_engine import PBCalculationEngine
>>> from data_sources import DataSourceResponse, FinancialDataRequest
>>> 
>>> engine = PBCalculationEngine()
>>> 
>>> # Process a DataSourceResponse for current P/B calculation
>>> current_pb = engine.calculate_current_pb(data_response)
>>> print(f"Current P/B: {current_pb['pb_ratio']:.2f}")
>>> 
>>> # Process historical data for P/B trend analysis
>>> historical_pb = engine.calculate_historical_pb(historical_response)
>>> print(f"Historical P/B data points: {len(historical_pb)}")
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass

from core.data_sources.interfaces.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics

logger = logging.getLogger(__name__)


@dataclass
class PBDataPoint:
    """Single P/B ratio data point with metadata"""
    
    date: str
    price: Optional[float] = None
    book_value_per_share: Optional[float] = None
    pb_ratio: Optional[float] = None
    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    source_type: Optional[DataSourceType] = None
    data_quality: Optional[float] = None


@dataclass
class PBCalculationResult:
    """Result of P/B calculation with metadata"""
    
    success: bool
    pb_ratio: Optional[float] = None
    book_value_per_share: Optional[float] = None
    current_price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    data_source: Optional[DataSourceType] = None
    calculation_date: Optional[str] = None
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None
    validation_notes: Optional[List[str]] = None


class PBCalculationEngine:
    """
    Engine for calculating P/B ratios from DataSourceResponse objects.
    
    This engine can process various data source formats and provides consistent
    P/B ratio calculations with data validation and quality assessment.
    """
    
    def __init__(self):
        """Initialize the P/B calculation engine"""
        self.supported_sources = {
            DataSourceType.ALPHA_VANTAGE,
            DataSourceType.FINANCIAL_MODELING_PREP,
            DataSourceType.POLYGON,
            DataSourceType.YFINANCE,
            DataSourceType.EXCEL
        }
        
        # Field mapping for different data sources
        self.equity_field_mappings = {
            DataSourceType.ALPHA_VANTAGE: [
                'totalStockholderEquity',
                'totalShareholderEquity', 
                'stockholderEquity',
                'totalEquity'
            ],
            DataSourceType.FINANCIAL_MODELING_PREP: [
                'totalStockholdersEquity',
                'totalShareholdersEquity',
                'stockholdersEquity',
                'totalEquity'
            ],
            DataSourceType.POLYGON: [
                'equity',
                'stockholders_equity',
                'total_equity'
            ],
            DataSourceType.YFINANCE: [
                'Total Stockholder Equity',
                'Stockholders Equity',
                'Total Equity'
            ]
        }
        
        self.shares_field_mappings = {
            DataSourceType.ALPHA_VANTAGE: [
                'commonSharesOutstanding',
                'sharesOutstanding',
                'weightedAverageShsOut'
            ],
            DataSourceType.FINANCIAL_MODELING_PREP: [
                'weightedAverageShsOut',
                'sharesOutstanding',
                'commonSharesOutstanding'
            ],
            DataSourceType.POLYGON: [
                'shares_outstanding',
                'weighted_average_shares'
            ],
            DataSourceType.YFINANCE: [
                'sharesOutstanding',
                'impliedSharesOutstanding'
            ]
        }
        
        logger.info("P/B Calculation Engine initialized")
    
    def calculate_current_pb(self, response: DataSourceResponse) -> PBCalculationResult:
        """
        Calculate current P/B ratio from a DataSourceResponse object.
        
        Args:
            response (DataSourceResponse): Response containing financial data
            
        Returns:
            PBCalculationResult: Calculation result with P/B ratio and metadata
        """
        try:
            if not response.success or not response.data:
                return PBCalculationResult(
                    success=False,
                    error_message="Invalid or unsuccessful data response"
                )
            
            # Extract current price
            current_price = self._extract_current_price(response)
            if current_price is None or current_price <= 0:
                return PBCalculationResult(
                    success=False,
                    error_message="Could not extract valid current price"
                )
            
            # Extract book value per share
            book_value_per_share = self._extract_book_value_per_share(response)
            if book_value_per_share is None or book_value_per_share <= 0:
                return PBCalculationResult(
                    success=False,
                    error_message="Could not extract valid book value per share"
                )
            
            # Calculate P/B ratio
            pb_ratio = current_price / book_value_per_share
            
            # Extract additional data
            shares_outstanding = self._extract_shares_outstanding(response)
            market_cap = self._extract_market_cap(response, current_price, shares_outstanding)
            
            # Calculate data quality score
            quality_score = self._calculate_data_quality(response)
            
            # Validate results
            validation_notes = self._validate_pb_calculation(
                pb_ratio, book_value_per_share, current_price, shares_outstanding
            )
            
            logger.info(
                f"Current P/B calculated: {pb_ratio:.2f} "
                f"(Price: ${current_price:.2f}, BVPS: ${book_value_per_share:.2f})"
            )
            
            return PBCalculationResult(
                success=True,
                pb_ratio=pb_ratio,
                book_value_per_share=book_value_per_share,
                current_price=current_price,
                shares_outstanding=shares_outstanding,
                market_cap=market_cap,
                data_source=response.source_type,
                calculation_date=datetime.now().isoformat(),
                data_quality_score=quality_score,
                validation_notes=validation_notes
            )
            
        except Exception as e:
            logger.error(f"Error calculating current P/B: {e}")
            return PBCalculationResult(
                success=False,
                error_message=f"Calculation error: {str(e)}"
            )
    
    def calculate_historical_pb(self, response: DataSourceResponse, 
                              years: int = 5) -> List[PBDataPoint]:
        """
        Calculate historical P/B ratios from a DataSourceResponse containing historical data.
        
        Args:
            response (DataSourceResponse): Response with historical price and balance sheet data
            years (int): Number of years to process
            
        Returns:
            List[PBDataPoint]: List of historical P/B data points
        """
        try:
            if not response.success or not response.data:
                logger.warning("Invalid response for historical P/B calculation")
                return []
            
            # Extract historical data components
            historical_prices = self._extract_historical_prices(response)
            balance_sheet_data = self._extract_balance_sheet_data(response)
            shares_data = self._extract_shares_history(response)
            
            if not historical_prices:
                logger.warning("No historical price data found")
                return []
            
            if not balance_sheet_data:
                logger.warning("No balance sheet data found")
                return []
            
            # Process data points
            pb_data_points = []
            quality_score = self._calculate_data_quality(response)
            
            # Convert to consistent format for processing
            price_df = self._normalize_price_data(historical_prices, response.source_type)
            balance_df = self._normalize_balance_sheet_data(balance_sheet_data, response.source_type)
            
            # Calculate P/B for each available period
            for date, price_row in price_df.iterrows():
                try:
                    price = price_row.get('Close', price_row.get('close', price_row.get('price')))
                    if price is None or price <= 0:
                        continue
                    
                    # Find closest balance sheet date
                    book_value_per_share = self._find_closest_book_value(
                        date, balance_df, shares_data, response.source_type
                    )
                    
                    if book_value_per_share and book_value_per_share > 0:
                        pb_ratio = price / book_value_per_share
                        
                        pb_data_points.append(PBDataPoint(
                            date=date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                            price=float(price),
                            book_value_per_share=float(book_value_per_share),
                            pb_ratio=float(pb_ratio),
                            source_type=response.source_type,
                            data_quality=quality_score
                        ))
                        
                except Exception as e:
                    logger.debug(f"Error processing data point for {date}: {e}")
                    continue
            
            # Sort by date
            pb_data_points.sort(key=lambda x: x.date)
            
            logger.info(f"Generated {len(pb_data_points)} historical P/B data points")
            return pb_data_points
            
        except Exception as e:
            logger.error(f"Error calculating historical P/B: {e}")
            return []
    
    def reconcile_multi_source_data(self, responses: List[DataSourceResponse]) -> PBCalculationResult:
        """
        Reconcile P/B data from multiple sources for improved accuracy.
        
        Args:
            responses (List[DataSourceResponse]): List of responses from different sources
            
        Returns:
            PBCalculationResult: Reconciled P/B calculation result
        """
        try:
            if not responses:
                return PBCalculationResult(
                    success=False,
                    error_message="No data responses provided"
                )
            
            # Calculate P/B from each source
            individual_results = []
            for response in responses:
                if response.success:
                    result = self.calculate_current_pb(response)
                    if result.success:
                        individual_results.append(result)
            
            if not individual_results:
                return PBCalculationResult(
                    success=False,
                    error_message="No successful calculations from any source"
                )
            
            # Reconcile values using weighted average based on quality scores
            pb_ratios = [(r.pb_ratio, r.data_quality_score or 0.5) for r in individual_results]
            book_values = [(r.book_value_per_share, r.data_quality_score or 0.5) for r in individual_results]
            prices = [(r.current_price, r.data_quality_score or 0.5) for r in individual_results]
            
            reconciled_pb = self._weighted_average(pb_ratios)
            reconciled_bvps = self._weighted_average(book_values)
            reconciled_price = self._weighted_average(prices)
            
            # Use the highest quality source as primary
            best_result = max(individual_results, key=lambda x: x.data_quality_score or 0)
            
            # Create validation notes
            validation_notes = [
                f"Reconciled from {len(individual_results)} sources",
                f"P/B range: {min(r.pb_ratio for r in individual_results):.2f} - {max(r.pb_ratio for r in individual_results):.2f}",
                f"Primary source: {best_result.data_source.value if best_result.data_source else 'Unknown'}"
            ]
            
            logger.info(
                f"Multi-source P/B reconciliation: {reconciled_pb:.2f} "
                f"(from {len(individual_results)} sources)"
            )
            
            return PBCalculationResult(
                success=True,
                pb_ratio=reconciled_pb,
                book_value_per_share=reconciled_bvps,
                current_price=reconciled_price,
                shares_outstanding=best_result.shares_outstanding,
                market_cap=best_result.market_cap,
                data_source=best_result.data_source,
                calculation_date=datetime.now().isoformat(),
                data_quality_score=max(r.data_quality_score or 0 for r in individual_results),
                validation_notes=validation_notes
            )
            
        except Exception as e:
            logger.error(f"Error in multi-source reconciliation: {e}")
            return PBCalculationResult(
                success=False,
                error_message=f"Reconciliation error: {str(e)}"
            )
    
    def _extract_current_price(self, response: DataSourceResponse) -> Optional[float]:
        """Extract current price from DataSourceResponse"""
        try:
            data = response.data
            
            # Try direct price fields first
            price_fields = ['current_price', 'price', 'currentPrice', 'regularMarketPrice']
            for field in price_fields:
                if field in data and data[field] is not None:
                    price = float(data[field])
                    if price > 0:
                        return price
            
            # Try nested structures
            if 'fundamentals' in data:
                for field in price_fields:
                    if field in data['fundamentals']:
                        price = float(data['fundamentals'][field])
                        if price > 0:
                            return price
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting current price: {e}")
            return None
    
    def _extract_book_value_per_share(self, response: DataSourceResponse) -> Optional[float]:
        """Extract book value per share from DataSourceResponse"""
        try:
            # Try direct BVPS field first
            if 'book_value_per_share' in response.data:
                bvps = float(response.data['book_value_per_share'])
                if bvps > 0:
                    return bvps
            
            # Calculate from equity and shares
            equity = self._extract_shareholders_equity(response)
            shares = self._extract_shares_outstanding(response)
            
            if equity and shares and shares > 0:
                return equity / shares
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting book value per share: {e}")
            return None
    
    def _extract_shareholders_equity(self, response: DataSourceResponse) -> Optional[float]:
        """Extract shareholders' equity from DataSourceResponse"""
        try:
            data = response.data
            source_type = response.source_type
            
            # Get field mappings for this source type
            equity_fields = self.equity_field_mappings.get(source_type, [])
            
            # Try direct fields first
            for field in equity_fields:
                if field in data and data[field] is not None:
                    equity = float(data[field])
                    if equity != 0:  # Allow negative equity for some cases
                        return equity
            
            # Try balance sheet data
            if 'balance_sheet' in data:
                balance_sheet = data['balance_sheet']
                
                # Handle list format (like Alpha Vantage)
                if isinstance(balance_sheet, list) and balance_sheet:
                    latest_bs = balance_sheet[0]
                    for field in equity_fields:
                        if field in latest_bs and latest_bs[field] is not None:
                            equity = float(latest_bs[field])
                            if equity != 0:
                                return equity
                
                # Handle dict format
                elif isinstance(balance_sheet, dict):
                    # Try direct access
                    for field in equity_fields:
                        if field in balance_sheet and balance_sheet[field] is not None:
                            equity = float(balance_sheet[field])
                            if equity != 0:
                                return equity
                    
                    # Try nested periods
                    for period_key, period_data in balance_sheet.items():
                        if isinstance(period_data, dict):
                            for field in equity_fields:
                                if field in period_data and period_data[field] is not None:
                                    equity = float(period_data[field])
                                    if equity != 0:
                                        return equity
            
            # Try fundamentals section
            if 'fundamentals' in data:
                fundamentals = data['fundamentals']
                for field in equity_fields:
                    if field in fundamentals and fundamentals[field] is not None:
                        equity = float(fundamentals[field])
                        if equity != 0:
                            return equity
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting shareholders equity: {e}")
            return None
    
    def _extract_shares_outstanding(self, response: DataSourceResponse) -> Optional[float]:
        """Extract shares outstanding from DataSourceResponse"""
        try:
            data = response.data
            source_type = response.source_type
            
            # Get field mappings for this source type
            shares_fields = self.shares_field_mappings.get(source_type, [])
            
            # Try direct fields
            for field in shares_fields:
                if field in data and data[field] is not None:
                    shares = float(data[field])
                    if shares > 0:
                        return shares
            
            # Try fundamentals
            if 'fundamentals' in data:
                for field in shares_fields:
                    if field in data['fundamentals'] and data['fundamentals'][field] is not None:
                        shares = float(data['fundamentals'][field])
                        if shares > 0:
                            return shares
            
            # Try balance sheet (some sources include shares there)
            if 'balance_sheet' in data:
                balance_sheet = data['balance_sheet']
                if isinstance(balance_sheet, list) and balance_sheet:
                    latest_bs = balance_sheet[0]
                    for field in shares_fields:
                        if field in latest_bs and latest_bs[field] is not None:
                            shares = float(latest_bs[field])
                            if shares > 0:
                                return shares
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting shares outstanding: {e}")
            return None
    
    def _extract_market_cap(self, response: DataSourceResponse, 
                          current_price: Optional[float] = None, 
                          shares_outstanding: Optional[float] = None) -> Optional[float]:
        """Extract or calculate market cap from DataSourceResponse"""
        try:
            # Try direct market cap field first
            if 'market_cap' in response.data and response.data['market_cap']:
                return float(response.data['market_cap'])
            
            if 'marketCap' in response.data and response.data['marketCap']:
                return float(response.data['marketCap'])
            
            # Calculate from price and shares
            if current_price and shares_outstanding and both_positive(current_price, shares_outstanding):
                return current_price * shares_outstanding
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting market cap: {e}")
            return None
    
    def _extract_historical_prices(self, response: DataSourceResponse) -> Optional[Dict]:
        """Extract historical price data from DataSourceResponse"""
        try:
            data = response.data
            
            # Look for historical price data
            price_keys = ['historical_prices', 'historicalPrices', 'prices', 'price_history']
            
            for key in price_keys:
                if key in data and data[key]:
                    return data[key]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting historical prices: {e}")
            return None
    
    def _extract_balance_sheet_data(self, response: DataSourceResponse) -> Optional[Dict]:
        """Extract balance sheet data from DataSourceResponse"""
        try:
            data = response.data
            
            # Look for balance sheet data
            bs_keys = ['quarterly_balance_sheet', 'balance_sheet', 'balanceSheet', 'financials']
            
            for key in bs_keys:
                if key in data and data[key]:
                    return data[key]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting balance sheet data: {e}")
            return None
    
    def _extract_shares_history(self, response: DataSourceResponse) -> Optional[Dict]:
        """Extract historical shares outstanding data from DataSourceResponse"""
        try:
            data = response.data
            
            # Look for shares history
            shares_keys = ['shares_history', 'sharesHistory', 'historical_shares']
            
            for key in shares_keys:
                if key in data and data[key]:
                    return data[key]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting shares history: {e}")
            return None
    
    def _normalize_price_data(self, price_data: Dict, source_type: DataSourceType) -> pd.DataFrame:
        """Normalize price data to consistent format"""
        try:
            if isinstance(price_data, pd.DataFrame):
                return price_data
            
            # Convert dict to DataFrame based on source type
            if source_type == DataSourceType.ALPHA_VANTAGE:
                # Alpha Vantage time series format
                df_data = []
                for date_str, price_info in price_data.items():
                    if isinstance(price_info, dict):
                        df_data.append({
                            'Date': pd.to_datetime(date_str),
                            'Close': float(price_info.get('4. close', price_info.get('close', 0)))
                        })
                df = pd.DataFrame(df_data)
                return df.set_index('Date')
            
            elif source_type in [DataSourceType.FINANCIAL_MODELING_PREP, DataSourceType.POLYGON]:
                # List of price records
                if isinstance(price_data, list):
                    df = pd.DataFrame(price_data)
                    if 'date' in df.columns:
                        df['Date'] = pd.to_datetime(df['date'])
                        df = df.set_index('Date')
                    return df
            
            # Default handling
            return pd.DataFrame(price_data)
            
        except Exception as e:
            logger.warning(f"Error normalizing price data: {e}")
            return pd.DataFrame()
    
    def _normalize_balance_sheet_data(self, bs_data: Dict, source_type: DataSourceType) -> pd.DataFrame:
        """Normalize balance sheet data to consistent format"""
        try:
            if isinstance(bs_data, pd.DataFrame):
                return bs_data
            
            # Convert to DataFrame based on source type
            if isinstance(bs_data, list):
                df = pd.DataFrame(bs_data)
                if 'fiscalDateEnding' in df.columns:
                    df['Date'] = pd.to_datetime(df['fiscalDateEnding'])
                elif 'date' in df.columns:
                    df['Date'] = pd.to_datetime(df['date'])
                elif 'calendarYear' in df.columns:
                    df['Date'] = pd.to_datetime(df['calendarYear'], format='%Y')
                
                if 'Date' in df.columns:
                    df = df.set_index('Date')
                
                return df
            
            return pd.DataFrame(bs_data)
            
        except Exception as e:
            logger.warning(f"Error normalizing balance sheet data: {e}")
            return pd.DataFrame()
    
    def _find_closest_book_value(self, date, balance_df: pd.DataFrame, 
                                shares_data: Optional[Dict], source_type: DataSourceType) -> Optional[float]:
        """Find the closest book value per share for a given date"""
        try:
            if balance_df.empty:
                return None
            
            # Find the closest balance sheet date that's before or on the target date
            valid_dates = [bs_date for bs_date in balance_df.index if bs_date <= date]
            
            if not valid_dates:
                return None
            
            closest_date = max(valid_dates)
            bs_row = balance_df.loc[closest_date]
            
            # Extract equity from this balance sheet entry
            equity_fields = self.equity_field_mappings.get(source_type, [])
            equity = None
            
            for field in equity_fields:
                if field in bs_row and pd.notna(bs_row[field]) and bs_row[field] != 0:
                    equity = float(bs_row[field])
                    break
            
            if equity is None:
                return None
            
            # Get shares outstanding for this period
            shares = None
            shares_fields = self.shares_field_mappings.get(source_type, [])
            
            # Try to get shares from balance sheet first
            for field in shares_fields:
                if field in bs_row and pd.notna(bs_row[field]) and bs_row[field] > 0:
                    shares = float(bs_row[field])
                    break
            
            # If not found in balance sheet, use shares history or assume constant
            if shares is None and shares_data:
                # This would need implementation based on shares_data format
                pass
            
            if shares and shares > 0:
                return equity / shares
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding closest book value: {e}")
            return None
    
    def _weighted_average(self, values_weights: List[Tuple[float, float]]) -> float:
        """Calculate weighted average of values"""
        if not values_weights:
            return 0.0
        
        total_weight = sum(weight for _, weight in values_weights)
        if total_weight == 0:
            return sum(value for value, _ in values_weights) / len(values_weights)
        
        weighted_sum = sum(value * weight for value, weight in values_weights)
        return weighted_sum / total_weight
    
    def _calculate_data_quality(self, response: DataSourceResponse) -> float:
        """Calculate data quality score for the response"""
        try:
            if response.quality_metrics:
                return response.quality_metrics.overall_score
            
            # Basic quality assessment based on available data
            data = response.data
            if not data:
                return 0.0
            
            quality_indicators = 0
            total_indicators = 0
            
            # Check for essential P/B calculation fields
            essential_fields = ['current_price', 'balance_sheet', 'fundamentals']
            for field in essential_fields:
                total_indicators += 1
                if field in data and data[field] is not None:
                    quality_indicators += 1
            
            return quality_indicators / total_indicators if total_indicators > 0 else 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating data quality: {e}")
            return 0.5
    
    def _validate_pb_calculation(self, pb_ratio: float, book_value_per_share: float, 
                               current_price: float, shares_outstanding: Optional[float]) -> List[str]:
        """Validate P/B calculation results and return validation notes"""
        notes = []
        
        try:
            # Basic validation
            if pb_ratio <= 0:
                notes.append("Warning: Non-positive P/B ratio")
            elif pb_ratio > 50:
                notes.append("Warning: Extremely high P/B ratio (>50)")
            elif pb_ratio < 0.1:
                notes.append("Warning: Extremely low P/B ratio (<0.1)")
            
            if book_value_per_share <= 0:
                notes.append("Warning: Non-positive book value per share")
            
            if current_price <= 0:
                notes.append("Error: Non-positive current price")
            
            # Reasonableness checks
            if shares_outstanding:
                if shares_outstanding < 1_000_000:  # Less than 1M shares
                    notes.append("Note: Low shares outstanding (<1M)")
                elif shares_outstanding > 50_000_000_000:  # More than 50B shares
                    notes.append("Note: High shares outstanding (>50B)")
            
            # Cross-validation
            if pb_ratio and book_value_per_share and current_price:
                calculated_pb = current_price / book_value_per_share
                if abs(calculated_pb - pb_ratio) > 0.01:
                    notes.append("Warning: P/B calculation inconsistency detected")
            
            if not notes:
                notes.append("All validations passed")
            
        except Exception as e:
            notes.append(f"Validation error: {str(e)}")
        
        return notes


def both_positive(a: Optional[float], b: Optional[float]) -> bool:
    """Helper function to check if both values are positive"""
    return a is not None and b is not None and a > 0 and b > 0