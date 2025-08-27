# Historical P/B Fair Value - Developer Examples

## Overview

This document provides comprehensive developer examples demonstrating how to implement and extend the Historical P/B Fair Value methodology using the generalized data pattern framework. All examples follow established patterns and are designed for easy integration and maintenance.

## 🏗️ **Core Architecture Patterns**

### Generalized Data Request Pattern

The system uses a standardized request-response pattern for all historical P/B operations:

```python
from data_sources import FinancialDataRequest, DataSourceResponse
from unified_data_adapter import UnifiedDataAdapter

# Standard request creation pattern
def create_historical_pb_request(ticker: str, years: int = 5) -> FinancialDataRequest:
    """Create standardized historical P/B analysis request"""
    return FinancialDataRequest(
        ticker=ticker,
        data_types=['historical_prices', 'quarterly_balance_sheet', 'historical_fundamentals'],
        period='quarterly',
        historical_years=years,
        pb_analysis_mode=True,
        limit=years * 4,  # Quarterly periods
        force_refresh=False
    )

# Usage example
request = create_historical_pb_request("AAPL", years=5)
```

### Unified Response Processing Pattern

All data sources return standardized `DataSourceResponse` objects:

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass

def process_pb_data_response(response: DataSourceResponse) -> Dict[str, Any]:
    """Process data source response for P/B analysis"""
    
    if not response.success:
        raise ValueError(f"Data fetch failed: {response.error_message}")
    
    # Extract standardized data components
    historical_data = {
        'prices': response.data.get('historical_prices', {}),
        'balance_sheets': response.data.get('quarterly_balance_sheet', {}),
        'fundamentals': response.data.get('historical_fundamentals', {}),
        'quality_score': response.quality_metrics.overall_score,
        'source_type': response.source_type.value
    }
    
    return historical_data

# Example usage with error handling
try:
    adapter = UnifiedDataAdapter()
    response = adapter.fetch_data(request)
    pb_data = process_pb_data_response(response)
    print(f"Data quality: {pb_data['quality_score']:.2f}")
except ValueError as e:
    print(f"Data processing error: {e}")
```

## 🔄 **Multi-Source Data Collection Examples**

### Advanced Multi-Source Collection with Fallbacks

```python
from typing import List, Dict, Any
from data_sources import DataSourceType, DataSourcePriority
from unified_data_adapter import UnifiedDataAdapter

