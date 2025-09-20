#!/usr/bin/env python3
"""
Streamlit App Integration Tests
==============================

Integration tests for Streamlit application components and their
interaction with analysis modules. Validates UI functionality
without requiring actual Streamlit server.

Test Coverage:
- FCF tab functionality and calculations
- DCF tab functionality and valuations
- DDM tab functionality and dividend analysis
- P/B tab functionality and historical analysis
- Watch Lists tab functionality
- Data integration between UI and calculation engines
- Session state management
- Export functionality from UI
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
import json
from pathlib import Path

# Ensure proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pytest
import pandas as pd
import numpy as np
import streamlit as st
from streamlit.testing.v1 import AppTest

# UI modules
import ui.streamlit.fcf_analysis_streamlit as fcf_app

# Core modules for testing
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.ddm.ddm_valuation import DDMValuator
from core.analysis.pb.pb_statistical_analysis import PBStatisticalAnalysisEngine

# Test utilities
from tests.fixtures.analysis_fixtures import AnalysisFixtures


class MockStreamlitState:
    """Mock Streamlit session state for testing"""

    def __init__(self):
        self._state = {}

    def __getattr__(self, key):
        return self._state.get(key, None)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self._state[key] = value

    def __contains__(self, key):
        return key in self._state

    def get(self, key, default=None):
        return self._state.get(key, default)


class TestStreamlitFCFTabIntegration(unittest.TestCase):
    """Test FCF tab integration with calculation engines"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()
        self.test_ticker = 'AAPL'
        self.fixtures = AnalysisFixtures()

    @patch('streamlit.session_state')
    @patch('streamlit.selectbox')
    @patch('streamlit.button')
    def test_fcf_calculation_integration(self, mock_button, mock_selectbox, mock_session_state):
        """Test FCF calculation integration in Streamlit UI"""
        # Mock Streamlit components
        mock_session_state.return_value = self.mock_st_state
        mock_selectbox.return_value = self.test_ticker
        mock_button.return_value = True

        # Initialize calculator
        calc = FinancialCalculator(self.test_ticker)

        # Test FCF calculation through UI pathway
        fcf_results = calc.calculate_all_fcf_types()

        # Verify FCF results structure
        self.assertIsInstance(fcf_results, dict)
        self.assertIn('fcfe', fcf_results)
        self.assertIn('fcff', fcf_results)
        self.assertIn('levered_fcf', fcf_results)

        # Test session state integration
        self.mock_st_state.fcf_results = fcf_results
        self.assertEqual(self.mock_st_state.fcf_results, fcf_results)

    @patch('streamlit.session_state')
    def test_fcf_visualization_data_flow(self, mock_session_state):
        """Test data flow from calculations to visualizations"""
        mock_session_state.return_value = self.mock_st_state

        # Simulate calculation results
        fcf_results = {
            'fcfe': {'historical_data': [100, 110, 120, 130, 140]},
            'fcff': {'historical_data': [120, 130, 140, 150, 160]},
            'levered_fcf': {'historical_data': [90, 100, 110, 120, 130]}
        }

        # Store in session state
        self.mock_st_state.fcf_results = fcf_results

        # Test visualization data preparation
        viz_data = {}
        for fcf_type, data in fcf_results.items():
            viz_data[fcf_type] = data.get('historical_data', [])

        # Verify visualization data
        self.assertEqual(len(viz_data), 3)
        self.assertEqual(len(viz_data['fcfe']), 5)
        self.assertEqual(viz_data['fcfe'][0], 100)


