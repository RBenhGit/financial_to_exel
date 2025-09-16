#!/usr/bin/env python3
"""
Test script for all financial API connections
"""
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_alpha_vantage():
    """Test Alpha Vantage API connection"""
    print("Testing Alpha Vantage API...")

    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("ERROR: No ALPHA_VANTAGE_API_KEY found")
        return False

    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL&apikey={api_key}"

    try:
        response = requests.get(url, timeout=30)
        response_time = response.elapsed.total_seconds()

        if response.status_code == 200:
            data = response.json()
            if 'Symbol' in data:
                print(f"SUCCESS - Response time: {response_time:.2f}s")
                print(f"Company: {data.get('Name', 'N/A')}")
                return True
            else:
                print(f"ERROR: API returned error - {data}")
                return False
        else:
            print(f"ERROR {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_fmp():
    """Test Financial Modeling Prep API connection"""
    print("Testing Financial Modeling Prep API...")

    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("ERROR: No FMP_API_KEY found")
        return False

    url = f"https://financialmodelingprep.com/api/v3/profile/AAPL?apikey={api_key}"

    try:
        response = requests.get(url, timeout=30)
        response_time = response.elapsed.total_seconds()

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"SUCCESS - Response time: {response_time:.2f}s")
                print(f"Company: {data[0].get('companyName', 'N/A')}")
                return True
            else:
                print(f"ERROR: API returned unexpected data - {data}")
                return False
        else:
            print(f"ERROR {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_polygon():
    """Test Polygon.io API connection"""
    print("Testing Polygon.io API...")

    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("ERROR: No POLYGON_API_KEY found")
        return False

    url = f"https://api.polygon.io/v3/reference/tickers/AAPL?apikey={api_key}"

    try:
        response = requests.get(url, timeout=30)
        response_time = response.elapsed.total_seconds()

        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                print(f"SUCCESS - Response time: {response_time:.2f}s")
                print(f"Company: {data['results'].get('name', 'N/A')}")
                return True
            else:
                print(f"ERROR: API returned unexpected data - {data}")
                return False
        else:
            print(f"ERROR {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_yfinance():
    """Test Yahoo Finance via yfinance library"""
    print("Testing Yahoo Finance...")

    try:
        import yfinance as yf
        ticker = yf.Ticker("AAPL")
        info = ticker.info

        if 'symbol' in info:
            print("SUCCESS - Yahoo Finance working")
            print(f"Company: {info.get('longName', 'N/A')}")
            return True
        else:
            print("ERROR: No data returned from Yahoo Finance")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """Test all APIs"""
    print("=" * 60)
    print("TESTING ALL FINANCIAL API CONNECTIONS")
    print("=" * 60)

    results = {}

    print("\n1. Yahoo Finance:")
    print("-" * 20)
    results['yfinance'] = test_yfinance()

    print("\n2. Alpha Vantage:")
    print("-" * 20)
    results['alpha_vantage'] = test_alpha_vantage()

    print("\n3. Financial Modeling Prep:")
    print("-" * 30)
    results['fmp'] = test_fmp()

    print("\n4. Polygon.io:")
    print("-" * 15)
    results['polygon'] = test_polygon()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    for api, success in results.items():
        status = "ONLINE" if success else "OFFLINE"
        print(f"{api}: {status}")

    print(f"\nOverall: {success_count}/{total_count} APIs working")

    if success_count == total_count:
        print("SUCCESS: All APIs are connected!")
    elif success_count > 0:
        print("PARTIAL: Some APIs are working")
    else:
        print("ERROR: No APIs are working")

if __name__ == "__main__":
    main()