"""
Test Script for Alternative Financial Data Sources

This script comprehensively tests the new alternative data sources functionality
including API connectors, fallback hierarchy, caching, and integration with
the existing system.

Run this script to verify that the implementation works correctly.
"""

import sys
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_data_manager import EnhancedDataManager, create_enhanced_data_manager
    from unified_data_adapter import UnifiedDataAdapter
    from data_sources import DataSourceType, FinancialDataRequest
    from data_source_manager import DataSourceManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available in the current directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlternativeDataSourcesTester:
    """Comprehensive tester for alternative data sources functionality"""

    def __init__(self, base_path: str = "."):
        """Initialize the tester"""
        self.base_path = base_path
        self.test_results = {}
        self.start_time = datetime.now()

        print("Alternative Financial Data Sources - Comprehensive Test Suite")
        print("=" * 70)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        test_suites = [
            ("Basic Import Tests", self.test_imports),
            ("Configuration System", self.test_configuration_system),
            ("Enhanced Data Manager", self.test_enhanced_data_manager),
            ("Unified Data Adapter", self.test_unified_data_adapter),
            ("Fallback Hierarchy", self.test_fallback_hierarchy),
            ("Caching System", self.test_caching_system),
            ("Data Quality Validation", self.test_data_quality),
            ("Usage Tracking", self.test_usage_tracking),
            ("Integration Tests", self.test_integration),
            ("Error Handling", self.test_error_handling),
        ]

        print(f"Running {len(test_suites)} test suites...\n")

        for suite_name, test_function in test_suites:
            print(f"Testing: {suite_name}")
            print("-" * 30)

            try:
                result = test_function()
                self.test_results[suite_name] = result

                if result.get('success', False):
                    print(f"PASS: {suite_name}")
                else:
                    print(f"FAIL: {suite_name} - {result.get('error', 'Unknown error')}")

            except Exception as e:
                error_msg = str(e)
                self.test_results[suite_name] = {'success': False, 'error': error_msg}
                print(f"FAIL: {suite_name} - {error_msg}")
                logger.error(f"Test suite {suite_name} failed", exc_info=True)

            print()  # Empty line between tests

        return self._generate_final_report()

    def test_imports(self) -> Dict[str, Any]:
        """Test that all required modules can be imported"""
        result = {'success': True, 'imports_tested': [], 'failed_imports': []}

        # Test core imports
        imports_to_test = [
            ('enhanced_data_manager', 'EnhancedDataManager'),
            ('unified_data_adapter', 'UnifiedDataAdapter'),
            ('data_sources', 'DataSourceType'),
            ('data_source_manager', 'DataSourceManager'),
        ]

        for module_name, class_name in imports_to_test:
            try:
                module = __import__(module_name)
                cls = getattr(module, class_name)
                result['imports_tested'].append(f"{module_name}.{class_name}")
                print(f"  ✓ {module_name}.{class_name}")
            except Exception as e:
                result['failed_imports'].append(f"{module_name}.{class_name}: {e}")
                result['success'] = False
                print(f"  ✗ {module_name}.{class_name}: {e}")

        # Test optional dependencies
        optional_imports = [
            ('requests', 'HTTP requests library'),
            ('pandas', 'Data processing library'),
            ('numpy', 'Numerical computing library'),
        ]

        for module_name, description in optional_imports:
            try:
                __import__(module_name)
                print(f"  ✓ {module_name} ({description})")
            except ImportError:
                print(f"  ⚠ {module_name} not available ({description})")

        return result

    def test_configuration_system(self) -> Dict[str, Any]:
        """Test the configuration system"""
        result = {'success': True, 'tests': []}

        try:
            # Test UnifiedDataAdapter initialization
            adapter = UnifiedDataAdapter(base_path=self.base_path)
            result['tests'].append("✓ UnifiedDataAdapter initialization")

            # Test configuration loading
            configs = adapter.configurations
            result['tests'].append(f"✓ Loaded {len(configs)} data source configurations")

            # Test default configuration structure
            expected_sources = [
                DataSourceType.EXCEL,
                DataSourceType.YFINANCE,
                DataSourceType.ALPHA_VANTAGE,
                DataSourceType.FINANCIAL_MODELING_PREP,
                DataSourceType.POLYGON,
            ]

            for source_type in expected_sources:
                if source_type in configs:
                    config = configs[source_type]
                    result['tests'].append(f"✓ {source_type.value} configuration loaded")

                    # Check configuration structure
                    if hasattr(config, 'priority') and hasattr(config, 'is_enabled'):
                        result['tests'].append(f"✓ {source_type.value} has valid structure")
                    else:
                        result['success'] = False
                        result['tests'].append(f"✗ {source_type.value} missing required fields")
                else:
                    result['success'] = False
                    result['tests'].append(f"✗ {source_type.value} configuration missing")

            # Test configuration saving/loading cycle
            adapter._save_configuration()
            result['tests'].append("✓ Configuration save test")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Configuration system error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_enhanced_data_manager(self) -> Dict[str, Any]:
        """Test the enhanced data manager"""
        result = {'success': True, 'tests': []}

        try:
            # Test enhanced data manager creation
            manager = create_enhanced_data_manager(base_path=self.base_path)
            result['tests'].append("✓ EnhancedDataManager creation")

            # Test available sources
            sources_info = manager.get_available_data_sources()
            result['tests'].append(f"✓ Found {sources_info['total_sources']} configured sources")
            result['tests'].append(f"✓ {sources_info['active_sources']} sources are active")

            # Test backward compatibility
            if hasattr(manager, 'fetch_market_data'):
                result['tests'].append("✓ Backward compatibility maintained")
            else:
                result['success'] = False
                result['tests'].append("✗ Missing backward compatibility methods")

            # Test enhanced methods
            enhanced_methods = [
                'get_available_data_sources',
                'get_enhanced_usage_report',
                'test_all_sources',
            ]
            for method in enhanced_methods:
                if hasattr(manager, method):
                    result['tests'].append(f"✓ Enhanced method: {method}")
                else:
                    result['success'] = False
                    result['tests'].append(f"✗ Missing enhanced method: {method}")

            manager.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ EnhancedDataManager error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_unified_data_adapter(self) -> Dict[str, Any]:
        """Test the unified data adapter functionality"""
        result = {'success': True, 'tests': []}

        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            # Test request creation
            request = FinancialDataRequest(ticker="AAPL", data_types=['price'], force_refresh=True)
            result['tests'].append("✓ FinancialDataRequest creation")

            # Test provider sorting
            sorted_providers = adapter._get_sorted_providers()
            result['tests'].append(f"✓ Found {len(sorted_providers)} available providers")

            # Test cache key generation
            cache_key = adapter._generate_cache_key(request)
            if cache_key and len(cache_key) == 32:  # MD5 hash length
                result['tests'].append("✓ Cache key generation")
            else:
                result['success'] = False
                result['tests'].append("✗ Invalid cache key generation")

            # Test usage statistics
            usage_report = adapter.get_usage_report()
            if isinstance(usage_report, dict):
                result['tests'].append("✓ Usage report generation")
            else:
                result['success'] = False
                result['tests'].append("✗ Usage report generation failed")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ UnifiedDataAdapter error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_fallback_hierarchy(self) -> Dict[str, Any]:
        """Test the fallback hierarchy system"""
        result = {'success': True, 'tests': []}

        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            # Test provider priority sorting
            sorted_providers = adapter._get_sorted_providers()

            if len(sorted_providers) > 1:
                # Verify that providers are sorted by priority
                priorities = []
                for source_type, provider in sorted_providers:
                    config = adapter.configurations.get(source_type)
                    if config:
                        priorities.append(config.priority.value)

                if priorities == sorted(priorities):
                    result['tests'].append("✓ Providers correctly sorted by priority")
                else:
                    result['success'] = False
                    result['tests'].append("✗ Provider priority sorting failed")
            else:
                result['tests'].append("⚠ Only one provider available, cannot test sorting")

            # Test that Excel provider is available as fallback
            excel_available = any(
                source_type == DataSourceType.EXCEL for source_type, _ in sorted_providers
            )

            if excel_available:
                result['tests'].append("✓ Excel fallback provider available")
            else:
                result['success'] = False
                result['tests'].append("✗ Excel fallback provider not available")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Fallback hierarchy error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_caching_system(self) -> Dict[str, Any]:
        """Test the caching system"""
        result = {'success': True, 'tests': []}

        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            # Test cache key generation
            request = FinancialDataRequest(ticker="TEST", data_types=['price'])
            cache_key = adapter._generate_cache_key(request)

            if cache_key:
                result['tests'].append("✓ Cache key generation works")
            else:
                result['success'] = False
                result['tests'].append("✗ Cache key generation failed")

            # Test different requests generate different keys
            request2 = FinancialDataRequest(ticker="TEST2", data_types=['price'])
            cache_key2 = adapter._generate_cache_key(request2)

            if cache_key != cache_key2:
                result['tests'].append("✓ Different requests generate different cache keys")
            else:
                result['success'] = False
                result['tests'].append("✗ Cache key collision detected")

            # Test cache save/load cycle
            try:
                adapter._save_cache()
                result['tests'].append("✓ Cache save functionality")
            except Exception as e:
                result['tests'].append(f"⚠ Cache save issue: {e}")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Caching system error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_data_quality(self) -> Dict[str, Any]:
        """Test data quality validation"""
        result = {'success': True, 'tests': []}

        try:
            from data_sources import FinancialDataProvider, DataQualityMetrics

            # Test DataQualityMetrics creation
            metrics = DataQualityMetrics()
            metrics.completeness = 0.8
            metrics.accuracy = 0.9
            metrics.timeliness = 0.7
            metrics.consistency = 0.85

            overall_score = metrics.calculate_overall_score()

            if 0 <= overall_score <= 1:
                result['tests'].append(f"✓ Quality metrics calculation: {overall_score:.2f}")
            else:
                result['success'] = False
                result['tests'].append(f"✗ Invalid quality score: {overall_score}")

            # Test quality threshold validation
            if overall_score > 0.5:  # Reasonable threshold
                result['tests'].append("✓ Quality score meets threshold")
            else:
                result['tests'].append("⚠ Quality score below typical threshold")

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Data quality validation error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_usage_tracking(self) -> Dict[str, Any]:
        """Test usage tracking and statistics"""
        result = {'success': True, 'tests': []}

        try:
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            # Test usage report generation
            usage_report = adapter.get_usage_report()

            required_fields = [
                'total_cost',
                'total_calls',
                'monthly_cost',
                'monthly_calls',
                'sources',
            ]
            for field in required_fields:
                if field in usage_report:
                    result['tests'].append(f"✓ Usage report has {field}")
                else:
                    result['success'] = False
                    result['tests'].append(f"✗ Usage report missing {field}")

            # Test statistics persistence
            try:
                adapter._save_usage_stats()
                result['tests'].append("✓ Usage statistics save")
            except Exception as e:
                result['tests'].append(f"⚠ Usage statistics save issue: {e}")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Usage tracking error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_integration(self) -> Dict[str, Any]:
        """Test integration with existing system"""
        result = {'success': True, 'tests': []}

        try:
            # Test enhanced data manager integration
            manager = create_enhanced_data_manager(base_path=self.base_path)

            # Test that it inherits from CentralizedDataManager
            from centralized_data_manager import CentralizedDataManager

            if isinstance(manager, CentralizedDataManager):
                result['tests'].append("✓ EnhancedDataManager inherits from CentralizedDataManager")
            else:
                result['success'] = False
                result['tests'].append("✗ Inheritance chain broken")

            # Test backward compatibility methods
            legacy_methods = ['load_excel_data', 'get_cache_stats']
            for method in legacy_methods:
                if hasattr(manager, method):
                    result['tests'].append(f"✓ Legacy method available: {method}")
                else:
                    result['success'] = False
                    result['tests'].append(f"✗ Legacy method missing: {method}")

            # Test enhanced methods
            enhanced_methods = ['get_available_data_sources', 'configure_enhanced_source']
            for method in enhanced_methods:
                if hasattr(manager, method):
                    result['tests'].append(f"✓ Enhanced method available: {method}")
                else:
                    result['success'] = False
                    result['tests'].append(f"✗ Enhanced method missing: {method}")

            manager.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Integration test error: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and robustness"""
        result = {'success': True, 'tests': []}

        try:
            # Test with invalid ticker
            adapter = UnifiedDataAdapter(base_path=self.base_path)

            request = FinancialDataRequest(
                ticker="INVALID_TICKER_12345", data_types=['price'], force_refresh=True
            )

            response = adapter.fetch_data(request)

            # Should handle gracefully without crashing
            if not response.success:
                result['tests'].append("✓ Invalid ticker handled gracefully")
            else:
                result['tests'].append("⚠ Invalid ticker returned success (might be valid)")

            # Test with empty configuration
            try:
                adapter2 = UnifiedDataAdapter(
                    config_file="nonexistent_config.json", base_path=self.base_path
                )
                result['tests'].append("✓ Missing config file handled gracefully")
                adapter2.cleanup()
            except Exception as e:
                result['tests'].append(f"⚠ Config file error: {e}")

            adapter.cleanup()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['tests'].append(f"✗ Error handling test failed: {e}")

        for test in result['tests']:
            print(f"  {test}")

        return result

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result.get('success', False)
        )
        failed_tests = total_tests - passed_tests

        report = {
            'summary': {
                'total_test_suites': total_tests,
                'passed_test_suites': passed_tests,
                'failed_test_suites': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'duration_seconds': duration,
                'timestamp': end_time.isoformat(),
            },
            'detailed_results': self.test_results,
            'recommendations': [],
        }

        # Generate recommendations based on results
        if failed_tests == 0:
            report['recommendations'].append(
                "✅ All tests passed! The alternative data sources implementation is ready for use."
            )
        else:
            report['recommendations'].append(
                f"⚠ {failed_tests} test suite(s) failed. Review the errors before deployment."
            )

        if report['summary']['success_rate'] >= 0.8:
            report['recommendations'].append("📊 Test success rate is good (≥80%).")
        else:
            report['recommendations'].append(
                "❌ Test success rate is low (<80%). Significant issues need to be addressed."
            )

        # Print final report
        print("📊 FINAL TEST REPORT")
        print("=" * 50)
        print(f"Test Suites Run: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {report['summary']['success_rate']:.1%}")
        print(f"Duration: {duration:.1f} seconds")
        print()

        print("💡 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            print(f"  {recommendation}")

        if failed_tests > 0:
            print("\n❌ FAILED TEST SUITES:")
            for suite_name, result in self.test_results.items():
                if not result.get('success', False):
                    print(f"  • {suite_name}: {result.get('error', 'Unknown error')}")

        return report


def main():
    """Main test execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Alternative Financial Data Sources")
    parser.add_argument('--base-path', default='.', help='Base path for test files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quick', '-q', action='store_true', help='Run quick tests only')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create tester and run tests
    tester = AlternativeDataSourcesTester(base_path=args.base_path)

    try:
        final_report = tester.run_all_tests()

        # Determine exit code based on results
        if final_report['summary']['success_rate'] >= 0.8:
            print(f"\n🎉 Tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n💥 Tests completed with issues!")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n🛑 Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        logger.error("Test execution failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