class HistoricalPBDataCollector:
    """Comprehensive historical P/B data collection with multi-source support"""
    
    def __init__(self, config_file: str = "data_sources_config.json"):
        self.adapter = UnifiedDataAdapter(config_file=config_file)
        self.configure_sources()
    
    def configure_sources(self):
        """Configure data sources in priority order"""
        source_configs = [
            (DataSourceType.ALPHA_VANTAGE, DataSourcePriority.PRIMARY),
            (DataSourceType.FINANCIAL_MODELING_PREP, DataSourcePriority.SECONDARY),
            (DataSourceType.YFINANCE, DataSourcePriority.TERTIARY),
            (DataSourceType.EXCEL, DataSourcePriority.FALLBACK)
        ]
        
        for source_type, priority in source_configs:
            try:
                self.adapter.configure_source(source_type, priority=priority)
            except Exception as e:
                print(f"Warning: Could not configure {source_type.value}: {e}")
    
    def collect_historical_pb_data(self, ticker: str, years: int = 5) -> Dict[str, Any]:
        """Collect comprehensive historical P/B data with automatic fallbacks"""
        
        request = FinancialDataRequest(
            ticker=ticker,
            data_types=['historical_prices', 'quarterly_balance_sheet', 'historical_fundamentals'],
            period='quarterly',
            historical_years=years,
            pb_analysis_mode=True,
            limit=years * 4,
            force_refresh=False
        )
        
        # Attempt data collection with automatic fallbacks
        response = self.adapter.fetch_data(request)
        
        if not response.success:
            raise RuntimeError(f"Failed to collect data for {ticker}: {response.error_message}")
        
        # Process and validate collected data
        collected_data = self._process_collected_data(response, ticker)
        
        # Add collection metadata
        collected_data['collection_metadata'] = {
            'successful_source': response.source_type.value,
            'quality_score': response.quality_metrics.overall_score,
            'api_calls_used': response.api_calls_used,
            'cache_hit': response.from_cache,
            'collection_timestamp': response.timestamp.isoformat(),
            'data_completeness': self._assess_data_completeness(collected_data)
        }
        
        return collected_data
    
    def _process_collected_data(self, response: DataSourceResponse, ticker: str) -> Dict[str, Any]:
        """Process and structure collected historical data"""
        
        raw_data = response.data
        
        processed_data = {
            'ticker': ticker,
            'historical_prices': self._extract_price_data(raw_data.get('historical_prices', {})),
            'balance_sheet_data': self._extract_balance_sheet_data(raw_data.get('quarterly_balance_sheet', {})),
            'fundamental_ratios': self._extract_fundamental_data(raw_data.get('historical_fundamentals', {})),
            'data_quality': {
                'overall_score': response.quality_metrics.overall_score,
                'completeness': response.quality_metrics.completeness,
                'accuracy': response.quality_metrics.accuracy,
                'timeliness': response.quality_metrics.timeliness
            }
        }
        
        return processed_data
    
    def _extract_price_data(self, price_data: Dict) -> List[Dict[str, Any]]:
        """Extract and standardize historical price data"""
        if not price_data:
            return []
        
        standardized_prices = []
        for date, data in price_data.items():
            standardized_prices.append({
                'date': date,
                'close_price': float(data.get('close', 0)),
                'volume': int(data.get('volume', 0)),
                'market_cap': float(data.get('market_cap', 0))
            })
        
        return sorted(standardized_prices, key=lambda x: x['date'])
    
    def _extract_balance_sheet_data(self, balance_data: Dict) -> List[Dict[str, Any]]:
        """Extract and standardize quarterly balance sheet data"""
        if not balance_data:
            return []
        
        standardized_balance = []
        for period, data in balance_data.items():
            standardized_balance.append({
                'period': period,
                'total_equity': float(data.get('total_stockholder_equity', 0)),
                'shares_outstanding': float(data.get('shares_outstanding', 0)),
                'book_value_per_share': float(data.get('book_value_per_share', 0)),
                'tangible_book_value': float(data.get('tangible_book_value', 0))
            })
        
        return sorted(standardized_balance, key=lambda x: x['period'])
    
    def _extract_fundamental_data(self, fundamental_data: Dict) -> List[Dict[str, Any]]:
        """Extract and standardize fundamental ratio data"""
        if not fundamental_data:
            return []
        
        standardized_fundamentals = []
        for period, data in fundamental_data.items():
            standardized_fundamentals.append({
                'period': period,
                'pb_ratio': float(data.get('price_to_book', 0)),
                'roe': float(data.get('return_on_equity', 0)),
                'debt_to_equity': float(data.get('debt_to_equity', 0)),
                'current_ratio': float(data.get('current_ratio', 0))
            })
        
        return sorted(standardized_fundamentals, key=lambda x: x['period'])
    
    def _assess_data_completeness(self, data: Dict[str, Any]) -> float:
        """Assess overall data completeness for P/B analysis"""
        
        required_components = {
            'historical_prices': len(data.get('historical_prices', [])),
            'balance_sheet_data': len(data.get('balance_sheet_data', [])),
            'fundamental_ratios': len(data.get('fundamental_ratios', []))
        }
        
        # Calculate completeness score based on data availability
        expected_quarters = 20  # 5 years of quarterly data
        completeness_scores = []
        
        for component, count in required_components.items():
            score = min(count / expected_quarters, 1.0)
            completeness_scores.append(score)
        
        return sum(completeness_scores) / len(completeness_scores)

# Usage example
collector = HistoricalPBDataCollector()
try:
    pb_data = collector.collect_historical_pb_data("AAPL", years=5)
    metadata = pb_data['collection_metadata']
    
    print(f"Data collected from: {metadata['successful_source']}")
    print(f"Quality score: {metadata['quality_score']:.2f}")
    print(f"Data completeness: {metadata['data_completeness']:.2f}")
    print(f"Historical prices: {len(pb_data['historical_prices'])}")
    print(f"Balance sheet periods: {len(pb_data['balance_sheet_data'])}")
    
