"""
Industry Benchmark Manager
===========================

Provides comprehensive industry benchmark data for ratio analysis,
including sector-specific thresholds and peer comparison data.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
from pathlib import Path
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class IndustryBenchmark:
    """Industry benchmark data for a specific ratio"""
    ratio_name: str
    industry: str
    sector: str
    percentile_25: float
    median: float
    percentile_75: float
    mean: float
    std_deviation: float
    sample_size: int
    data_date: datetime
    source: str = "Industry Analysis"

    @property
    def excellent_threshold(self) -> float:
        """Threshold for excellent performance (75th percentile)"""
        return self.percentile_75

    @property
    def good_threshold(self) -> float:
        """Threshold for good performance (median)"""
        return self.median

    @property
    def poor_threshold(self) -> float:
        """Threshold for poor performance (25th percentile)"""
        return self.percentile_25


@dataclass
class IndustryProfile:
    """Complete industry profile with all ratio benchmarks"""
    industry_name: str
    sector: str
    description: str
    typical_characteristics: List[str]
    benchmarks: Dict[str, IndustryBenchmark] = field(default_factory=dict)
    peer_companies: List[str] = field(default_factory=list)


class IndustryBenchmarkManager:
    """Manages industry benchmark data and provides comparison services"""

    def __init__(self, data_path: Optional[Path] = None):
        """Initialize with optional custom data path"""
        self.data_path = data_path or Path(__file__).parent / "data"
        self.data_path.mkdir(exist_ok=True)

        self._industry_profiles: Dict[str, IndustryProfile] = {}
        self._load_benchmark_data()

    def _load_benchmark_data(self) -> None:
        """Load industry benchmark data from files or create defaults"""
        try:
            benchmark_file = self.data_path / "industry_benchmarks.json"

            if benchmark_file.exists():
                self._load_from_file(benchmark_file)
                logger.info(f"Loaded benchmark data from {benchmark_file}")
            else:
                self._create_default_benchmarks()
                self._save_to_file(benchmark_file)
                logger.info("Created default industry benchmarks")

        except Exception as e:
            logger.error(f"Error loading benchmark data: {e}")
            self._create_default_benchmarks()

    def _load_from_file(self, file_path: Path) -> None:
        """Load benchmark data from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        for industry_name, profile_data in data.items():
            benchmarks = {}

            for ratio_name, benchmark_data in profile_data.get('benchmarks', {}).items():
                benchmarks[ratio_name] = IndustryBenchmark(
                    ratio_name=ratio_name,
                    industry=industry_name,
                    sector=profile_data['sector'],
                    percentile_25=benchmark_data['percentile_25'],
                    median=benchmark_data['median'],
                    percentile_75=benchmark_data['percentile_75'],
                    mean=benchmark_data['mean'],
                    std_deviation=benchmark_data['std_deviation'],
                    sample_size=benchmark_data['sample_size'],
                    data_date=datetime.fromisoformat(benchmark_data['data_date']),
                    source=benchmark_data.get('source', 'Industry Analysis')
                )

            self._industry_profiles[industry_name] = IndustryProfile(
                industry_name=industry_name,
                sector=profile_data['sector'],
                description=profile_data['description'],
                typical_characteristics=profile_data['typical_characteristics'],
                benchmarks=benchmarks,
                peer_companies=profile_data.get('peer_companies', [])
            )

    def _save_to_file(self, file_path: Path) -> None:
        """Save benchmark data to JSON file"""
        data = {}

        for industry_name, profile in self._industry_profiles.items():
            benchmarks = {}

            for ratio_name, benchmark in profile.benchmarks.items():
                benchmarks[ratio_name] = {
                    'percentile_25': benchmark.percentile_25,
                    'median': benchmark.median,
                    'percentile_75': benchmark.percentile_75,
                    'mean': benchmark.mean,
                    'std_deviation': benchmark.std_deviation,
                    'sample_size': benchmark.sample_size,
                    'data_date': benchmark.data_date.isoformat(),
                    'source': benchmark.source
                }

            data[industry_name] = {
                'sector': profile.sector,
                'description': profile.description,
                'typical_characteristics': profile.typical_characteristics,
                'benchmarks': benchmarks,
                'peer_companies': profile.peer_companies
            }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _create_default_benchmarks(self) -> None:
        """Create default industry benchmark data"""

        # Technology Industry
        tech_benchmarks = {
            'roe': IndustryBenchmark(
                'roe', 'Technology', 'Technology', 12.0, 18.0, 28.0, 20.5, 8.2, 150,
                datetime(2024, 1, 1)
            ),
            'roa': IndustryBenchmark(
                'roa', 'Technology', 'Technology', 8.0, 12.0, 18.0, 13.2, 5.1, 150,
                datetime(2024, 1, 1)
            ),
            'current_ratio': IndustryBenchmark(
                'current_ratio', 'Technology', 'Technology', 1.8, 2.5, 3.8, 2.7, 0.9, 150,
                datetime(2024, 1, 1)
            ),
            'debt_to_equity': IndustryBenchmark(
                'debt_to_equity', 'Technology', 'Technology', 0.1, 0.3, 0.8, 0.4, 0.3, 150,
                datetime(2024, 1, 1)
            ),
            'gross_margin': IndustryBenchmark(
                'gross_margin', 'Technology', 'Technology', 60.0, 75.0, 85.0, 73.5, 12.0, 150,
                datetime(2024, 1, 1)
            )
        }

        self._industry_profiles['Technology'] = IndustryProfile(
            industry_name='Technology',
            sector='Technology',
            description='Software, hardware, and technology services companies',
            typical_characteristics=[
                'High gross margins', 'R&D intensive', 'Scalable business models',
                'Strong cash generation', 'Low physical asset requirements'
            ],
            benchmarks=tech_benchmarks,
            peer_companies=['MSFT', 'AAPL', 'GOOGL', 'NVDA', 'META']
        )

        # Financial Services
        financial_benchmarks = {
            'roe': IndustryBenchmark(
                'roe', 'Financial Services', 'Financial', 8.0, 12.0, 16.0, 12.5, 4.2, 120,
                datetime(2024, 1, 1)
            ),
            'roa': IndustryBenchmark(
                'roa', 'Financial Services', 'Financial', 0.8, 1.2, 1.8, 1.3, 0.4, 120,
                datetime(2024, 1, 1)
            ),
            'current_ratio': IndustryBenchmark(
                'current_ratio', 'Financial Services', 'Financial', 1.0, 1.1, 1.3, 1.1, 0.2, 120,
                datetime(2024, 1, 1)
            ),
            'debt_to_equity': IndustryBenchmark(
                'debt_to_equity', 'Financial Services', 'Financial', 3.0, 5.0, 8.0, 5.5, 2.1, 120,
                datetime(2024, 1, 1)
            )
        }

        self._industry_profiles['Financial Services'] = IndustryProfile(
            industry_name='Financial Services',
            sector='Financial',
            description='Banks, insurance companies, and financial service providers',
            typical_characteristics=[
                'High leverage ratios', 'Interest rate sensitive', 'Regulatory compliance',
                'Asset quality focus', 'Credit risk management'
            ],
            benchmarks=financial_benchmarks,
            peer_companies=['JPM', 'BAC', 'WFC', 'C', 'GS']
        )

        # Manufacturing
        manufacturing_benchmarks = {
            'roe': IndustryBenchmark(
                'roe', 'Manufacturing', 'Industrial', 8.0, 14.0, 20.0, 14.8, 6.1, 200,
                datetime(2024, 1, 1)
            ),
            'roa': IndustryBenchmark(
                'roa', 'Manufacturing', 'Industrial', 4.0, 7.0, 12.0, 8.2, 3.8, 200,
                datetime(2024, 1, 1)
            ),
            'current_ratio': IndustryBenchmark(
                'current_ratio', 'Manufacturing', 'Industrial', 1.2, 1.8, 2.8, 2.0, 0.7, 200,
                datetime(2024, 1, 1)
            ),
            'debt_to_equity': IndustryBenchmark(
                'debt_to_equity', 'Manufacturing', 'Industrial', 0.3, 0.6, 1.2, 0.7, 0.4, 200,
                datetime(2024, 1, 1)
            ),
            'asset_turnover': IndustryBenchmark(
                'asset_turnover', 'Manufacturing', 'Industrial', 0.8, 1.2, 1.8, 1.3, 0.4, 200,
                datetime(2024, 1, 1)
            )
        }

        self._industry_profiles['Manufacturing'] = IndustryProfile(
            industry_name='Manufacturing',
            sector='Industrial',
            description='Industrial manufacturing and production companies',
            typical_characteristics=[
                'Asset intensive', 'Cyclical business', 'Inventory management',
                'Supply chain dependent', 'Capital expenditure heavy'
            ],
            benchmarks=manufacturing_benchmarks,
            peer_companies=['GE', 'CAT', 'MMM', 'HON', 'UTX']
        )

        # Retail
        retail_benchmarks = {
            'roe': IndustryBenchmark(
                'roe', 'Retail', 'Consumer Discretionary', 10.0, 15.0, 22.0, 16.2, 5.8, 180,
                datetime(2024, 1, 1)
            ),
            'roa': IndustryBenchmark(
                'roa', 'Retail', 'Consumer Discretionary', 3.0, 6.0, 10.0, 6.5, 3.1, 180,
                datetime(2024, 1, 1)
            ),
            'current_ratio': IndustryBenchmark(
                'current_ratio', 'Retail', 'Consumer Discretionary', 1.0, 1.5, 2.2, 1.6, 0.5, 180,
                datetime(2024, 1, 1)
            ),
            'inventory_turnover': IndustryBenchmark(
                'inventory_turnover', 'Retail', 'Consumer Discretionary', 4.0, 6.0, 9.0, 6.5, 2.2, 180,
                datetime(2024, 1, 1)
            ),
            'gross_margin': IndustryBenchmark(
                'gross_margin', 'Retail', 'Consumer Discretionary', 20.0, 35.0, 50.0, 36.5, 12.8, 180,
                datetime(2024, 1, 1)
            )
        }

        self._industry_profiles['Retail'] = IndustryProfile(
            industry_name='Retail',
            sector='Consumer Discretionary',
            description='Retail and consumer goods companies',
            typical_characteristics=[
                'Inventory management', 'Seasonal variations', 'Consumer sentiment driven',
                'Working capital intensive', 'Competitive pricing pressure'
            ],
            benchmarks=retail_benchmarks,
            peer_companies=['WMT', 'TGT', 'COST', 'HD', 'AMZN']
        )

    def get_industry_benchmark(self, industry: str, ratio_name: str) -> Optional[IndustryBenchmark]:
        """Get benchmark for specific industry and ratio"""
        profile = self._industry_profiles.get(industry)
        if profile:
            return profile.benchmarks.get(ratio_name)
        return None

    def get_industry_profile(self, industry: str) -> Optional[IndustryProfile]:
        """Get complete industry profile"""
        return self._industry_profiles.get(industry)

    def get_available_industries(self) -> List[str]:
        """Get list of available industries"""
        return list(self._industry_profiles.keys())

    def get_ratio_benchmarks(self, ratio_name: str) -> Dict[str, IndustryBenchmark]:
        """Get benchmarks for specific ratio across all industries"""
        benchmarks = {}
        for industry, profile in self._industry_profiles.items():
            if ratio_name in profile.benchmarks:
                benchmarks[industry] = profile.benchmarks[ratio_name]
        return benchmarks

    def classify_performance(self, industry: str, ratio_name: str, value: float) -> Tuple[str, float]:
        """
        Classify performance level and return percentile rank

        Returns:
            Tuple of (performance_level, percentile_rank)
        """
        benchmark = self.get_industry_benchmark(industry, ratio_name)
        if not benchmark:
            return "unknown", 0.0

        # Calculate percentile rank
        if value >= benchmark.percentile_75:
            performance = "excellent"
            # Approximate percentile above 75th
            percentile = min(95.0, 75.0 + (value - benchmark.percentile_75) /
                           (benchmark.percentile_75 - benchmark.median) * 20.0)
        elif value >= benchmark.median:
            performance = "good"
            percentile = 50.0 + (value - benchmark.median) / \
                        (benchmark.percentile_75 - benchmark.median) * 25.0
        elif value >= benchmark.percentile_25:
            performance = "average"
            percentile = 25.0 + (value - benchmark.percentile_25) / \
                        (benchmark.median - benchmark.percentile_25) * 25.0
        else:
            performance = "poor"
            # Approximate percentile below 25th
            percentile = max(5.0, 25.0 - (benchmark.percentile_25 - value) /
                           (benchmark.median - benchmark.percentile_25) * 20.0)

        return performance, percentile

    def get_peer_companies(self, industry: str) -> List[str]:
        """Get peer companies for industry"""
        profile = self._industry_profiles.get(industry)
        return profile.peer_companies if profile else []

    def add_custom_benchmark(self, industry: str, ratio_name: str,
                           benchmark_data: Dict[str, Any]) -> None:
        """Add custom benchmark data"""
        try:
            benchmark = IndustryBenchmark(
                ratio_name=ratio_name,
                industry=industry,
                sector=benchmark_data.get('sector', 'Custom'),
                percentile_25=benchmark_data['percentile_25'],
                median=benchmark_data['median'],
                percentile_75=benchmark_data['percentile_75'],
                mean=benchmark_data['mean'],
                std_deviation=benchmark_data['std_deviation'],
                sample_size=benchmark_data['sample_size'],
                data_date=datetime.now(),
                source=benchmark_data.get('source', 'Custom')
            )

            if industry not in self._industry_profiles:
                self._industry_profiles[industry] = IndustryProfile(
                    industry_name=industry,
                    sector=benchmark_data.get('sector', 'Custom'),
                    description=benchmark_data.get('description', ''),
                    typical_characteristics=[]
                )

            self._industry_profiles[industry].benchmarks[ratio_name] = benchmark
            logger.info(f"Added custom benchmark for {industry}: {ratio_name}")

        except KeyError as e:
            logger.error(f"Missing required benchmark data: {e}")
            raise ValueError(f"Missing required benchmark data: {e}")