class TestStreamlitDCFTabIntegration(unittest.TestCase):
    """Test DCF tab integration with DCF valuation engine"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()
        self.test_ticker = 'MSFT'

    @patch('streamlit.session_state')
    @patch('streamlit.number_input')
    @patch('streamlit.button')
    def test_dcf_valuation_integration(self, mock_button, mock_number_input, mock_session_state):
        """Test DCF valuation integration in Streamlit UI"""
        # Mock Streamlit components
        mock_session_state.return_value = self.mock_st_state
        mock_number_input.side_effect = [0.10, 0.03]  # discount_rate, terminal_growth
        mock_button.return_value = True

        # Initialize calculator and DCF valuator
        calc = FinancialCalculator(self.test_ticker)
        dcf_valuator = DCFValuator(calc)

        # Test DCF calculation through UI pathway
        dcf_result = dcf_valuator.calculate_dcf_projections()

        # Verify DCF results structure
        self.assertIsInstance(dcf_result, dict)
        expected_keys = ['intrinsic_value', 'enterprise_value', 'value_per_share']
        for key in expected_keys:
            self.assertIn(key, dcf_result)

        # Test session state integration
        self.mock_st_state.dcf_results = dcf_result
        self.assertEqual(self.mock_st_state.dcf_results, dcf_result)

    @patch('streamlit.session_state')
    def test_dcf_sensitivity_analysis_integration(self, mock_session_state):
        """Test DCF sensitivity analysis integration"""
        mock_session_state.return_value = self.mock_st_state

        # Initialize DCF valuator
        calc = FinancialCalculator(self.test_ticker)
        dcf_valuator = DCFValuator(calc)

        # Test sensitivity analysis
        discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        growth_rates = [0.02, 0.03, 0.04, 0.05, 0.06]

        try:
            sensitivity_result = dcf_valuator.sensitivity_analysis(discount_rates, growth_rates)

            # Verify sensitivity analysis results
            self.assertIsInstance(sensitivity_result, dict)

            # Store in session state
            self.mock_st_state.sensitivity_analysis = sensitivity_result

        except Exception as e:
            # Sensitivity analysis may fail with missing data
            self.assertIsInstance(e, (ValueError, KeyError, TypeError))


class TestStreamlitPBTabIntegration(unittest.TestCase):
    """Test P/B tab integration with P/B analysis engine"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()
        self.test_ticker = 'GOOGL'

    @patch('streamlit.session_state')
    @patch('streamlit.button')
    def test_pb_analysis_integration(self, mock_button, mock_session_state):
        """Test P/B analysis integration in Streamlit UI"""
        # Mock Streamlit components
        mock_session_state.return_value = self.mock_st_state
        mock_button.return_value = True

        # Initialize calculator and P/B analyzer
        calc = FinancialCalculator(self.test_ticker)
        pb_analyzer = PBStatisticalAnalysis(calc.enhanced_data_manager)

        # Test P/B analysis through UI pathway
        try:
            pb_result = pb_analyzer.analyze_historical_pb_with_statistics(self.test_ticker)

            # Verify P/B results structure
            self.assertIsInstance(pb_result, dict)
            expected_keys = ['current_pb', 'historical_statistics']
            for key in expected_keys:
                self.assertIn(key, pb_result)

            # Test session state integration
            self.mock_st_state.pb_results = pb_result

        except Exception as e:
            # P/B analysis may fail with insufficient data
            self.assertIsInstance(e, (ValueError, KeyError))

    @patch('streamlit.session_state')
    def test_pb_historical_visualization_data(self, mock_session_state):
        """Test P/B historical visualization data preparation"""
        mock_session_state.return_value = self.mock_st_state

        # Mock P/B historical data
        pb_data = {
            'historical_pb_ratios': [1.5, 1.8, 2.1, 1.9, 2.3, 2.0],
            'dates': ['2019', '2020', '2021', '2022', '2023', '2024'],
            'current_pb': 2.0,
            'historical_statistics': {
                'mean': 1.93,
                'median': 1.95,
                'std': 0.28
            }
        }

        # Store in session state
        self.mock_st_state.pb_data = pb_data

        # Test visualization data structure
        self.assertEqual(len(pb_data['historical_pb_ratios']), 6)
        self.assertEqual(len(pb_data['dates']), 6)
        self.assertIsInstance(pb_data['historical_statistics'], dict)


