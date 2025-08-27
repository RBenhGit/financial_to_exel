"""
FCF Calculation Accuracy Test

This test specifically validates FCF calculation accuracy across all configured APIs.
Uses simple ASCII characters to avoid Windows encoding issues.
"""

import sys
import os
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_sources import (
        DataSourceType,
        FinancialDataRequest,
        DataSourceConfig,
        ApiCredentials,
        YfinanceProvider,
        AlphaVantageProvider,
        FinancialModelingPrepProvider,
        PolygonProvider,
    )
    from unified_data_adapter import UnifiedDataAdapter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available in the current directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FCFAccuracyTester:
    """Test FCF calculation accuracy across APIs"""

    def __init__(self, base_path: str = "."):
        """Initialize the tester"""
        self.base_path = base_path
        self.test_ticker = "AAPL"  # Single ticker for focused testing

        print("FCF Calculation Accuracy Test")
        print("=" * 40)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run FCF accuracy tests for all APIs"""

        results = {}

        # Test each API
        print(f"\nTesting FCF calculation for {self.test_ticker}...")

        results['yfinance'] = self.test_yfinance_fcf()
        results['alpha_vantage'] = self.test_alpha_vantage_fcf()
        results['fmp'] = self.test_fmp_fcf()
        results['polygon'] = self.test_polygon_fcf()

        # Test unified adapter
        results['unified'] = self.test_unified_fcf()

        # Generate comparison report
        return self.generate_comparison_report(results)

    def test_yfinance_fcf(self) -> Dict[str, Any]:
        """Test yfinance FCF calculation"""
        print("\n-- Testing yfinance FCF calculation --")

        try:
            config = DataSourceConfig(
                source_type=DataSourceType.YFINANCE, priority=1, is_enabled=True
            )
            provider = YfinanceProvider(config)

            if not provider.validate_credentials():
                print("  yfinance connection failed")
                return {"success": False, "error": "Connection failed"}

            request = FinancialDataRequest(
                ticker=self.test_ticker, data_types=['fundamentals'], force_refresh=True
            )

            start_time = time.time()
            response = provider.fetch_data(request)
            duration = time.time() - start_time

            if response.success and response.data:
                fcf_data = self.extract_fcf_data(response.data)
                print(f"  SUCCESS: FCF retrieved in {duration:.2f}s")
                if fcf_data['free_cash_flow']:
                    print(f"    Free Cash Flow: ${fcf_data['free_cash_flow']:,.2f}")
                    print(f"    Operating Cash Flow: ${fcf_data['operating_cash_flow']:,.2f}")
                    print(f"    Capital Expenditures: ${fcf_data['capital_expenditures']:,.2f}")
                    print(f"    FCF Year: {fcf_data['fcf_year']}")

                return {
                    "success": True,
                    "duration": duration,
                    "fcf_data": fcf_data,
                    "source": response.data.get('source', 'yfinance'),
                }
            else:
                print(f"  FAILED: {response.error_message}")
                return {"success": False, "error": response.error_message}

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"success": False, "error": str(e)}

    def test_alpha_vantage_fcf(self) -> Dict[str, Any]:
        """Test Alpha Vantage FCF calculation"""
        print("\n-- Testing Alpha Vantage FCF calculation --")

        try:
            config = self._load_api_config("alpha_vantage")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  Alpha Vantage API key not configured")
                return {"success": False, "error": "API key not configured"}

            provider = AlphaVantageProvider(config)

            if not provider.validate_credentials():
                print("  Alpha Vantage API key validation failed")
                return {"success": False, "error": "API key validation failed"}

            request = FinancialDataRequest(
                ticker=self.test_ticker, data_types=['fundamentals'], force_refresh=True
            )

            start_time = time.time()
            response = provider.fetch_data(request)
            duration = time.time() - start_time

            if response.success and response.data:
                fcf_data = self.extract_fcf_data(response.data)
                print(f"  SUCCESS: FCF retrieved in {duration:.2f}s")
                if fcf_data['free_cash_flow']:
                    print(f"    Free Cash Flow: ${fcf_data['free_cash_flow']:,.2f}")
                    print(f"    Operating Cash Flow: ${fcf_data['operating_cash_flow']:,.2f}")
                    print(f"    Capital Expenditures: ${fcf_data['capital_expenditures']:,.2f}")
                    print(f"    FCF Year: {fcf_data['fcf_year']}")

                return {
                    "success": True,
                    "duration": duration,
                    "fcf_data": fcf_data,
                    "source": response.data.get('source', 'alpha_vantage'),
                }
            else:
                print(f"  FAILED: {response.error_message}")
                return {"success": False, "error": response.error_message}

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"success": False, "error": str(e)}

    def test_fmp_fcf(self) -> Dict[str, Any]:
        """Test FMP FCF calculation"""
        print("\n-- Testing Financial Modeling Prep FCF calculation --")

        try:
            config = self._load_api_config("fmp")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  FMP API key not configured")
                return {"success": False, "error": "API key not configured"}

            provider = FinancialModelingPrepProvider(config)

            if not provider.validate_credentials():
                print("  FMP API key validation failed")
                return {"success": False, "error": "API key validation failed"}

            request = FinancialDataRequest(
                ticker=self.test_ticker, data_types=['fundamentals'], force_refresh=True
            )

            start_time = time.time()
            response = provider.fetch_data(request)
            duration = time.time() - start_time

            if response.success and response.data:
                fcf_data = self.extract_fcf_data(response.data)
                print(f"  SUCCESS: FCF retrieved in {duration:.2f}s")
                if fcf_data['free_cash_flow']:
                    print(f"    Free Cash Flow: ${fcf_data['free_cash_flow']:,.2f}")
                    print(f"    Operating Cash Flow: ${fcf_data['operating_cash_flow']:,.2f}")
                    print(f"    Capital Expenditures: ${fcf_data['capital_expenditures']:,.2f}")
                    print(f"    FCF Year: {fcf_data['fcf_year']}")

                return {
                    "success": True,
                    "duration": duration,
                    "fcf_data": fcf_data,
                    "source": response.data.get('source', 'fmp'),
                }
            else:
                print(f"  FAILED: {response.error_message}")
                return {"success": False, "error": response.error_message}

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"success": False, "error": str(e)}

    def test_polygon_fcf(self) -> Dict[str, Any]:
        """Test Polygon FCF calculation"""
        print("\n-- Testing Polygon FCF calculation --")

        try:
            config = self._load_api_config("polygon")
            if not config or not config.credentials or not config.credentials.api_key:
                print("  Polygon API key not configured")
                return {"success": False, "error": "API key not configured"}

            provider = PolygonProvider(config)

            if not provider.validate_credentials():
                print("  Polygon API key validation failed")
                return {"success": False, "error": "API key validation failed"}

            request = FinancialDataRequest(
                ticker=self.test_ticker, data_types=['fundamentals'], force_refresh=True
            )

            start_time = time.time()
            response = provider.fetch_data(request)
            duration = time.time() - start_time

            if response.success and response.data:
                fcf_data = self.extract_fcf_data(response.data)
                print(f"  SUCCESS: FCF retrieved in {duration:.2f}s")
                if fcf_data['free_cash_flow']:
                    print(f"    Free Cash Flow: ${fcf_data['free_cash_flow']:,.2f}")
                    print(f"    Operating Cash Flow: ${fcf_data['operating_cash_flow']:,.2f}")
                    print(f"    Capital Expenditures: ${fcf_data['capital_expenditures']:,.2f}")
                    print(f"    FCF Year: {fcf_data['fcf_year']}")

                return {
                    "success": True,
                    "duration": duration,
                    "fcf_data": fcf_data,
                    "source": response.data.get('source', 'polygon'),
                }
            else:
                print(f"  FAILED: {response.error_message}")
                return {"success": False, "error": response.error_message}

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"success": False, "error": str(e)}

    def test_unified_fcf(self) -> Dict[str, Any]:
        """Test unified adapter FCF calculation"""
        print("\n-- Testing Unified Adapter FCF calculation --")

        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            request = FinancialDataRequest(
                ticker=self.test_ticker, data_types=['fundamentals'], force_refresh=True
            )

            start_time = time.time()
            response = adapter.fetch_data(request)
            duration = time.time() - start_time

            if response.success and response.data:
                fcf_data = self.extract_fcf_data(response.data)
                print(
                    f"  SUCCESS: FCF retrieved via {response.source_type.value} in {duration:.2f}s"
                )
                if fcf_data['free_cash_flow']:
                    print(f"    Free Cash Flow: ${fcf_data['free_cash_flow']:,.2f}")
                    print(f"    Operating Cash Flow: ${fcf_data['operating_cash_flow']:,.2f}")
                    print(f"    Capital Expenditures: ${fcf_data['capital_expenditures']:,.2f}")
                    print(f"    FCF Year: {fcf_data['fcf_year']}")

                adapter.cleanup()
                return {
                    "success": True,
                    "duration": duration,
                    "fcf_data": fcf_data,
                    "source": response.source_type.value,
                    "quality_score": (
                        response.quality_metrics.overall_score if response.quality_metrics else None
                    ),
                }
            else:
                print(f"  FAILED: {response.error_message}")
                adapter.cleanup()
                return {"success": False, "error": response.error_message}

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"success": False, "error": str(e)}

    def extract_fcf_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FCF data from API response"""
        fcf_data = {
            "free_cash_flow": 0.0,
            "operating_cash_flow": 0.0,
            "capital_expenditures": 0.0,
            "fcf_year": None,
            "fcf_source": "not_found",
        }

        # Look for FCF data in various possible locations
        fcf_fields = ['free_cash_flow', 'freeCashFlow', 'fcf']
        ocf_fields = ['operating_cash_flow', 'operatingCashFlow', 'ocf']
        capex_fields = ['capital_expenditures', 'capitalExpenditures', 'capex']

        for field in fcf_fields:
            if field in data and data[field]:
                fcf_data["free_cash_flow"] = float(data[field])
                break

        for field in ocf_fields:
            if field in data and data[field]:
                fcf_data["operating_cash_flow"] = float(data[field])
                break

        for field in capex_fields:
            if field in data and data[field]:
                fcf_data["capital_expenditures"] = float(data[field])
                break

        # Look for year and source information
        if "fcf_year" in data:
            fcf_data["fcf_year"] = data["fcf_year"]
        if "fcf_source" in data:
            fcf_data["fcf_source"] = data["fcf_source"]

        return fcf_data

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
                    is_active=cred_data.get("is_active", True),
                )

            # Map source names to DataSourceType
            source_type_map = {
                "yfinance": DataSourceType.YFINANCE,
                "alpha_vantage": DataSourceType.ALPHA_VANTAGE,
                "fmp": DataSourceType.FINANCIAL_MODELING_PREP,
                "polygon": DataSourceType.POLYGON,
            }

            return DataSourceConfig(
                source_type=source_type_map.get(source_name, DataSourceType.YFINANCE),
                priority=source_config.get("priority", 1),
                credentials=credentials,
                is_enabled=source_config.get("is_enabled", True),
                quality_threshold=source_config.get("quality_threshold", 0.8),
                cache_ttl_hours=source_config.get("cache_ttl_hours", 24),
            )

        except Exception as e:
            logger.error(f"Failed to load config for {source_name}: {e}")
            return None

    def generate_comparison_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FCF comparison report"""
        print("\n" + "=" * 50)
        print("FCF CALCULATION COMPARISON REPORT")
        print("=" * 50)

        successful_apis = []
        fcf_values = {}

        for api_name, result in results.items():
            if result.get("success") and result.get("fcf_data", {}).get("free_cash_flow"):
                successful_apis.append(api_name)
                fcf_values[api_name] = result["fcf_data"]["free_cash_flow"]

        print(f"APIs with successful FCF calculation: {len(successful_apis)}")
        for api in successful_apis:
            print(f"  - {api}: ${fcf_values[api]:,.2f}")

        # Calculate variance if multiple APIs worked
        if len(fcf_values) > 1:
            values = list(fcf_values.values())
            avg_fcf = sum(values) / len(values)
            max_fcf = max(values)
            min_fcf = min(values)
            variance = ((max_fcf - min_fcf) / avg_fcf) * 100 if avg_fcf != 0 else 0

            print(f"\nFCF Variance Analysis:")
            print(f"  Average FCF: ${avg_fcf:,.2f}")
            print(f"  Max FCF: ${max_fcf:,.2f}")
            print(f"  Min FCF: ${min_fcf:,.2f}")
            print(f"  Variance: {variance:.1f}%")

            if variance < 10:
                print("  ASSESSMENT: Low variance - APIs are consistent")
            elif variance < 25:
                print("  ASSESSMENT: Moderate variance - some differences")
            else:
                print("  ASSESSMENT: High variance - significant differences")

        # Failed APIs
        failed_apis = [api for api, result in results.items() if not result.get("success")]
        if failed_apis:
            print(f"\nFailed APIs: {len(failed_apis)}")
            for api in failed_apis:
                print(f"  - {api}: {results[api].get('error', 'Unknown error')}")

        report = {
            "successful_apis": len(successful_apis),
            "failed_apis": len(failed_apis),
            "fcf_values": fcf_values,
            "variance": variance if len(fcf_values) > 1 else 0,
            "detailed_results": results,
        }

        return report


def main():
    """Main test execution function"""
    tester = FCFAccuracyTester()

    try:
        final_report = tester.run_all_tests()

        # Determine exit code based on results
        if final_report['successful_apis'] > 0:
            print(
                f"\nSUCCESS: {final_report['successful_apis']} API(s) successfully calculated FCF"
            )
            sys.exit(0)
        else:
            print(f"\nFAILED: No APIs successfully calculated FCF")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\nTests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        logger.error("FCF test execution failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
