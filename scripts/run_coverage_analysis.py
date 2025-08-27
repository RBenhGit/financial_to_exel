#!/usr/bin/env python3
"""
Cross-platform Coverage Analysis Script

This script provides automated coverage analysis workflow
that works on both Windows and Unix-like systems.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd: str, timeout: int = None, capture_output: bool = False) -> tuple:
    """Run a shell command with optional timeout."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                shell=True, 
                timeout=timeout, 
                capture_output=True, 
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {cmd}")
        return 1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1, "", str(e)


def check_virtual_environment() -> bool:
    """Check if we're running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )


def setup_environment() -> bool:
    """Set up the testing environment."""
    logger.info("Setting up testing environment...")
    
    # Check virtual environment
    if not check_virtual_environment():
        logger.warning("Not running in a virtual environment. Consider activating venv.")
    
    # Ensure required packages are installed
    logger.info("Checking for required packages...")
    required_packages = ['pytest', 'pytest-cov']
    
    for package in required_packages:
        returncode, _, _ = run_command(f"pip show {package}", capture_output=True)
        if returncode != 0:
            logger.info(f"Installing missing package: {package}")
            returncode, _, _ = run_command(f"pip install {package}")
            if returncode != 0:
                logger.error(f"Failed to install {package}")
                return False
    
    return True


def clean_previous_coverage() -> None:
    """Clean up previous coverage data."""
    logger.info("Cleaning previous coverage data...")
    
    # Remove coverage files
    for file in ['coverage.json', '.coverage']:
        if Path(file).exists():
            Path(file).unlink()
            logger.info(f"Removed {file}")
    
    # Remove HTML coverage directory
    htmlcov_dir = Path('htmlcov')
    if htmlcov_dir.exists():
        import shutil
        shutil.rmtree(htmlcov_dir)
        logger.info("Removed htmlcov directory")


def run_basic_coverage() -> bool:
    """Run basic tests for coverage baseline."""
    logger.info("Running basic tests for coverage baseline...")
    
    cmd = (
        "pytest tests/test_basic.py "
        "--cov=core --cov=config --cov=utils "
        "--cov-report=html --cov-report=term-missing --cov-report=json"
    )
    
    returncode, _, _ = run_command(cmd, timeout=120)
    return returncode == 0


def run_unit_coverage() -> bool:
    """Run unit tests with coverage (best effort)."""
    logger.info("Running unit tests with coverage (this may take several minutes)...")
    logger.info("Note: Some tests may fail - this is expected for baseline analysis")
    
    cmd = (
        "pytest tests/unit/ "
        "--cov=core --cov=config --cov=utils "
        "--cov-report=html --cov-report=term-missing --cov-report=json --cov-append "
        "--timeout=60 -x --tb=no -q"
    )
    
    # Run with best effort - don't fail if some tests fail
    returncode, _, _ = run_command(cmd, timeout=600)
    
    # Check if coverage data was generated
    coverage_file = Path('coverage.json')
    if coverage_file.exists():
        logger.info("Unit test coverage data collected (some tests may have failed)")
        return True
    else:
        logger.warning("No coverage data generated from unit tests")
        return False


def generate_coverage_analysis() -> bool:
    """Generate coverage analysis report."""
    logger.info("Generating coverage analysis report...")
    
    # Ensure tools directory exists
    tools_dir = Path('tools')
    if not tools_dir.exists():
        logger.error("Tools directory not found")
        return False
    
    # Check if coverage analysis script exists
    analysis_script = tools_dir / 'coverage_analysis.py'
    if not analysis_script.exists():
        logger.error("Coverage analysis script not found")
        return False
    
    # Run coverage analysis
    cmd = "python tools/coverage_analysis.py"
    returncode, _, _ = run_command(cmd)
    
    if returncode == 0:
        logger.info("Coverage analysis report generated successfully")
        return True
    else:
        logger.error("Failed to generate coverage analysis report")
        return False


def open_reports(interactive: bool = True) -> None:
    """Open generated reports."""
    html_report = Path('htmlcov/index.html')
    analysis_report = Path('reports/coverage_analysis_report.md')
    
    reports_opened = []
    
    # Open HTML report
    if html_report.exists():
        if not interactive or input("Open HTML coverage report in browser? (y/n): ").lower().startswith('y'):
            try:
                webbrowser.open(html_report.resolve().as_uri())
                reports_opened.append("HTML coverage report")
            except Exception as e:
                logger.warning(f"Could not open HTML report: {e}")
    
    # Show analysis report location
    if analysis_report.exists():
        print(f"\nCoverage analysis report available at: {analysis_report}")
        reports_opened.append("Analysis report")
    
    if reports_opened:
        logger.info(f"Opened: {', '.join(reports_opened)}")


def print_summary() -> None:
    """Print summary of generated reports."""
    print("\n" + "="*60)
    print("COVERAGE ANALYSIS COMPLETE")
    print("="*60)
    
    # Check what reports were generated
    reports = []
    
    if Path('htmlcov/index.html').exists():
        reports.append("📊 HTML Report: htmlcov/index.html")
    
    if Path('reports/coverage_analysis_report.md').exists():
        reports.append("📋 Analysis Report: reports/coverage_analysis_report.md")
    
    if Path('coverage.json').exists():
        reports.append("🔢 JSON Data: coverage.json")
    
    if reports:
        print("\nGenerated Reports:")
        for report in reports:
            print(f"  {report}")
    else:
        print("\nNo reports generated - check for errors above")
    
    print("\nNext Steps:")
    print("  1. Review the coverage analysis report for priority areas")
    print("  2. Start with high-priority files (core analysis engines)")
    print("  3. Aim for 70% coverage as initial target")
    print("  4. Focus on critical business logic first")
    
    print("\n" + "="*60)


def main():
    """Main coverage analysis workflow."""
    logger.info("Starting automated coverage analysis workflow...")
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    logger.info(f"Working directory: {project_root}")
    
    try:
        # Setup environment
        if not setup_environment():
            logger.error("Failed to set up environment")
            return 1
        
        # Clean previous coverage data
        clean_previous_coverage()
        
        # Run basic coverage test
        if not run_basic_coverage():
            logger.error("Basic coverage test failed")
            return 1
        
        # Run unit tests with coverage (best effort)
        run_unit_coverage()  # Don't fail on this step
        
        # Generate analysis report
        if not generate_coverage_analysis():
            logger.error("Failed to generate coverage analysis")
            return 1
        
        # Print summary
        print_summary()
        
        # Open reports (interactive mode)
        if len(sys.argv) > 1 and sys.argv[1] == '--no-open':
            logger.info("Skipping report opening (--no-open specified)")
        else:
            open_reports(interactive=True)
        
        logger.info("Coverage analysis workflow completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Coverage analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())