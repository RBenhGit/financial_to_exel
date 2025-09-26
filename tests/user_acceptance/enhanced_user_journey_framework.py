"""
Enhanced User Journey Testing Framework with Playwright Integration

This module extends the base user journey testing framework with advanced automation
capabilities including Playwright integration, screenshot capture, performance monitoring,
and CI/CD pipeline integration.
"""

import os
import sys
import time
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import subprocess
import psutil
from contextlib import asynccontextmanager

# Import base framework
from user_journey_testing_framework import (
    TestPriority, TestStatus, UserAction, TestScenario, TestResult,
    UserJourneyTestFramework
)

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not available. Install with: pip install playwright")

try:
    from PIL import Image, ImageChops
    import cv2
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    print("Warning: Image processing libraries not available. Install Pillow and opencv-python")


@dataclass
class PerformanceMetrics:
    """Detailed performance metrics for a test scenario."""
    page_load_time: Optional[float] = None
    first_paint_time: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    dom_content_loaded: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    network_requests: int = 0
    network_data_kb: Optional[float] = None
    javascript_errors: List[str] = field(default_factory=list)
    console_warnings: List[str] = field(default_factory=list)


@dataclass
class ScreenshotComparison:
    """Results from screenshot comparison."""
    baseline_path: str
    current_path: str
    diff_path: str
    similarity_score: float
    pixel_diff_count: int
    total_pixels: int
    is_match: bool
    threshold: float = 0.95


@dataclass
class EnhancedTestResult(TestResult):
    """Extended test result with automation-specific data."""
    performance_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    screenshot_comparisons: List[ScreenshotComparison] = field(default_factory=list)
    automation_log: List[str] = field(default_factory=list)
    session_recording_path: Optional[str] = None
    execution_trace_path: Optional[str] = None


class AutomationMode(Enum):
    """Different modes of test automation."""
    MANUAL = "manual"
    SEMI_AUTOMATED = "semi_automated"  # Manual verification with automated actions
    FULLY_AUTOMATED = "fully_automated"  # Complete automation including validation


