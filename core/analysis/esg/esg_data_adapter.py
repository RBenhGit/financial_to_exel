"""
ESG Data Adapter
================

Adapter for fetching ESG (Environmental, Social, Governance) data from multiple sources.
This adapter integrates with the existing financial data infrastructure to provide
standardized ESG metrics and scores.

Supported ESG Data Sources:
- ESG Enterprise API (primary) - comprehensive ESG ratings and risk data
- Yahoo Finance ESG scores (limited data)
- Financial Modeling Prep ESG scores (backup)
- Alpha Vantage ESG metrics (backup)

Key Features:
- Unified ESG data interface following the BaseApiAdapter pattern
- Intelligent fallback between ESG data sources
- ESG score normalization across different providers
- Integration with VarInputData system
- Comprehensive data quality assessment
"""

import json
import logging
import requests
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from core.data_processing.adapters.base_adapter import (
    BaseApiAdapter, DataSourceType, DataCategory, DataQualityMetrics,
    ExtractionResult, ApiCapabilities
)
from core.analysis.esg.esg_variable_definitions import get_esg_variable_definitions

logger = logging.getLogger(__name__)


from enum import Enum

class ESGDataSourceType(Enum):
    """ESG-specific data source types"""
    ESG_ENTERPRISE = "esg_enterprise"
    SUSTAINALYTICS = "sustainalytics"
    MSCI_ESG = "msci_esg"
    BLOOMBERG_ESG = "bloomberg_esg"
    # Include base types for compatibility
    EXCEL = "excel"
    YFINANCE = "yfinance"
    FMP = "fmp"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"


class ESGDataCategory(Enum):
    """ESG-specific data categories"""
    ENVIRONMENTAL_METRICS = "environmental"
    SOCIAL_METRICS = "social"
    GOVERNANCE_METRICS = "governance"
    ESG_SCORES = "esg_scores"
    ESG_RATINGS = "esg_ratings"
    SUSTAINABILITY_METRICS = "sustainability"


@dataclass
class ESGScoreMapping:
    """Mapping configuration for normalizing ESG scores across providers"""
    provider: str
    score_field: str
    score_range: Tuple[float, float]  # (min, max) values for the provider
    target_range: Tuple[float, float] = (0.0, 100.0)  # Target 0-100 scale
    higher_is_better: bool = True  # True if higher score is better

    def normalize_score(self, raw_score: float) -> float:
        """Normalize provider score to 0-100 scale"""
        if raw_score is None:
            return None

        # Normalize to 0-1 first
        provider_min, provider_max = self.score_range
        normalized = (raw_score - provider_min) / (provider_max - provider_min)

        # Flip if lower is better for this provider
        if not self.higher_is_better:
            normalized = 1.0 - normalized

        # Scale to target range
        target_min, target_max = self.target_range
        final_score = target_min + normalized * (target_max - target_min)

        return max(target_min, min(target_max, final_score))