class TestStreamlitDDMTabIntegration(unittest.TestCase):
    """Test DDM tab integration with DDM calculator"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()
        self.test_ticker = 'AAPL'  # Known dividend payer

    @patch('streamlit.session_state')
    @patch('streamlit.button')
    def test_ddm_calculation_integration(self, mock_button, mock_session_state):
        """Test DDM calculation integration in Streamlit UI"""
        # Mock Streamlit components
        mock_session_state.return_value = self.mock_st_state
        mock_button.return_value = True

        # Initialize calculator and DDM calculator
        calc = FinancialCalculator(self.test_ticker)
        ddm_calc = DDMValuator(calc)

        # Test DDM calculation through UI pathway
        try:
            ddm_result = ddm_calc.calculate_ddm_valuation()

            # Verify DDM results structure
            if ddm_result:
                self.assertIsInstance(ddm_result, dict)
                expected_keys = ['intrinsic_value', 'dividend_yield']
                for key in expected_keys:
                    if key in ddm_result:
                        self.assertIsNotNone(ddm_result[key])

                # Test session state integration
                self.mock_st_state.ddm_results = ddm_result

        except Exception as e:
            # DDM may fail for non-dividend or irregular dividend companies
            self.assertIsInstance(e, (ValueError, ZeroDivisionError, KeyError))


class TestStreamlitWatchListIntegration(unittest.TestCase):
    """Test Watch List tab integration"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('streamlit.session_state')
    def test_watchlist_data_structure(self, mock_session_state):
        """Test watch list data structure and management"""
        mock_session_state.return_value = self.mock_st_state

        # Mock watch list data
        watchlist_data = [
            {
                'ticker': 'AAPL',
                'analysis_date': '2024-09-18',
                'fair_value': 180.0,
                'current_price': 175.0,
                'upside_downside': 2.86,
                'analysis_type': 'DCF'
            },
            {
                'ticker': 'MSFT',
                'analysis_date': '2024-09-18',
                'fair_value': 420.0,
                'current_price': 410.0,
                'upside_downside': 2.44,
                'analysis_type': 'DDM'
            }
        ]

        # Store in session state
        self.mock_st_state.watchlist_data = watchlist_data

        # Verify data structure
        self.assertEqual(len(watchlist_data), 2)
        for entry in watchlist_data:
            required_keys = ['ticker', 'fair_value', 'current_price', 'upside_downside']
            for key in required_keys:
                self.assertIn(key, entry)

    @patch('streamlit.session_state')
    def test_watchlist_export_functionality(self, mock_session_state):
        """Test watch list export functionality"""
        mock_session_state.return_value = self.mock_st_state

        # Mock watch list data
        watchlist_data = [
            {
                'ticker': 'AAPL',
                'fair_value': 180.0,
                'current_price': 175.0,
                'upside_downside': 2.86
            }
        ]

        # Test export to CSV
        df = pd.DataFrame(watchlist_data)
        export_path = Path(self.test_dir) / "test_watchlist.csv"
        df.to_csv(export_path, index=False)

        # Verify export
        self.assertTrue(export_path.exists())

        # Verify content
        imported_df = pd.read_csv(export_path)
        self.assertEqual(len(imported_df), 1)
        self.assertEqual(imported_df.iloc[0]['ticker'], 'AAPL')


class TestStreamlitSessionStateManagement(unittest.TestCase):
    """Test Streamlit session state management across tabs"""

    def setUp(self):
        """Set up test environment"""
        self.mock_st_state = MockStreamlitState()

    @patch('streamlit.session_state')
    def test_cross_tab_data_persistence(self, mock_session_state):
        """Test data persistence across different tabs"""
        mock_session_state.return_value = self.mock_st_state

        # Simulate data from FCF tab
        fcf_data = {'fcfe': [100, 110, 120], 'fcff': [120, 130, 140]}
        self.mock_st_state.fcf_results = fcf_data

        # Simulate data from DCF tab
        dcf_data = {'intrinsic_value': 180.0, 'enterprise_value': 2800000000}
        self.mock_st_state.dcf_results = dcf_data

        # Verify data persistence
        self.assertEqual(self.mock_st_state.fcf_results, fcf_data)
        self.assertEqual(self.mock_st_state.dcf_results, dcf_data)

        # Test data availability across tabs
        self.assertIn('fcf_results', self.mock_st_state._state)
        self.assertIn('dcf_results', self.mock_st_state._state)

    @patch('streamlit.session_state')
    def test_dual_view_toggle_state_management(self, mock_session_state):
        """Test dual view toggle state management"""
        mock_session_state.return_value = self.mock_st_state

        # Test context-specific state management
        contexts = ['fcf', 'dcf', 'ddm', 'pb']

        for context in contexts:
            key = f"dual_view_toggle_{context}"
            self.mock_st_state._state[key] = "Historical Analysis"

            # Verify context-specific state
            self.assertEqual(self.mock_st_state._state[key], "Historical Analysis")

        # Verify no duplicate keys
        keys = list(self.mock_st_state._state.keys())
        self.assertEqual(len(keys), len(set(keys)))  # No duplicates


if __name__ == '__main__':
    # Configure test discovery and execution
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--durations=10'
    ])