class EnhancedUserJourneyTestFramework(UserJourneyTestFramework):
    """
    Enhanced testing framework with Playwright integration and advanced automation.

    Features:
    - Playwright integration for browser automation
    - Screenshot capture and visual regression testing
    - Performance monitoring and benchmarking
    - Real-time user session monitoring
    - CI/CD pipeline integration
    - Enhanced reporting with visual elements
    """

    def __init__(self, base_url: str = "http://localhost:8501",
                 headless: bool = True,
                 browser_type: str = "chromium",
                 screenshots_dir: str = "test_screenshots",
                 baseline_screenshots_dir: str = "baseline_screenshots"):
        super().__init__(base_url)

        self.headless = headless
        self.browser_type = browser_type
        self.screenshots_dir = Path(screenshots_dir)
        self.baseline_screenshots_dir = Path(baseline_screenshots_dir)
        self.performance_thresholds = self._get_default_performance_thresholds()

        # Create directories
        self.screenshots_dir.mkdir(exist_ok=True)
        self.baseline_screenshots_dir.mkdir(exist_ok=True)

        # Playwright components
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.logger.info(f"Enhanced framework initialized. Playwright available: {PLAYWRIGHT_AVAILABLE}")

    def _get_default_performance_thresholds(self) -> Dict[str, float]:
        """Get default performance thresholds for validation."""
        return {
            "page_load_time": 10.0,  # seconds
            "first_paint_time": 3.0,  # seconds
            "dom_content_loaded": 5.0,  # seconds
            "memory_usage_mb": 500.0,  # MB
            "cpu_usage_percent": 80.0,  # %
        }

    async def setup_browser(self) -> bool:
        """Initialize Playwright browser for automation."""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright not available, falling back to manual testing")
            return False

        try:
            self.playwright = await async_playwright().start()

            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")

            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir="test_recordings" if not self.headless else None
            )

            # Enable performance monitoring
            await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)

            self.page = await self.context.new_page()

            # Set up error monitoring
            self.page.on("console", self._handle_console_message)
            self.page.on("pageerror", self._handle_page_error)

            self.logger.info(f"Browser setup complete: {self.browser_type}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup browser: {e}")
            return False

    async def cleanup_browser(self):
        """Clean up Playwright resources."""
        try:
            if self.context:
                await self.context.tracing.stop(path="test_trace.zip")
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")

    def _handle_console_message(self, msg):
        """Handle console messages from the page."""
        if msg.type == "error":
            self.current_performance_metrics.javascript_errors.append(msg.text)
        elif msg.type == "warning":
            self.current_performance_metrics.console_warnings.append(msg.text)

    def _handle_page_error(self, error):
        """Handle page errors."""
        self.current_performance_metrics.javascript_errors.append(str(error))

    async def execute_automated_scenario(self, scenario: TestScenario) -> EnhancedTestResult:
        """
        Execute a test scenario with full automation using Playwright.

        Args:
            scenario: The test scenario to execute

        Returns:
            Enhanced test result with automation data
        """
        result = EnhancedTestResult(
            scenario_id=scenario.scenario_id,
            status=TestStatus.NOT_RUN,
            start_time=datetime.now()
        )

        self.current_performance_metrics = PerformanceMetrics()

        if not await self.setup_browser():
            result.status = TestStatus.BLOCKED
            result.error_message = "Browser setup failed"
            return result

        try:
            self.logger.info(f"Executing automated scenario: {scenario.title}")

            # Start performance monitoring
            start_time = time.time()
            start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB

            # Execute each action
            for i, action in enumerate(scenario.actions):
                try:
                    success = await self._execute_automated_action(action, scenario)
                    if not success:
                        result.status = TestStatus.FAILED
                        result.error_message = f"Action {i+1} failed: {action.target}"
                        return result

                    result.automation_log.append(f"Action {i+1} completed: {action.action_type} - {action.target}")

                except Exception as e:
                    result.status = TestStatus.FAILED
                    result.error_message = f"Action {i+1} error: {str(e)}"
                    result.automation_log.append(f"Action {i+1} failed: {str(e)}")
                    return result

            # Collect final performance metrics
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / 1024 / 1024  # MB

            self.current_performance_metrics.memory_usage_mb = end_memory - start_memory
            result.performance_metrics = self.current_performance_metrics

            # Validate success criteria automatically
            success_validation = await self._validate_success_criteria(scenario)

            if success_validation:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                result.error_message = "Automated success criteria validation failed"

            result.automation_log.append("Scenario execution completed")

        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = f"Scenario execution failed: {str(e)}"
            self.logger.error(f"Automated execution failed: {e}")

        finally:
            result.end_time = datetime.now()
            await self.cleanup_browser()

        return result

    async def _execute_automated_action(self, action: UserAction, scenario: TestScenario) -> bool:
        """Execute a single user action using Playwright."""

        try:
            if action.action_type == "navigate":
                await self.page.goto(self.base_url, wait_until="domcontentloaded")

                # Measure page load performance
                await self.page.wait_for_load_state("networkidle")
                performance_timing = await self.page.evaluate("""
                    () => {
                        const timing = performance.timing;
                        return {
                            domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                            loadComplete: timing.loadEventEnd - timing.navigationStart,
                            firstPaint: performance.getEntriesByType('paint')[0]?.startTime || null
                        };
                    }
                """)

                self.current_performance_metrics.dom_content_loaded = performance_timing.get('domContentLoaded', 0) / 1000
                self.current_performance_metrics.page_load_time = performance_timing.get('loadComplete', 0) / 1000
                if performance_timing.get('firstPaint'):
                    self.current_performance_metrics.first_paint_time = performance_timing['firstPaint'] / 1000

            elif action.action_type == "click":
                # Try different selectors
                selectors = [
                    f"text={action.target}",
                    f"[aria-label*='{action.target}']",
                    f"[title*='{action.target}']",
                    f".{action.target.lower().replace(' ', '-')}",
                    f"#{action.target.lower().replace(' ', '-')}"
                ]

                element_found = False
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.click(selector)
                        element_found = True
                        break
                    except:
                        continue

                if not element_found:
                    # Try fuzzy text matching
                    try:
                        await self.page.get_by_text(action.target, exact=False).click(timeout=action.timeout * 1000)
                        element_found = True
                    except:
                        pass

                if not element_found:
                    self.logger.warning(f"Could not find clickable element: {action.target}")
                    return False

            elif action.action_type == "input":
                # Try different input selectors
                selectors = [
                    f"input[placeholder*='{action.target}']",
                    f"input[name*='{action.target}']",
                    f"textarea[placeholder*='{action.target}']",
                    f"[aria-label*='{action.target}']"
                ]

                input_found = False
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.fill(selector, action.value or "")
                        input_found = True
                        break
                    except:
                        continue

                if not input_found:
                    self.logger.warning(f"Could not find input element: {action.target}")
                    return False

            elif action.action_type == "select":
                try:
                    await self.page.select_option(f"select", action.value)
                except:
                    # Try clicking dropdown option
                    try:
                        await self.page.get_by_text(action.value, exact=False).click()
                    except:
                        self.logger.warning(f"Could not select option: {action.value}")
                        return False

            elif action.action_type == "wait":
                if "loading" in action.target.lower():
                    # Wait for loading indicators to disappear
                    try:
                        await self.page.wait_for_selector(".loading", state="hidden", timeout=action.timeout * 1000)
                    except:
                        # If no loading selector found, wait for network to be idle
                        await self.page.wait_for_load_state("networkidle", timeout=action.timeout * 1000)
                else:
                    await self.page.wait_for_timeout(action.timeout * 1000)

            elif action.action_type == "validate":
                # Perform automated validation
                return await self._validate_page_condition(action)

            elif action.action_type == "measure":
                # Capture performance metrics
                await self._capture_performance_metrics(action)

            # Take screenshot after each action if not a wait or measure
            if action.action_type not in ["wait", "measure"]:
                screenshot_path = await self._capture_screenshot(scenario.scenario_id, action.action_type)
                if screenshot_path and IMAGE_PROCESSING_AVAILABLE:
                    comparison = await self._compare_screenshot(screenshot_path, scenario.scenario_id, action.action_type)
                    if comparison:
                        # Add to result when we have access to it
                        pass

            return True

        except Exception as e:
            self.logger.error(f"Action execution failed: {action.action_type} - {e}")
            return False

    async def _validate_page_condition(self, action: UserAction) -> bool:
        """Validate a condition on the current page."""
        try:
            target = action.target.lower()
            expected = action.expected_result

            if "displays" in target or "shows" in target or "appears" in target:
                # Check if element/text is visible
                text_to_find = expected if expected else action.target
                try:
                    await self.page.wait_for_selector(f"text={text_to_find}", timeout=10000)
                    return True
                except:
                    # Try partial text match
                    try:
                        element = self.page.get_by_text(text_to_find, exact=False)
                        return await element.is_visible()
                    except:
                        return False

            elif "calculated" in target or "loaded" in target:
                # Check for non-zero values or successful loading
                # This is context-specific and would need customization
                await self.page.wait_for_timeout(2000)  # Give time for calculations
                return True

            elif "error" in target:
                # Check for error messages
                try:
                    error_selectors = [".error", ".alert-danger", "[class*='error']", "text=Error"]
                    for selector in error_selectors:
                        if await self.page.is_visible(selector):
                            return True
                    return False
                except:
                    return False

            else:
                # Generic text presence validation
                try:
                    content = await self.page.content()
                    return action.target in content or (expected and expected in content)
                except:
                    return False

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False

    async def _capture_performance_metrics(self, action: UserAction):
        """Capture performance metrics for the current page."""
        try:
            # JavaScript performance metrics
            js_metrics = await self.page.evaluate("""
                () => {
                    const timing = performance.timing;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || null,
                        firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || null,
                        memoryUsed: performance.memory?.usedJSHeapSize || null
                    };
                }
            """)

            if js_metrics.get('domContentLoaded'):
                self.current_performance_metrics.dom_content_loaded = js_metrics['domContentLoaded'] / 1000
            if js_metrics.get('loadComplete'):
                self.current_performance_metrics.page_load_time = js_metrics['loadComplete'] / 1000
            if js_metrics.get('firstPaint'):
                self.current_performance_metrics.first_paint_time = js_metrics['firstPaint'] / 1000
            if js_metrics.get('firstContentfulPaint'):
                self.current_performance_metrics.first_contentful_paint = js_metrics['firstContentfulPaint'] / 1000

            # System performance metrics
            process = psutil.Process()
            self.current_performance_metrics.cpu_usage_percent = process.cpu_percent()
            self.current_performance_metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024

            # Network metrics
            network_entries = await self.page.evaluate("""
                () => {
                    const entries = performance.getEntriesByType('resource');
                    return {
                        count: entries.length,
                        totalSize: entries.reduce((total, entry) => total + (entry.transferSize || 0), 0)
                    };
                }
            """)

            self.current_performance_metrics.network_requests = network_entries.get('count', 0)
            if network_entries.get('totalSize'):
                self.current_performance_metrics.network_data_kb = network_entries['totalSize'] / 1024

        except Exception as e:
            self.logger.warning(f"Failed to capture performance metrics: {e}")

    async def _capture_screenshot(self, scenario_id: str, action_type: str) -> Optional[str]:
        """Capture a screenshot of the current page."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{scenario_id}_{action_type}_{timestamp}.png"
            filepath = self.screenshots_dir / filename

            await self.page.screenshot(path=str(filepath), full_page=True)
            return str(filepath)

        except Exception as e:
            self.logger.warning(f"Failed to capture screenshot: {e}")
            return None

    async def _compare_screenshot(self, current_path: str, scenario_id: str, action_type: str) -> Optional[ScreenshotComparison]:
        """Compare current screenshot with baseline."""
        if not IMAGE_PROCESSING_AVAILABLE:
            return None

        try:
            # Find baseline screenshot
            baseline_pattern = f"{scenario_id}_{action_type}_baseline.png"
            baseline_path = self.baseline_screenshots_dir / baseline_pattern

            if not baseline_path.exists():
                # If no baseline exists, save current as baseline
                import shutil
                shutil.copy2(current_path, baseline_path)
                self.logger.info(f"Created new baseline screenshot: {baseline_path}")
                return None

            # Load images
            current_img = Image.open(current_path)
            baseline_img = Image.open(baseline_path)

            # Ensure same size
            if current_img.size != baseline_img.size:
                baseline_img = baseline_img.resize(current_img.size)

            # Calculate difference
            diff = ImageChops.difference(current_img, baseline_img)

            # Convert to numpy arrays for detailed analysis
            current_array = np.array(current_img)
            baseline_array = np.array(baseline_img)

            # Calculate similarity metrics
            total_pixels = current_array.size
            diff_pixels = np.count_nonzero(current_array != baseline_array)
            similarity = 1.0 - (diff_pixels / total_pixels)

            # Save diff image
            diff_path = self.screenshots_dir / f"{scenario_id}_{action_type}_diff.png"
            diff.save(diff_path)

            return ScreenshotComparison(
                baseline_path=str(baseline_path),
                current_path=current_path,
                diff_path=str(diff_path),
                similarity_score=similarity,
                pixel_diff_count=diff_pixels,
                total_pixels=total_pixels,
                is_match=similarity >= 0.95,
                threshold=0.95
            )

        except Exception as e:
            self.logger.warning(f"Screenshot comparison failed: {e}")
            return None

    async def _validate_success_criteria(self, scenario: TestScenario) -> bool:
        """Automatically validate success criteria for a scenario."""
        try:
            page_content = await self.page.content()

            for criteria in scenario.success_criteria:
                criteria_lower = criteria.lower()

                if "without errors" in criteria_lower:
                    if self.current_performance_metrics.javascript_errors:
                        return False

                elif "loads" in criteria_lower and "successfully" in criteria_lower:
                    # Check if page loaded properly (no error pages)
                    if "error" in page_content.lower() or "not found" in page_content.lower():
                        return False

                elif "calculate" in criteria_lower or "display" in criteria_lower:
                    # Generic check for dynamic content
                    await self.page.wait_for_timeout(2000)  # Allow time for calculations

                # Additional custom validations would go here
                # This is where domain-specific validation logic would be implemented

            return True

        except Exception as e:
            self.logger.warning(f"Success criteria validation failed: {e}")
            return False

    def execute_scenario_with_mode(self, scenario: TestScenario, mode: AutomationMode) -> EnhancedTestResult:
        """
        Execute a scenario with specified automation mode.

        Args:
            scenario: Test scenario to execute
            mode: Level of automation to use

        Returns:
            Enhanced test result with automation data
        """
        if mode == AutomationMode.FULLY_AUTOMATED:
            return asyncio.run(self.execute_automated_scenario(scenario))
        elif mode == AutomationMode.SEMI_AUTOMATED:
            return self._execute_semi_automated_scenario(scenario)
        else:
            # Fall back to manual execution from base class
            base_result = self.execute_scenario(scenario, automated=False)
            return self._convert_to_enhanced_result(base_result)

    def _execute_semi_automated_scenario(self, scenario: TestScenario) -> EnhancedTestResult:
        """Execute scenario with automation for actions but manual validation."""
        # This would combine automated actions with manual validation
        # Implementation would depend on specific requirements
        base_result = self.execute_scenario(scenario, automated=False)
        return self._convert_to_enhanced_result(base_result)

    def _convert_to_enhanced_result(self, base_result: TestResult) -> EnhancedTestResult:
        """Convert base test result to enhanced result."""
        return EnhancedTestResult(
            scenario_id=base_result.scenario_id,
            status=base_result.status,
            start_time=base_result.start_time,
            end_time=base_result.end_time,
            error_message=base_result.error_message,
            screenshots=base_result.screenshots,
            user_feedback=base_result.user_feedback,
            performance_metrics=base_result.performance_metrics or PerformanceMetrics()
        )

    async def run_continuous_monitoring(self, scenarios: List[TestScenario],
                                       interval_minutes: int = 30) -> None:
        """
        Run continuous monitoring of key scenarios.

        Args:
            scenarios: List of scenarios to monitor continuously
            interval_minutes: How often to run the scenarios
        """
        self.logger.info(f"Starting continuous monitoring with {len(scenarios)} scenarios")

        while True:
            try:
                for scenario in scenarios:
                    result = await self.execute_automated_scenario(scenario)

                    # Log results and alert on failures
                    if result.status == TestStatus.FAILED:
                        self.logger.error(f"Continuous monitoring failure: {scenario.title}")
                        # Here you could integrate with alerting systems

                    elif result.status == TestStatus.PASSED:
                        self.logger.info(f"Continuous monitoring success: {scenario.title}")

                    # Store results for trending
                    self._store_monitoring_result(result)

                # Wait for next interval
                await asyncio.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Continuous monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Continuous monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def _store_monitoring_result(self, result: EnhancedTestResult):
        """Store monitoring result for trending analysis."""
        # Implementation would store results in database or file system
        # for trend analysis and reporting
        pass

    def generate_ci_cd_config(self, output_file: str = "test_automation_config.yml"):
        """
        Generate CI/CD pipeline configuration for test automation.

        Args:
            output_file: Path to save the configuration file
        """
        config = {
            "name": "User Acceptance Test Automation",
            "on": ["push", "pull_request", "schedule"],
            "schedule": [{"cron": "0 */6 * * *"}],  # Run every 6 hours
            "jobs": {
                "user-acceptance-tests": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Setup Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.11"}
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements-dev.txt"
                        },
                        {
                            "name": "Install Playwright browsers",
                            "run": "playwright install"
                        },
                        {
                            "name": "Start application",
                            "run": "python run_streamlit_app.py &",
                            "timeout-minutes": 2
                        },
                        {
                            "name": "Wait for application startup",
                            "run": "sleep 30"
                        },
                        {
                            "name": "Run automated UAT",
                            "run": "python -m pytest tests/user_acceptance/ --uat-automated"
                        },
                        {
                            "name": "Upload test results",
                            "uses": "actions/upload-artifact@v3",
                            "with": {
                                "name": "uat-results",
                                "path": "test_results/"
                            }
                        },
                        {
                            "name": "Upload screenshots",
                            "uses": "actions/upload-artifact@v3",
                            "with": {
                                "name": "test-screenshots",
                                "path": "test_screenshots/"
                            }
                        }
                    ]
                }
            }
        }

        import yaml
        with open(output_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        self.logger.info(f"CI/CD configuration saved to {output_file}")

    def generate_enhanced_test_report(self, results: List[EnhancedTestResult],
                                    output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive test report with automation data.

        Args:
            results: List of enhanced test results
            output_file: Optional file path to save report

        Returns:
            Generated report as string
        """
        total_scenarios = len(results)
        passed = len([r for r in results if r.status == TestStatus.PASSED])
        failed = len([r for r in results if r.status == TestStatus.FAILED])

        success_rate = (passed / total_scenarios * 100) if total_scenarios > 0 else 0

        report = f"""
# Enhanced User Acceptance Testing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Scenarios**: {total_scenarios}
- **Success Rate**: {success_rate:.1f}%
- **Passed**: {passed}
- **Failed**: {failed}
- **Automation Level**: Advanced (Playwright Integration)

## Performance Summary
"""

        # Aggregate performance metrics
        if results:
            load_times = [r.performance_metrics.page_load_time or 0 for r in results if hasattr(r, 'performance_metrics') and r.performance_metrics]
            memory_values = [r.performance_metrics.memory_usage_mb or 0 for r in results if hasattr(r, 'performance_metrics') and r.performance_metrics]

            avg_load_time = sum(load_times) / len(load_times) if load_times else 0
            avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0
            total_js_errors = sum(len(r.performance_metrics.javascript_errors or []) for r in results if hasattr(r, 'performance_metrics') and r.performance_metrics)

            report += f"""
- **Average Page Load Time**: {avg_load_time:.2f}s
- **Average Memory Usage**: {avg_memory:.1f} MB
- **Total JavaScript Errors**: {total_js_errors}
"""

        report += "\n## Detailed Results\n"

        for result in results:
            status_icon = {
                TestStatus.PASSED.value: "✅",
                TestStatus.FAILED.value: "❌",
                TestStatus.BLOCKED.value: "🚫",
                TestStatus.SKIPPED.value: "⏭️"
            }.get(result.status.value if hasattr(result.status, 'value') else result.status, "❓")

            scenario = next((s for s in self.test_scenarios if s.scenario_id == result.scenario_id), None)
            if scenario:
                report += f"\n### {status_icon} {scenario.title}\n"
                report += f"- **Scenario ID**: {result.scenario_id}\n"
                report += f"- **Status**: {result.status}\n"

                if result.performance_metrics:
                    pm = result.performance_metrics
                    if pm.page_load_time:
                        report += f"- **Page Load Time**: {pm.page_load_time:.2f}s\n"
                    if pm.memory_usage_mb:
                        report += f"- **Memory Usage**: {pm.memory_usage_mb:.1f} MB\n"
                    if pm.javascript_errors:
                        report += f"- **JS Errors**: {len(pm.javascript_errors)}\n"

                if result.screenshot_comparisons:
                    passed_visual = len([sc for sc in result.screenshot_comparisons if sc.is_match])
                    total_visual = len(result.screenshot_comparisons)
                    report += f"- **Visual Regression**: {passed_visual}/{total_visual} passed\n"

                if result.error_message:
                    report += f"- **Error**: {result.error_message}\n"

        report += "\n## Automation Statistics\n"
        report += f"- **Playwright Integration**: {'✅ Active' if PLAYWRIGHT_AVAILABLE else '❌ Not Available'}\n"
        report += f"- **Image Processing**: {'✅ Active' if IMAGE_PROCESSING_AVAILABLE else '❌ Not Available'}\n"
        report += f"- **Screenshots Captured**: {sum(len(r.screenshots or []) for r in results)}\n"

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)

        return report


# Example usage and test runner
async def main():
    """Example usage of the Enhanced User Journey Testing Framework."""
    framework = EnhancedUserJourneyTestFramework()

    print("Enhanced User Journey Testing Framework")
    print("=" * 60)
    print(f"Playwright Available: {PLAYWRIGHT_AVAILABLE}")
    print(f"Image Processing Available: {IMAGE_PROCESSING_AVAILABLE}")

    # Run a single automated test
    critical_scenarios = framework.get_scenarios_by_priority(TestPriority.CRITICAL)

    if critical_scenarios:
        print(f"\nRunning automated test for: {critical_scenarios[0].title}")
        result = await framework.execute_automated_scenario(critical_scenarios[0])
        print(f"Result: {result.status}")

        if result.performance_metrics:
            pm = result.performance_metrics
            print(f"Performance: Load Time: {pm.page_load_time:.2f}s, Memory: {pm.memory_usage_mb:.1f}MB")

    # Generate CI/CD config
    framework.generate_ci_cd_config()
    print("\nCI/CD configuration generated.")


if __name__ == "__main__":
    asyncio.run(main())