except RuntimeError as e:
    print(f"Collection failed: {e}")
```

## 📊 **P/B Calculation Engine Examples**

### Comprehensive P/B Calculation Engine

```python
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PBCalculationResult:
    """Standardized P/B calculation result"""
    pb_ratios: List[float]
    median_pb: float
    mean_pb: float
    pb_range: Tuple[float, float]
    quartiles: Dict[str, float]
    trend_metrics: Dict[str, Any]
    volatility_score: float
    data_quality_score: float

class PBCalculationEngine:
    """Advanced P/B ratio calculation and analysis engine"""
    
    def __init__(self):
        self.minimum_data_points = 8  # Minimum quarters for reliable analysis
    
    def calculate_historical_pb_analysis(self, collected_data: Dict[str, Any]) -> PBCalculationResult:
        """Calculate comprehensive historical P/B analysis"""
        
        # Validate input data
        self._validate_input_data(collected_data)
        
        # Extract and align data
        aligned_data = self._align_price_and_book_data(
            collected_data['historical_prices'],
            collected_data['balance_sheet_data']
        )
        
        # Calculate P/B ratios for each period
        pb_ratios = self._calculate_pb_ratios(aligned_data)
        
        # Perform statistical analysis
        statistical_metrics = self._calculate_statistical_metrics(pb_ratios)
        
        # Analyze trends
        trend_metrics = self._analyze_pb_trends(pb_ratios, aligned_data)
        
        # Calculate volatility
        volatility_score = self._calculate_volatility_score(pb_ratios)
        
        # Assess data quality
        quality_score = self._assess_calculation_quality(aligned_data, pb_ratios)
        
        return PBCalculationResult(
            pb_ratios=pb_ratios,
            median_pb=statistical_metrics['median'],
            mean_pb=statistical_metrics['mean'],
            pb_range=(statistical_metrics['min'], statistical_metrics['max']),
            quartiles=statistical_metrics['quartiles'],
            trend_metrics=trend_metrics,
            volatility_score=volatility_score,
            data_quality_score=quality_score
        )
    
    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """Validate input data for P/B calculations"""
        
        required_fields = ['historical_prices', 'balance_sheet_data']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        if len(data['balance_sheet_data']) < self.minimum_data_points:
            raise ValueError(f"Insufficient data: need at least {self.minimum_data_points} periods")
    
    def _align_price_and_book_data(self, prices: List[Dict], balance_sheets: List[Dict]) -> List[Dict[str, Any]]:
        """Align price and book value data by period"""
        
        # Convert to pandas for easier manipulation
        price_df = pd.DataFrame(prices)
        balance_df = pd.DataFrame(balance_sheets)
        
        if price_df.empty or balance_df.empty:
            raise ValueError("Empty price or balance sheet data")
        
        # Convert dates to datetime for proper alignment
        price_df['date'] = pd.to_datetime(price_df['date'])
        balance_df['period'] = pd.to_datetime(balance_df['period'])
        
        # Align data by quarter
        aligned_data = []
        
        for _, balance_row in balance_df.iterrows():
            period_end = balance_row['period']
            
            # Find closest price data (within 30 days of quarter end)
            price_mask = (price_df['date'] >= period_end - pd.Timedelta(days=30)) & \
                        (price_df['date'] <= period_end + pd.Timedelta(days=30))
            
            matching_prices = price_df[price_mask]
            
            if not matching_prices.empty:
                # Use closest price to period end
                closest_price = matching_prices.loc[
                    (matching_prices['date'] - period_end).abs().idxmin()
                ]
                
                aligned_record = {
                    'period': period_end,
                    'close_price': closest_price['close_price'],
                    'book_value_per_share': balance_row['book_value_per_share'],
                    'shares_outstanding': balance_row['shares_outstanding'],
                    'total_equity': balance_row['total_equity']
                }
                
                # Validate data quality
                if self._is_valid_record(aligned_record):
                    aligned_data.append(aligned_record)
        
        if len(aligned_data) < self.minimum_data_points:
            raise ValueError(f"Insufficient aligned data: {len(aligned_data)} periods")
        
        return sorted(aligned_data, key=lambda x: x['period'])
    
    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """Validate individual aligned record"""
        
        required_values = ['close_price', 'book_value_per_share']
        
        for field in required_values:
            if field not in record or record[field] <= 0:
                return False
        
        return True
    
    def _calculate_pb_ratios(self, aligned_data: List[Dict[str, Any]]) -> List[float]:
        """Calculate P/B ratios for each period"""
        
        pb_ratios = []
        
        for record in aligned_data:
            pb_ratio = record['close_price'] / record['book_value_per_share']
            
            # Sanity check: P/B ratios should be reasonable
            if 0.1 <= pb_ratio <= 50.0:  # Reasonable range filter
                pb_ratios.append(pb_ratio)
        
        return pb_ratios
    
    def _calculate_statistical_metrics(self, pb_ratios: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive statistical metrics"""
        
        if not pb_ratios:
            raise ValueError("No valid P/B ratios calculated")
        
        pb_array = np.array(pb_ratios)
        
        return {
            'count': len(pb_ratios),
            'mean': float(np.mean(pb_array)),
            'median': float(np.median(pb_array)),
            'std': float(np.std(pb_array)),
            'min': float(np.min(pb_array)),
            'max': float(np.max(pb_array)),
            'quartiles': {
                'q25': float(np.percentile(pb_array, 25)),
                'q50': float(np.percentile(pb_array, 50)),
                'q75': float(np.percentile(pb_array, 75))
            },
            'percentiles': {
                'p10': float(np.percentile(pb_array, 10)),
                'p90': float(np.percentile(pb_array, 90))
            }
        }
    
    def _analyze_pb_trends(self, pb_ratios: List[float], aligned_data: List[Dict]) -> Dict[str, Any]:
        """Analyze P/B ratio trends over time"""
        
        if len(pb_ratios) < 4:
            return {'trend_direction': 'insufficient_data', 'trend_strength': 0.0}
        
        # Convert to time series
        dates = [record['period'] for record in aligned_data[-len(pb_ratios):]]
        pb_series = pd.Series(pb_ratios, index=dates)
        
        # Calculate trend using linear regression
        x = np.arange(len(pb_ratios))
        coefficients = np.polyfit(x, pb_ratios, 1)
        slope = coefficients[0]
        
        # Determine trend direction and strength
        trend_strength = abs(slope) / np.mean(pb_ratios)  # Normalized slope
        
        if abs(slope) < 0.01:
            trend_direction = 'stable'
        elif slope > 0:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'
        
        # Calculate trend consistency (R-squared)
        predicted = np.polyval(coefficients, x)
        ss_res = np.sum((pb_ratios - predicted) ** 2)
        ss_tot = np.sum((pb_ratios - np.mean(pb_ratios)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': float(min(trend_strength, 1.0)),
            'trend_consistency': float(max(r_squared, 0.0)),
            'slope': float(slope),
            'recent_trend': self._analyze_recent_trend(pb_ratios[-8:]) if len(pb_ratios) >= 8 else None
        }
    
    def _analyze_recent_trend(self, recent_ratios: List[float]) -> Dict[str, Any]:
        """Analyze recent trend in P/B ratios (last 2 years)"""
        
        if len(recent_ratios) < 4:
            return {'direction': 'insufficient_data', 'strength': 0.0}
        
        x = np.arange(len(recent_ratios))
        coefficients = np.polyfit(x, recent_ratios, 1)
        slope = coefficients[0]
        
        strength = abs(slope) / np.mean(recent_ratios)
        
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        return {
            'direction': direction,
            'strength': float(min(strength, 1.0)),
            'slope': float(slope)
        }
    
    def _calculate_volatility_score(self, pb_ratios: List[float]) -> float:
        """Calculate volatility score for P/B ratios"""
        
        if len(pb_ratios) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_pb = np.mean(pb_ratios)
        std_pb = np.std(pb_ratios)
        
        if mean_pb == 0:
            return 1.0  # Maximum volatility
        
        cv = std_pb / mean_pb
        
        # Normalize to 0-1 scale (CV > 0.5 is considered high volatility)
        volatility_score = min(cv / 0.5, 1.0)
        
        return float(volatility_score)
    
    def _assess_calculation_quality(self, aligned_data: List[Dict], pb_ratios: List[float]) -> float:
        """Assess overall quality of P/B calculations"""
        
        quality_factors = []
        
        # Data completeness factor
        expected_periods = 20  # 5 years quarterly
        completeness = min(len(aligned_data) / expected_periods, 1.0)
        quality_factors.append(completeness)
        
        # Data consistency factor (outlier detection)
        if pb_ratios:
            pb_array = np.array(pb_ratios)
            q25, q75 = np.percentile(pb_array, [25, 75])
            iqr = q75 - q25
            
            # Count outliers (beyond 1.5 * IQR)
            outliers = np.sum((pb_array < q25 - 1.5 * iqr) | (pb_array > q75 + 1.5 * iqr))
            consistency = 1.0 - (outliers / len(pb_ratios))
            quality_factors.append(consistency)
        
        # Data recency factor
        if aligned_data:
            latest_period = aligned_data[-1]['period']
            days_old = (datetime.now() - latest_period.to_pydatetime()).days
            recency = max(0, 1.0 - (days_old / 365))  # Penalty for data older than 1 year
            quality_factors.append(recency)
        
        return float(np.mean(quality_factors))

# Usage example
engine = PBCalculationEngine()

try:
    # Assuming we have collected_data from previous example
    pb_results = engine.calculate_historical_pb_analysis(pb_data)
    
    print(f"Historical P/B Analysis Results:")
    print(f"Median P/B: {pb_results.median_pb:.2f}")
    print(f"P/B Range: {pb_results.pb_range[0]:.2f} - {pb_results.pb_range[1]:.2f}")
    print(f"Trend: {pb_results.trend_metrics['trend_direction']}")
    print(f"Volatility Score: {pb_results.volatility_score:.2f}")
    print(f"Data Quality: {pb_results.data_quality_score:.2f}")
    
except ValueError as e:
    print(f"Calculation error: {e}")
```

## 🎯 **Fair Value Calculator Examples**

### Advanced Fair Value Calculator with Confidence Metrics

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class FairValueEstimate:
    """Comprehensive fair value estimate with confidence metrics"""
    conservative_estimate: float
    fair_value_estimate: float
    optimistic_estimate: float
    current_price: float
    current_vs_fair: float
    confidence_metrics: Dict[str, float]

class PBFairValueCalculator:
    """Advanced fair value calculator using historical P/B patterns"""
    
    def __init__(self):
        self.confidence_weights = {
            'data_quality': 0.35,
            'trend_consistency': 0.25,
            'volatility_factor': 0.20,
            'market_cycle': 0.20
        }
    
    def calculate_fair_value(self, 
                           current_book_value: float,
                           current_price: float,
                           pb_calculation_result: PBCalculationResult,
                           market_context: Optional[Dict[str, Any]] = None) -> FairValueEstimate:
        """Calculate comprehensive fair value estimate"""
        
        # Validate inputs
        self._validate_inputs(current_book_value, current_price, pb_calculation_result)
        
        # Calculate base fair value scenarios
        scenarios = self._calculate_value_scenarios(current_book_value, pb_calculation_result)
        
        # Calculate confidence metrics
        confidence = self._calculate_confidence_metrics(pb_calculation_result, market_context)
        
        # Apply confidence adjustments
        adjusted_scenarios = self._apply_confidence_adjustments(scenarios, confidence)
        
        # Calculate current vs fair value relationship
        current_vs_fair = (current_price - adjusted_scenarios['fair']) / adjusted_scenarios['fair']
        
        return FairValueEstimate(
            conservative_estimate=adjusted_scenarios['conservative'],
            fair_value_estimate=adjusted_scenarios['fair'],
            optimistic_estimate=adjusted_scenarios['optimistic'],
            current_price=current_price,
            current_vs_fair=current_vs_fair,
            confidence_metrics=confidence
        )
    
    def _validate_inputs(self, book_value: float, price: float, pb_result: PBCalculationResult):
        """Validate calculation inputs"""
        
        if book_value <= 0:
            raise ValueError("Book value must be positive")
        
        if price <= 0:
            raise ValueError("Current price must be positive")
        
        if pb_result.data_quality_score < 0.3:
            raise ValueError("Data quality too low for reliable fair value calculation")
    
    def _calculate_value_scenarios(self, book_value: float, pb_result: PBCalculationResult) -> Dict[str, float]:
        """Calculate base fair value scenarios"""
        
        return {
            'conservative': book_value * pb_result.quartiles['q25'],
            'fair': book_value * pb_result.median_pb,
            'optimistic': book_value * pb_result.quartiles['q75']
        }
    
    def _calculate_confidence_metrics(self, 
                                    pb_result: PBCalculationResult,
                                    market_context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive confidence metrics"""
        
        # Data quality component
        data_quality = pb_result.data_quality_score
        
        # Trend consistency component
        trend_consistency = pb_result.trend_metrics.get('trend_consistency', 0.5)
        
        # Volatility factor (inverse relationship - lower volatility = higher confidence)
        volatility_factor = max(0, 1.0 - pb_result.volatility_score)
        
        # Market cycle factor
        market_cycle = self._assess_market_cycle_factor(market_context)
        
        # Calculate overall confidence
        overall_confidence = (
            data_quality * self.confidence_weights['data_quality'] +
            trend_consistency * self.confidence_weights['trend_consistency'] +
            volatility_factor * self.confidence_weights['volatility_factor'] +
            market_cycle * self.confidence_weights['market_cycle']
        )
        
        return {
            'overall_confidence': overall_confidence,
            'data_quality': data_quality,
            'trend_consistency': trend_consistency,
            'volatility_factor': volatility_factor,
            'market_cycle_factor': market_cycle
        }
    
    def _assess_market_cycle_factor(self, market_context: Optional[Dict[str, Any]]) -> float:
        """Assess market cycle impact on confidence"""
        
        if not market_context:
            return 0.75  # Neutral assumption
        
        cycle_position = market_context.get('cycle_position', 'unknown')
        
        cycle_confidence = {
            'early_cycle': 0.85,    # Historical patterns more reliable
            'mid_cycle': 0.90,      # Most stable period
            'late_cycle': 0.70,     # Patterns may be distorted
            'recession': 0.60,      # High uncertainty
            'recovery': 0.75,       # Moderate reliability
            'unknown': 0.70         # Conservative assumption
        }
        
        return cycle_confidence.get(cycle_position, 0.70)
    
    def _apply_confidence_adjustments(self, scenarios: Dict[str, float], confidence: Dict[str, float]) -> Dict[str, float]:
        """Apply confidence-based adjustments to fair value scenarios"""
        
        overall_confidence = confidence['overall_confidence']
        
        # Adjust scenarios based on confidence level
        if overall_confidence >= 0.85:
            # High confidence - minimal adjustment
            adjustment_factor = 1.0
        elif overall_confidence >= 0.70:
            # Moderate confidence - slight widening of ranges
            adjustment_factor = 1.05
        else:
            # Low confidence - significant widening of ranges
            adjustment_factor = 1.15
        
        fair_value = scenarios['fair']
        conservative_range = fair_value - scenarios['conservative']
        optimistic_range = scenarios['optimistic'] - fair_value
        
        return {
            'conservative': fair_value - (conservative_range * adjustment_factor),
            'fair': fair_value,
            'optimistic': fair_value + (optimistic_range * adjustment_factor)
        }

# Usage example with complete workflow
def complete_historical_pb_analysis_example():
    """Complete example of historical P/B fair value analysis"""
    
    ticker = "AAPL"
    
    try:
        # Step 1: Collect historical data
        print("Step 1: Collecting historical data...")
        collector = HistoricalPBDataCollector()
        collected_data = collector.collect_historical_pb_data(ticker, years=5)
        
        print(f"✓ Collected data from: {collected_data['collection_metadata']['successful_source']}")
        print(f"✓ Data quality: {collected_data['collection_metadata']['quality_score']:.2f}")
        
        # Step 2: Calculate P/B analysis
        print("\nStep 2: Calculating P/B analysis...")
        engine = PBCalculationEngine()
        pb_results = engine.calculate_historical_pb_analysis(collected_data)
        
        print(f"✓ Analyzed {len(pb_results.pb_ratios)} periods")
        print(f"✓ Historical median P/B: {pb_results.median_pb:.2f}")
        
        # Step 3: Calculate fair value
        print("\nStep 3: Calculating fair value...")
        calculator = PBFairValueCalculator()
        
        # Get current fundamentals (would come from latest data)
        current_book_value = 4.20  # Example value
        current_price = 150.30     # Example value
        
        market_context = {
            'cycle_position': 'mid_cycle',
            'market_volatility': 0.25
        }
        
        fair_value = calculator.calculate_fair_value(
            current_book_value=current_book_value,
            current_price=current_price,
            pb_calculation_result=pb_results,
            market_context=market_context
        )
        
        # Step 4: Display comprehensive results
        print("\n" + "="*50)
        print(f"HISTORICAL P/B FAIR VALUE ANALYSIS - {ticker}")
        print("="*50)
        
        print(f"\nCURRENT VALUATION:")
        print(f"Current Price:           ${fair_value.current_price:.2f}")
        print(f"Book Value per Share:    ${current_book_value:.2f}")
        print(f"Current P/B Ratio:       {current_price/current_book_value:.2f}")
        
        print(f"\nHISTORICAL ANALYSIS:")
        print(f"Periods Analyzed:        {len(pb_results.pb_ratios)}")
        print(f"Historical Median P/B:   {pb_results.median_pb:.2f}")
        print(f"Historical Range:        {pb_results.pb_range[0]:.2f} - {pb_results.pb_range[1]:.2f}")
        print(f"Trend Direction:         {pb_results.trend_metrics['trend_direction']}")
        print(f"Volatility Score:        {pb_results.volatility_score:.2f}")
        
        print(f"\nFAIR VALUE ESTIMATES:")
        print(f"Conservative:            ${fair_value.conservative_estimate:.2f}")
        print(f"Fair Value:              ${fair_value.fair_value_estimate:.2f}")
        print(f"Optimistic:              ${fair_value.optimistic_estimate:.2f}")
        
        print(f"\nVALUATION ASSESSMENT:")
        premium_discount = fair_value.current_vs_fair * 100
        if premium_discount > 10:
            assessment = "Significantly Overvalued"
        elif premium_discount > 5:
            assessment = "Moderately Overvalued"
        elif premium_discount > -5:
            assessment = "Fairly Valued"
        elif premium_discount > -10:
            assessment = "Moderately Undervalued"
        else:
            assessment = "Significantly Undervalued"
        
        print(f"Current vs Fair Value:   {premium_discount:+.1f}%")
        print(f"Assessment:              {assessment}")
        
        print(f"\nCONFIDENCE METRICS:")
        conf = fair_value.confidence_metrics
        print(f"Overall Confidence:      {conf['overall_confidence']:.1%}")
        print(f"Data Quality:            {conf['data_quality']:.1%}")
        print(f"Trend Consistency:       {conf['trend_consistency']:.1%}")
        print(f"Market Cycle Factor:     {conf['market_cycle_factor']:.1%}")
        
        confidence_level = "High" if conf['overall_confidence'] > 0.8 else \
                          "Moderate" if conf['overall_confidence'] > 0.6 else "Low"
        print(f"Confidence Level:        {confidence_level}")
        
        return {
            'ticker': ticker,
            'analysis_results': pb_results,
            'fair_value': fair_value,
            'collected_data': collected_data
        }
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return None

# Run the complete example
if __name__ == "__main__":
    results = complete_historical_pb_analysis_example()
```

This comprehensive set of developer examples demonstrates how to implement and extend the Historical P/B Fair Value methodology using the established generalized data patterns. The examples show proper error handling, data validation, statistical analysis, and confidence assessment following the system's architectural principles.