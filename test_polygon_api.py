#!/usr/bin/env python3
"""
Simple test script for Polygon.io API connectivity
"""
import os
import requests
import json
from datetime import datetime

def test_polygon_connection():
    """Test Polygon.io API connection"""
    print("Testing Polygon.io API Connection...")

    # Check for API key
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("ERROR: No POLYGON_API_KEY found in environment variables")
        print("INFO: Set POLYGON_API_KEY in your .env file or environment")
        return False

    # Test basic API endpoint
    base_url = "https://api.polygon.io"
    test_endpoints = [
        f"/v1/meta/symbols/stocks/tickers?limit=1&apikey={api_key}",
        f"/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-02?apikey={api_key}",
        f"/v3/reference/tickers/AAPL?apikey={api_key}"
    ]

    results = []

    for endpoint in test_endpoints:
        try:
            print(f"Testing endpoint: {endpoint.split('?')[0]}")

            response = requests.get(
                base_url + endpoint,
                timeout=10,
                headers={'User-Agent': 'Financial Analysis Tool'}
            )

            response_time = response.elapsed.total_seconds()

            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS - Response time: {response_time:.2f}s")
                print(f"Data keys: {list(data.keys())}")
                results.append({"endpoint": endpoint, "status": "success", "time": response_time})
            elif response.status_code == 401:
                print(f"Authentication Error (401) - Check your API key")
                results.append({"endpoint": endpoint, "status": "auth_error", "time": response_time})
            elif response.status_code == 403:
                print(f"Forbidden (403) - API key may not have required permissions")
                results.append({"endpoint": endpoint, "status": "forbidden", "time": response_time})
            elif response.status_code == 429:
                print(f"Rate Limited (429) - Too many requests")
                results.append({"endpoint": endpoint, "status": "rate_limited", "time": response_time})
            else:
                print(f"ERROR {response.status_code}: {response.text[:200]}")
                results.append({"endpoint": endpoint, "status": "error", "code": response.status_code, "time": response_time})

        except requests.exceptions.Timeout:
            print(f"Timeout - Request took longer than 10 seconds")
            results.append({"endpoint": endpoint, "status": "timeout"})
        except requests.exceptions.ConnectionError:
            print(f"Connection Error - Check internet connection")
            results.append({"endpoint": endpoint, "status": "connection_error"})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            results.append({"endpoint": endpoint, "status": "unexpected_error", "error": str(e)})

        print("-" * 50)

    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)

    print(f"SUMMARY: {success_count}/{total_count} endpoints successful")

    if success_count > 0:
        print("SUCCESS: Polygon.io API is accessible")
        return True
    else:
        print("ERROR: Polygon.io API is not accessible")
        return False

if __name__ == "__main__":
    test_polygon_connection()