"""
Windows-Specific Streamlit Launcher

This script ensures proper Unicode and encoding setup for Windows environments
before launching the Streamlit application.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_windows_environment():
    """Setup Windows environment for optimal Unicode support."""
    if sys.platform == 'win32':
        # Set environment variables for UTF-8 support
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'

        # Set console code page to UTF-8 if possible
        try:
            # Change console code page to UTF-8 (65001)
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        except Exception:
            pass

        print("✓ Windows environment configured for UTF-8 support")
    else:
        print("ℹ Non-Windows platform detected, using default settings")


def validate_dependencies():
    """Validate that required packages are installed."""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'yfinance',
        'requests',
        'openpyxl',
        'xlsxwriter'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False

    print("✓ All required packages are installed")
    return True


def run_streamlit_app():
    """Launch the Streamlit application."""
    app_file = current_dir / "fcf_analysis_streamlit.py"

    if not app_file.exists():
        print(f"❌ Application file not found: {app_file}")
        return False

    print(f"🚀 Launching Streamlit app: {app_file}")

    # Launch Streamlit with optimal settings for Windows
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_file),
        "--theme.base=light",
        "--server.maxUploadSize=200"
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True


def main():
    """Main launcher function."""
    print("=" * 60)
    print("Financial Analysis - Windows Streamlit Launcher")
    print("=" * 60)

    # Setup Windows environment
    setup_windows_environment()

    # Validate dependencies
    if not validate_dependencies():
        sys.exit(1)

    # Test encoding utilities
    try:
        from utils.encoding_utils import validate_unicode_support, get_system_encoding_info

        if validate_unicode_support():
            print("✓ Unicode support validation passed")
        else:
            print("⚠ Unicode support validation failed - some characters may not display correctly")

        # Display encoding info
        encoding_info = get_system_encoding_info()
        print(f"ℹ System encoding: {encoding_info.get('default_encoding', 'unknown')}")
        print(f"ℹ Recommended CSV encoding: {encoding_info.get('recommended_csv', 'utf-8-sig')}")

    except ImportError as e:
        print(f"⚠ Could not import encoding utilities: {e}")

    print("-" * 60)
    print("Starting Financial Analysis Application...")
    print("Press Ctrl+C to stop the application")
    print("-" * 60)

    # Launch the application
    success = run_streamlit_app()

    if success:
        print("\n✓ Application completed successfully")
    else:
        print("\n❌ Application failed to start")
        sys.exit(1)


if __name__ == "__main__":
    main()