class ESGDataAdapter(BaseApiAdapter):
    """
    Unified ESG data adapter that fetches ESG metrics from multiple sources
    with intelligent fallback and score normalization.
    """

    def __init__(
        self,
        esg_enterprise_api_key: Optional[str] = None,
        fmp_api_key: Optional[str] = None,
        alpha_vantage_api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize ESG data adapter with multiple API keys.

        Args:
            esg_enterprise_api_key: ESG Enterprise API key (primary source)
            fmp_api_key: Financial Modeling Prep API key (backup)
            alpha_vantage_api_key: Alpha Vantage API key (backup)
            **kwargs: Additional arguments passed to BaseApiAdapter
        """
        super().__init__(**kwargs)

        self.esg_enterprise_key = esg_enterprise_api_key
        self.fmp_api_key = fmp_api_key
        self.alpha_vantage_key = alpha_vantage_api_key

        # ESG score normalization mappings
        self.score_mappings = {
            'esg_enterprise': ESGScoreMapping(
                provider='esg_enterprise',
                score_field='esg_score',
                score_range=(0.0, 100.0),  # Already 0-100
                higher_is_better=True
            ),
            'msci': ESGScoreMapping(
                provider='msci',
                score_field='esg_score',
                score_range=(0.0, 10.0),  # MSCI uses 0-10 scale
                higher_is_better=True
            ),
            'sustainalytics': ESGScoreMapping(
                provider='sustainalytics',
                score_field='esg_risk_score',
                score_range=(0.0, 100.0),  # Sustainalytics risk score (lower is better)
                higher_is_better=False  # Risk score - lower is better
            ),
            'yfinance': ESGScoreMapping(
                provider='yfinance',
                score_field='esgScore',
                score_range=(1.0, 100.0),  # Yahoo Finance ESG score
                higher_is_better=True
            )
        }

        # ESG variable definitions
        self.esg_variables = get_esg_variable_definitions()

        logger.info("ESG Data Adapter initialized with multiple source support")

    def get_capabilities(self) -> ApiCapabilities:
        """Get adapter capabilities"""
        return ApiCapabilities(
            source_type=ESGDataSourceType.ESG_ENTERPRISE,
            supported_categories=[
                ESGDataCategory.ENVIRONMENTAL_METRICS,
                ESGDataCategory.SOCIAL_METRICS,
                ESGDataCategory.GOVERNANCE_METRICS,
                ESGDataCategory.ESG_SCORES,
                ESGDataCategory.ESG_RATINGS
            ],
            rate_limit_per_minute=60,  # Conservative estimate
            rate_limit_per_day=1000,
            max_historical_years=5,
            requires_api_key=True,
            supports_batch_requests=False,
            real_time_data=False,  # ESG data updated quarterly/annually
            cost_per_request=0.01,  # Estimated cost
            reliability_rating=0.85
        )

    def load_symbol_data(
        self,
        symbol: str,
        force_refresh: bool = False,
        categories: Optional[List[ESGDataCategory]] = None
    ) -> ExtractionResult:
        """
        Load ESG data for a given symbol from available sources.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            force_refresh: Whether to bypass cache and fetch fresh data
            categories: Specific ESG categories to fetch (optional)

        Returns:
            ExtractionResult with ESG data extraction results
        """
        start_time = time.time()
        errors = []
        warnings = []

        logger.info(f"Loading ESG data for symbol: {symbol}")

        # Try data sources in order of preference
        data_sources = [
            ('esg_enterprise', self._fetch_esg_enterprise_data),
            ('yfinance', self._fetch_yfinance_esg_data),
            ('fmp', self._fetch_fmp_esg_data),
        ]

        esg_data = {}
        quality_scores = []
        successful_sources = []

        for source_name, fetch_func in data_sources:
            try:
                logger.debug(f"Attempting to fetch ESG data from {source_name}")
                source_data, quality_score = fetch_func(symbol)

                if source_data:
                    esg_data.update(source_data)
                    quality_scores.append(quality_score)
                    successful_sources.append(source_name)
                    logger.info(f"Successfully fetched ESG data from {source_name}")
                else:
                    warnings.append(f"No ESG data available from {source_name}")

            except Exception as e:
                error_msg = f"Failed to fetch ESG data from {source_name}: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

        # Calculate overall quality metrics
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            quality_metrics = DataQualityMetrics(
                completeness_score=avg_quality,
                timeliness_score=0.8,  # ESG data is typically updated quarterly
                consistency_score=0.9,
                reliability_score=avg_quality,
                overall_score=avg_quality,
                issues=[],
                metadata={
                    'sources_used': successful_sources,
                    'score_count': len(quality_scores)
                }
            )
        else:
            quality_metrics = DataQualityMetrics(
                completeness_score=0.0,
                timeliness_score=0.0,
                consistency_score=0.0,
                reliability_score=0.0,
                overall_score=0.0,
                issues=['No ESG data sources available'],
                metadata={}
            )

        # Store data in VarInputData system if successful
        data_points_stored = 0
        variables_extracted = 0

        if esg_data:
            data_points_stored, variables_extracted = self._store_esg_data(symbol, esg_data)

        extraction_time = time.time() - start_time

        return ExtractionResult(
            source=ESGDataSourceType.ESG_ENTERPRISE,  # Primary source
            symbol=symbol,
            success=bool(esg_data),
            variables_extracted=variables_extracted,
            data_points_stored=data_points_stored,
            categories_covered=[ESGDataCategory.ESG_SCORES, ESGDataCategory.ESG_RATINGS],
            periods_covered=['current'],
            quality_metrics=quality_metrics,
            extraction_time=extraction_time,
            errors=errors,
            warnings=warnings,
            metadata={
                'esg_data_points': len(esg_data),
                'sources_attempted': len(data_sources),
                'sources_successful': len(successful_sources),
                'successful_sources': successful_sources
            }
        )

    def _fetch_esg_enterprise_data(self, symbol: str) -> Tuple[Dict[str, Any], float]:
        """
        Fetch ESG data from ESG Enterprise API

        Args:
            symbol: Stock ticker symbol

        Returns:
            Tuple of (esg_data_dict, quality_score)
        """
        if not self.esg_enterprise_key:
            logger.debug("ESG Enterprise API key not available")
            return {}, 0.0

        url = "https://api.esg-enterprise.com/esg-data"
        params = {
            'token': self.esg_enterprise_key,
            'ticker': symbol,
            'format': 'json'
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if not data or 'error' in data:
                logger.warning(f"ESG Enterprise API error for {symbol}: {data.get('error', 'Unknown error')}")
                return {}, 0.0

            # Extract ESG metrics
            esg_data = {}
            quality_score = 0.0
            field_count = 0
            valid_fields = 0

            # Map ESG Enterprise fields to our standard variables
            field_mappings = {
                'esg_score': 'esg_score_total',
                'environmental_score': 'environmental_score',
                'social_score': 'social_score',
                'governance_score': 'governance_score',
                'esg_rating': 'esg_rating_letter',
                'carbon_emissions': 'carbon_emissions_total',
                'employee_count': 'employee_count_total',
                'board_independence': 'board_independence',
                'women_board_pct': 'gender_diversity_board'
            }

            for esg_field, var_name in field_mappings.items():
                if esg_field in data:
                    raw_value = data[esg_field]
                    field_count += 1

                    if raw_value is not None and raw_value != '':
                        # Normalize scores if needed
                        if 'score' in esg_field and esg_field != 'esg_rating':
                            normalized_value = self.score_mappings['esg_enterprise'].normalize_score(raw_value)
                            esg_data[var_name] = normalized_value
                        else:
                            esg_data[var_name] = raw_value

                        valid_fields += 1

            # Calculate quality score based on data completeness
            quality_score = valid_fields / field_count if field_count > 0 else 0.0

            logger.debug(f"Extracted {valid_fields}/{field_count} ESG fields from ESG Enterprise for {symbol}")
            return esg_data, quality_score

        except requests.RequestException as e:
            logger.error(f"ESG Enterprise API request failed for {symbol}: {e}")
            return {}, 0.0
        except Exception as e:
            logger.error(f"Error processing ESG Enterprise data for {symbol}: {e}")
            return {}, 0.0

    def _fetch_yfinance_esg_data(self, symbol: str) -> Tuple[Dict[str, Any], float]:
        """
        Fetch limited ESG data from yfinance

        Args:
            symbol: Stock ticker symbol

        Returns:
            Tuple of (esg_data_dict, quality_score)
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            esg_data = {}
            quality_score = 0.0

            # Extract available ESG-related fields from yfinance
            esg_fields = [
                'esgScores',
                'fullTimeEmployees',
                'governanceEpochDate',
                'compensationRisk',
                'shareHolderRightsRisk',
                'overallRisk',
                'boardRisk',
                'auditRisk'
            ]

            valid_fields = 0
            total_fields = len(esg_fields)

            for field in esg_fields:
                if field in info and info[field] is not None:
                    valid_fields += 1

                    if field == 'esgScores' and isinstance(info[field], dict):
                        # Extract ESG scores if available
                        esg_scores = info[field]

                        # Map yfinance ESG scores to our variables
                        if 'totalEsg' in esg_scores:
                            raw_score = esg_scores['totalEsg']
                            normalized_score = self.score_mappings['yfinance'].normalize_score(raw_score)
                            esg_data['esg_score_total'] = normalized_score

                        if 'environmentScore' in esg_scores:
                            raw_score = esg_scores['environmentScore']
                            normalized_score = self.score_mappings['yfinance'].normalize_score(raw_score)
                            esg_data['environmental_score'] = normalized_score

                        if 'socialScore' in esg_scores:
                            raw_score = esg_scores['socialScore']
                            normalized_score = self.score_mappings['yfinance'].normalize_score(raw_score)
                            esg_data['social_score'] = normalized_score

                        if 'governanceScore' in esg_scores:
                            raw_score = esg_scores['governanceScore']
                            normalized_score = self.score_mappings['yfinance'].normalize_score(raw_score)
                            esg_data['governance_score'] = normalized_score

                    elif field == 'fullTimeEmployees':
                        esg_data['employee_count_total'] = info[field]

                    # Add other risk-related fields as governance metrics
                    elif 'Risk' in field and field != 'overallRisk':
                        # Convert risk scores to governance scores (inverted scale)
                        risk_score = info[field]
                        if isinstance(risk_score, (int, float)) and risk_score > 0:
                            # Convert 1-10 risk scale to 0-100 governance score (inverted)
                            governance_score = 100 - (risk_score - 1) * 10
                            esg_data[f'governance_{field.lower().replace("risk", "score")}'] = governance_score

            quality_score = valid_fields / total_fields if total_fields > 0 else 0.0

            logger.debug(f"Extracted {valid_fields}/{total_fields} ESG fields from yfinance for {symbol}")
            return esg_data, quality_score

        except Exception as e:
            logger.error(f"Error fetching yfinance ESG data for {symbol}: {e}")
            return {}, 0.0

    def _fetch_fmp_esg_data(self, symbol: str) -> Tuple[Dict[str, Any], float]:
        """
        Fetch ESG data from Financial Modeling Prep API

        Args:
            symbol: Stock ticker symbol

        Returns:
            Tuple of (esg_data_dict, quality_score)
        """
        if not self.fmp_api_key:
            logger.debug("FMP API key not available for ESG data")
            return {}, 0.0

        url = f"https://financialmodelingprep.com/api/v4/esg-environmental-social-governance-data"
        params = {
            'symbol': symbol,
            'apikey': self.fmp_api_key
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if not data or isinstance(data, dict) and 'error' in data:
                logger.warning(f"FMP ESG API error for {symbol}: {data.get('error', 'No data')}")
                return {}, 0.0

            # FMP returns a list, take the most recent entry
            if isinstance(data, list) and len(data) > 0:
                esg_entry = data[0]  # Most recent data

                esg_data = {}
                quality_score = 0.0

                # Map FMP fields to our standard variables
                fmp_mappings = {
                    'esgScore': 'esg_score_total',
                    'environmentalScore': 'environmental_score',
                    'socialScore': 'social_score',
                    'governanceScore': 'governance_score'
                }

                valid_fields = 0
                total_fields = len(fmp_mappings)

                for fmp_field, var_name in fmp_mappings.items():
                    if fmp_field in esg_entry and esg_entry[fmp_field] is not None:
                        raw_score = esg_entry[fmp_field]
                        # FMP scores are typically 0-100 scale already
                        esg_data[var_name] = float(raw_score)
                        valid_fields += 1

                quality_score = valid_fields / total_fields if total_fields > 0 else 0.0

                logger.debug(f"Extracted {valid_fields}/{total_fields} ESG fields from FMP for {symbol}")
                return esg_data, quality_score

            return {}, 0.0

        except Exception as e:
            logger.error(f"Error fetching FMP ESG data for {symbol}: {e}")
            return {}, 0.0

    def _store_esg_data(self, symbol: str, esg_data: Dict[str, Any]) -> Tuple[int, int]:
        """
        Store ESG data in the VarInputData system

        Args:
            symbol: Stock ticker symbol
            esg_data: Dictionary of ESG variable data

        Returns:
            Tuple of (data_points_stored, variables_extracted)
        """
        try:
            from core.data_processing.var_input_data import get_var_input_data

            var_data = get_var_input_data()

            data_points_stored = 0
            variables_extracted = len(esg_data)
            current_year = str(datetime.now().year)

            for var_name, value in esg_data.items():
                try:
                    var_data.set_variable(
                        symbol=symbol,
                        variable_name=var_name,
                        value=value,
                        source="esg_api",
                        period=current_year,
                        metadata={
                            'data_type': 'esg',
                            'last_updated': datetime.now().isoformat(),
                            'source_adapter': 'esg_data_adapter'
                        }
                    )
                    data_points_stored += 1

                except Exception as e:
                    logger.warning(f"Failed to store ESG variable {var_name} for {symbol}: {e}")

            logger.info(f"Stored {data_points_stored}/{variables_extracted} ESG variables for {symbol}")
            return data_points_stored, variables_extracted

        except Exception as e:
            logger.error(f"Error storing ESG data for {symbol}: {e}")
            return 0, 0

    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols supported by ESG data sources.

        Note: ESG data is typically available for large-cap stocks in major indices.
        """
        # This would ideally query the ESG data providers for supported symbols
        # For now, return major indices that typically have ESG coverage
        return [
            # S&P 500 major components (sample)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'V',
            'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC', 'ADBE', 'CRM', 'NFLX', 'KO',
            # Add more as needed based on ESG data availability
        ]

    def validate_api_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to all configured ESG data sources

        Returns:
            Dictionary mapping source names to connectivity status
        """
        connectivity = {}

        # Test ESG Enterprise API
        if self.esg_enterprise_key:
            try:
                # Test with a common symbol
                test_data, _ = self._fetch_esg_enterprise_data('AAPL')
                connectivity['esg_enterprise'] = bool(test_data)
            except:
                connectivity['esg_enterprise'] = False
        else:
            connectivity['esg_enterprise'] = False

        # Test yfinance (always available)
        try:
            test_data, _ = self._fetch_yfinance_esg_data('AAPL')
            connectivity['yfinance'] = bool(test_data)
        except:
            connectivity['yfinance'] = False

        # Test FMP API
        if self.fmp_api_key:
            try:
                test_data, _ = self._fetch_fmp_esg_data('AAPL')
                connectivity['fmp'] = bool(test_data)
            except:
                connectivity['fmp'] = False
        else:
            connectivity['fmp'] = False

        logger.info(f"ESG API connectivity test results: {connectivity}")
        return connectivity