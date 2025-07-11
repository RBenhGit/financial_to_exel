"""
Launch script for the Streamlit FCF Analysis application

Run this script to start the modern web-based FCF analysis tool.
"""

import subprocess
import sys
import os

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy', 'openpyxl', 'scipy', 'yfinance']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Please install requirements using:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def launch_app():
    """Launch the Streamlit application"""
    script_path = os.path.join(os.path.dirname(__file__), 'fcf_analysis_streamlit.py')
    
    if not os.path.exists(script_path):
        print(f"❌ Application script not found: {script_path}")
        return False
    
    print("🚀 Launching FCF Analysis Tool...")
    print("📊 The application will open in your default web browser")
    print("🔗 URL: http://localhost:8501")
    print("\n⭐ Features:")
    print("   - Interactive FCF Analysis")
    print("   - DCF Valuation Calculator")
    print("   - Sensitivity Analysis")
    print("   - Professional Charts & Visualizations")
    print("   - Export Capabilities")
    print("\n" + "="*50)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', script_path,
            '--server.port', '8501',
            '--server.headless', 'false'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch application: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
        return True
    
    return True

if __name__ == "__main__":
    print("🔍 Checking requirements...")
    if check_requirements():
        print("✅ All requirements satisfied")
        launch_app()
    else:
        sys.exit(1)