"""
E2E test runner for the Financial Analysis Streamlit application.
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path


def check_streamlit_running(port=8501, max_retries=5):
    """Check if Streamlit is already running."""
    for _ in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(1)
    return False


def start_streamlit_for_testing():
    """Start Streamlit app for testing if not already running."""
    if check_streamlit_running():
        print("Streamlit app is already running on port 8501")
        return None
    
    print("Starting Streamlit app for testing...")
    app_path = Path(__file__).parent.parent.parent / "ui" / "streamlit" / "fcf_analysis_streamlit.py"
    
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port=8501",
        "--server.headless=true",
        "--server.runOnSave=false",
        "--logger.level=error"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for app to start
    if check_streamlit_running(max_retries=30):
        print("Streamlit app started successfully")
        return process
    else:
        process.terminate()
        raise RuntimeError("Failed to start Streamlit app")


def run_e2e_tests():
    """Run the E2E test suite."""
    # Change to project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Start Streamlit if needed
    streamlit_process = None
    try:
        streamlit_process = start_streamlit_for_testing()
        
        # Run E2E tests
        print("Running E2E tests...")
        
        test_command = [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--tb=short",
            "-m", "e2e",
            "--maxfail=5",  # Stop after 5 failures
            "--timeout=300",  # 5 minute timeout per test
        ]
        
        # Add browser configuration
        test_command.extend([
            "--browser", "chromium",
            "--headed=false"
        ])
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running E2E tests: {e}")
        return False
        
    finally:
        # Clean up Streamlit process
        if streamlit_process:
            try:
                streamlit_process.terminate()
                streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()


def run_specific_test_suite(suite_name):
    """Run a specific test suite."""
    suite_mapping = {
        "basic": "tests/e2e/test_streamlit_app.py",
        "workflows": "tests/e2e/test_analysis_workflows.py",
        "performance": "tests/e2e/test_performance.py"
    }
    
    if suite_name not in suite_mapping:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_mapping.keys())}")
        return False
    
    # Change to project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Start Streamlit if needed
    streamlit_process = None
    try:
        streamlit_process = start_streamlit_for_testing()
        
        # Run specific test suite
        print(f"Running {suite_name} test suite...")
        
        test_command = [
            sys.executable, "-m", "pytest",
            suite_mapping[suite_name],
            "-v",
            "--tb=short",
            "--browser", "chromium",
            "--headed=false"
        ]
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running {suite_name} tests: {e}")
        return False
        
    finally:
        # Clean up
        if streamlit_process:
            try:
                streamlit_process.terminate()
                streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        success = run_specific_test_suite(suite_name)
    else:
        success = run_e2e_tests()
    
    sys.exit(0 if success else 1)