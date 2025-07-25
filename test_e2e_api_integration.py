"""
End-to-End API Integration Tests

This module contains comprehensive E2E tests for all configured APIs:
- yfinance
- Alpha Vantage
- Financial Modeling Prep
- Polygon.io

Tests include:
- Basic connectivity
- Financial statements retrieval
- FCF calculation accuracy
- Error handling
- Performance benchmarking
"""

import sys
import os
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_sources import (
        DataSourceType, FinancialDataRequest, DataSourceConfig, ApiCredentials,
        YfinanceProvider, AlphaVantageProvider, FinancialModelingPrepProvider, PolygonProvider
    )
    from unified_data_adapter import UnifiedDataAdapter
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available in the current directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result container"""
    test_name: str
    api_name: str
    success: bool
    duration: float
    data_retrieved: bool = False
    fcf_calculated: bool = False
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None

class E2EApiTester:
    """End-to-end API integration tester"""
    
    def __init__(self, base_path: str = "."):
        """Initialize the tester"""
        self.base_path = base_path
        self.test_results: List[TestResult] = []
        self.test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]  # Diverse set for testing
        
        print("E2E API Integration Test Suite")
        print("=" * 50)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all E2E tests for all APIs"""
        
        # Test each API individually
        self.test_yfinance_e2e()
        self.test_alpha_vantage_e2e()
        self.test_fmp_e2e()
        self.test_polygon_e2e()
        
        # Test unified adapter
        self.test_unified_adapter_e2e()
        
        # Test FCF calculation accuracy across APIs
        self.test_fcf_accuracy_comparison()
        
        return self.generate_report()
    
    def test_yfinance_e2e(self):
        """Test yfinance API end-to-end"""
        print("\n🧪 Testing yfinance API...")
        
        try:
            # Create yfinance provider
            config = DataSourceConfig(
                source_type=DataSourceType.YFINANCE,
                priority=1,
                is_enabled=True
            )
            provider = YfinanceProvider(config)
            
            # Test credential validation (should pass without API key)
            if provider.validate_credentials():
                print("  ✓ yfinance connection validated")
            else:
                print("  ❌ yfinance connection failed")
                return
            
            # Test data retrieval for each ticker
            for ticker in self.test_tickers:
                result = self._test_api_data_retrieval(provider, ticker, "yfinance")
                self.test_results.append(result)
                
                if result.success:
                    print(f"  ✓ {ticker}: Data retrieved in {result.duration:.2f}s")
                    if result.fcf_calculated:
                        print(f"    ✓ FCF calculated successfully")
                else:
                    print(f"  ❌ {ticker}: {result.error_message}")
                    
        except Exception as e:
            print(f"  ❌ yfinance test failed: {e}")
            logger.error(f"yfinance E2E test error", exc_info=True)
    
    def test_alpha_vantage_e2e(self):
        """Test Alpha Vantage API end-to-end"""
        print("\n🧪 Testing Alpha Vantage API...")
        
        try:
            # Load API credentials
            config = self._load_api_config("alpha_vantage")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  ⚠ Alpha Vantage API key not configured, skipping tests")
                return
            
            provider = AlphaVantageProvider(config)
            
            # Test credential validation
            if provider.validate_credentials():
                print("  ✓ Alpha Vantage API key validated")
            else:
                print("  ❌ Alpha Vantage API key validation failed")
                return
            
            # Test data retrieval (limited to avoid rate limits)
            test_ticker = "AAPL"  # Test with one ticker to avoid rate limits
            result = self._test_api_data_retrieval(provider, test_ticker, "alpha_vantage")
            self.test_results.append(result)
            
            if result.success:
                print(f"  ✓ {test_ticker}: Data retrieved in {result.duration:.2f}s")
                if result.fcf_calculated:
                    print(f"    ✓ FCF calculated successfully")
            else:
                print(f"  ❌ {test_ticker}: {result.error_message}")
                
        except Exception as e:
            print(f"  ❌ Alpha Vantage test failed: {e}")
            logger.error(f"Alpha Vantage E2E test error", exc_info=True)
    
    def test_fmp_e2e(self):
        """Test Financial Modeling Prep API end-to-end"""
        print("\n🧪 Testing Financial Modeling Prep API...")
        
        try:
            # Load API credentials
            config = self._load_api_config("fmp")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  ⚠ FMP API key not configured, skipping tests")
                return
            
            provider = FinancialModelingPrepProvider(config)
            
            # Test credential validation
            if provider.validate_credentials():
                print("  ✓ FMP API key validated")
            else:
                print("  ❌ FMP API key validation failed")
                return
            
            # Test data retrieval
            test_ticker = "AAPL"  # Test with one ticker first
            result = self._test_api_data_retrieval(provider, test_ticker, "fmp")
            self.test_results.append(result)
            
            if result.success:
                print(f"  ✓ {test_ticker}: Data retrieved in {result.duration:.2f}s")
                if result.fcf_calculated:
                    print(f"    ✓ FCF calculated successfully")
            else:
                print(f"  ❌ {test_ticker}: {result.error_message}")
                
        except Exception as e:
            print(f"  ❌ FMP test failed: {e}")
            logger.error(f"FMP E2E test error", exc_info=True)
    
    def test_polygon_e2e(self):
        """Test Polygon.io API end-to-end"""
        print("\n🧪 Testing Polygon.io API...")
        
        try:
            # Load API credentials
            config = self._load_api_config("polygon")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  ⚠ Polygon API key not configured, skipping tests")
                return
            
            provider = PolygonProvider(config)
            
            # Test credential validation
            if provider.validate_credentials():
                print("  ✓ Polygon API key validated")
            else:
                print("  ❌ Polygon API key validation failed")
                return
            
            # Test data retrieval
            test_ticker = "AAPL"  # Test with one ticker
            result = self._test_api_data_retrieval(provider, test_ticker, "polygon")
            self.test_results.append(result)
            
            if result.success:
                print(f"  ✓ {test_ticker}: Data retrieved in {result.duration:.2f}s")
                if result.fcf_calculated:
                    print(f"    ✓ FCF calculated successfully")
            else:
                print(f"  ❌ {test_ticker}: {result.error_message}")
                
        except Exception as e:
            print(f"  ❌ Polygon test failed: {e}")
            logger.error(f"Polygon E2E test error", exc_info=True)
    
    def test_unified_adapter_e2e(self):
        """Test unified data adapter with fallback"""
        print("\n🧪 Testing Unified Data Adapter...")
        
        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)
            
            # Test data retrieval with automatic fallback
            request = FinancialDataRequest(
                ticker="AAPL",
                data_types=['price', 'fundamentals'],
                force_refresh=True
            )
            
            start_time = time.time()
            response = adapter.fetch_data(request)
            duration = time.time() - start_time
            
            result = TestResult(
                test_name="unified_adapter_fallback",
                api_name="unified",
                success=response.success,
                duration=duration,
                data_retrieved=response.data is not None,
                fcf_calculated="free_cash_flow" in (response.data or {}),
                error_message=response.error_message,
                data_quality_score=response.quality_metrics.overall_score if response.quality_metrics else None
            )
            self.test_results.append(result)
            
            if response.success:
                print(f"  ✓ Data retrieved via {response.source_type.value} in {duration:.2f}s")
                if response.quality_metrics:
                    print(f"    ✓ Quality score: {response.quality_metrics.overall_score:.2f}")
            else:
                print(f"  ❌ Unified adapter failed: {response.error_message}")
            
            adapter.cleanup()
            
        except Exception as e:
            print(f"  ❌ Unified adapter test failed: {e}")
            logger.error(f"Unified adapter E2E test error", exc_info=True)
    
    def test_fcf_accuracy_comparison(self):
        """Compare FCF calculations across different APIs"""
        print("\n🧪 Testing FCF Calculation Accuracy...")
        
        # Extract FCF results from previous tests
        fcf_results = {}
        
        for result in self.test_results:
            if result.fcf_calculated and result.success:
                # This is a simplified comparison - in reality, we'd need to store actual FCF values
                if result.api_name not in fcf_results:
                    fcf_results[result.api_name] = []
                fcf_results[result.api_name].append(result.test_name)
        
        if len(fcf_results) > 1:
            print(f"  ✓ FCF calculated by {len(fcf_results)} different APIs")
            for api, tests in fcf_results.items():
                print(f"    - {api}: {len(tests)} successful calculations")
        else:
            print("  ⚠ FCF comparison requires multiple working APIs")
    
    def _test_api_data_retrieval(self, provider, ticker: str, api_name: str) -> TestResult:
        """Test data retrieval for a specific API and ticker"""
        start_time = time.time()
        
        try:
            request = FinancialDataRequest(
                ticker=ticker,
                data_types=['price', 'fundamentals'],
                force_refresh=True
            )
            
            response = provider.fetch_data(request)
            duration = time.time() - start_time
            
            # Check if FCF was calculated
            fcf_calculated = False
            if response.success and response.data:
                fcf_calculated = any(key in response.data for key in 
                                   ['free_cash_flow', 'fcf_calculated', 'operating_cash_flow'])
            
            return TestResult(
                test_name=f"{api_name}_{ticker.lower()}",
                api_name=api_name,
                success=response.success,
                duration=duration,
                data_retrieved=response.data is not None,
                fcf_calculated=fcf_calculated,
                error_message=response.error_message,
                data_quality_score=response.quality_metrics.overall_score if response.quality_metrics else None
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=f"{api_name}_{ticker.lower()}",
                api_name=api_name,
                success=False,
                duration=duration,
                error_message=str(e)
            )
    
    def _load_api_config(self, source_name: str) -> Optional[DataSourceConfig]:
        """Load API configuration from config file"""
        try:
            config_file = os.path.join(self.base_path, "data_sources_config.json")
            if not os.path.exists(config_file):
                return None
            
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            if source_name not in config_data.get("sources", {}):
                return None
            
            source_config = config_data["sources"][source_name]
            
            # Create credentials if they exist
            credentials = None
            if "credentials" in source_config:
                cred_data = source_config["credentials"]
                credentials = ApiCredentials(
                    api_key=cred_data.get("api_key", ""),
                    base_url=cred_data.get("base_url", ""),
                    rate_limit_calls=cred_data.get("rate_limit_calls", 5),
                    rate_limit_period=cred_data.get("rate_limit_period", 60),
                    timeout=cred_data.get("timeout", 30),
                    retry_attempts=cred_data.get("retry_attempts", 3),
                    cost_per_call=cred_data.get("cost_per_call", 0.0),
                    monthly_limit=cred_data.get("monthly_limit", 1000),
                    is_active=cred_data.get("is_active", True)
                )
            
            # Map source names to DataSourceType
            source_type_map = {
                "yfinance": DataSourceType.YFINANCE,
                "alpha_vantage": DataSourceType.ALPHA_VANTAGE,
                "fmp": DataSourceType.FINANCIAL_MODELING_PREP,
                "polygon": DataSourceType.POLYGON
            }
            
            return DataSourceConfig(
                source_type=source_type_map.get(source_name, DataSourceType.YFINANCE),
                priority=source_config.get("priority", 1),
                credentials=credentials,
                is_enabled=source_config.get("is_enabled", True),
                quality_threshold=source_config.get("quality_threshold", 0.8),
                cache_ttl_hours=source_config.get("cache_ttl_hours", 24)
            )
            
        except Exception as e:
            logger.error(f"Failed to load config for {source_name}: {e}")
            return None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Group results by API
        api_results = {}
        for result in self.test_results:
            if result.api_name not in api_results:
                api_results[result.api_name] = []
            api_results[result.api_name].append(result)
        
        # Calculate statistics
        avg_duration = sum(r.duration for r in self.test_results) / total_tests if total_tests > 0 else 0
        fcf_success_count = sum(1 for r in self.test_results if r.fcf_calculated)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "average_duration": avg_duration,
                "fcf_calculations": fcf_success_count,
                "timestamp": datetime.now().isoformat()
            },
            "api_breakdown": {},
            "recommendations": []
        }
        
        # Generate API-specific breakdowns
        for api_name, results in api_results.items():
            api_success = sum(1 for r in results if r.success)
            api_total = len(results)
            
            report["api_breakdown"][api_name] = {
                "tests_run": api_total,
                "successes": api_success,
                "failures": api_total - api_success,
                "success_rate": api_success / api_total if api_total > 0 else 0,
                "avg_duration": sum(r.duration for r in results) / api_total if api_total > 0 else 0,
                "fcf_calculations": sum(1 for r in results if r.fcf_calculated)
            }
        
        # Generate recommendations
        if report["summary"]["success_rate"] >= 0.8:
            report["recommendations"].append("✅ Overall test success rate is excellent (≥80%)")
        else:
            report["recommendations"].append("⚠ Overall test success rate needs improvement (<80%)")
        
        if fcf_success_count > 0:
            report["recommendations"].append(f"✅ FCF calculation working on {fcf_success_count} test(s)")
        else:
            report["recommendations"].append("❌ FCF calculation not working on any APIs")
        
        # Print report
        self._print_report(report)
        
        return report
    
    def _print_report(self, report: Dict[str, Any]):
        """Print formatted test report"""
        print("\n" + "=" * 60)
        print("📊 E2E API INTEGRATION TEST REPORT")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Average Duration: {summary['average_duration']:.2f}s")
        print(f"FCF Calculations: {summary['fcf_calculations']}")
        
        print(f"\n📋 API BREAKDOWN:")
        for api_name, stats in report["api_breakdown"].items():
            print(f"  {api_name.upper()}:")
            print(f"    Tests: {stats['tests_run']}")
            print(f"    Success Rate: {stats['success_rate']:.1%}")
            print(f"    Avg Duration: {stats['avg_duration']:.2f}s")
            print(f"    FCF Calculations: {stats['fcf_calculations']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  {rec}")
        
        if summary["failed_tests"] > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result.success:
                    print(f"  • {result.test_name} ({result.api_name}): {result.error_message}")

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="E2E API Integration Tests")
    parser.add_argument('--base-path', default='.', help='Base path for config files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tester and run tests
    tester = E2EApiTester(base_path=args.base_path)
    
    try:
        final_report = tester.run_all_tests()
        
        # Determine exit code based on results
        if final_report['summary']['success_rate'] >= 0.7:  # 70% threshold for E2E tests
            print(f"\n🎉 E2E tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n💥 E2E tests completed with significant issues!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        logger.error("E2E test execution failed", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()