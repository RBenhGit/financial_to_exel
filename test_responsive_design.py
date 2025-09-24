#!/usr/bin/env python3
"""
Test script for responsive design implementation
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_responsive_functions():
    """Test the responsive design helper functions"""
    print("Testing responsive design implementation...")

    try:
        # Import the responsive functions
        from ui.streamlit.fcf_analysis_streamlit import (
            get_responsive_columns,
            create_mobile_friendly_tabs,
            render_responsive_metric_cards,
            create_responsive_chart_config,
            create_responsive_plotly_layout
        )

        print("[OK] All responsive helper functions imported successfully")

        # Test responsive chart config
        config = create_responsive_chart_config()
        assert 'responsive' in config
        assert config['responsive'] == True
        print("[OK] Responsive chart configuration test passed")

        # Test responsive plotly layout
        layout = create_responsive_plotly_layout("Test Chart", 400)
        assert 'autosize' in layout
        assert layout['autosize'] == True
        assert layout['height'] == 400
        print("[OK] Responsive Plotly layout test passed")

        print("\n[SUCCESS] All responsive design tests passed!")
        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        return False

def test_responsive_css():
    """Test that responsive CSS is properly formatted"""
    print("\nTesting responsive CSS implementation...")

    try:
        # Read the main Streamlit file and check for responsive CSS
        with open('ui/streamlit/fcf_analysis_streamlit.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key responsive elements
        responsive_checks = [
            '@media (min-width: 375px)',
            '@media (min-width: 576px)',
            '@media (min-width: 768px)',
            '@media (min-width: 992px)',
            '@media (min-width: 1024px)',
            '@media (min-width: 1200px)',
            '@media (min-width: 1400px)',
            'create_mobile_friendly_tabs',
            'render_responsive_chart',
            'responsive-columns'
        ]

        for check in responsive_checks:
            if check in content:
                print(f"[OK] Found: {check}")
            else:
                print(f"[ERROR] Missing: {check}")
                return False

        print("[OK] All responsive CSS elements found")
        return True

    except Exception as e:
        print(f"[ERROR] CSS test error: {e}")
        return False

def test_mobile_tab_implementation():
    """Test that mobile-friendly tabs are implemented"""
    print("\nTesting mobile tab implementation...")

    try:
        with open('ui/streamlit/fcf_analysis_streamlit.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that create_mobile_friendly_tabs is used in main function
        if 'create_mobile_friendly_tabs(' in content:
            # Count occurrences
            occurrences = content.count('create_mobile_friendly_tabs(')
            print(f"[OK] Mobile-friendly tabs implemented in {occurrences} locations")
            return True
        else:
            print("[ERROR] Mobile-friendly tabs not implemented")
            return False

    except Exception as e:
        print(f"[ERROR] Mobile tab test error: {e}")
        return False

def main():
    """Run all responsive design tests"""
    print("=" * 60)
    print("RESPONSIVE DESIGN IMPLEMENTATION TEST")
    print("=" * 60)

    tests = [
        test_responsive_functions,
        test_responsive_css,
        test_mobile_tab_implementation
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED - Responsive design implementation successful!")
    else:
        print("[ERROR] Some tests failed - Please review implementation")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)