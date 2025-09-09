"""
Test core module imports to ensure basic functionality
"""
import pytest


def test_config_imports():
    """Test that configuration modules import correctly"""
    from config import get_config, get_dcf_config, get_export_config
    assert get_config is not None
    assert get_dcf_config is not None
    assert get_export_config is not None


def test_main_module_imports():
    """Test that main modules import correctly"""
    from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
    from core.data_processing.processors.data_processing import DataProcessor
    from core.analysis.dcf.dcf_valuation import DCFValuator
    from core.analysis.engines.financial_calculations import FinancialCalculator
    from core.analysis.pb.pb_valuation import PBValuator
    from core.analysis.ddm.ddm_valuation import DDMValuator
    
    assert CentralizedDataManager is not None
    assert DataProcessor is not None
    assert DCFValuator is not None
    assert FinancialCalculator is not None
    assert PBValuator is not None
    assert DDMValuator is not None


def test_package_init():
    """Test that the package __init__ works correctly"""
    import financial_to_exel
    
    # Test version info
    assert hasattr(financial_to_exel, '__version__')
    assert hasattr(financial_to_exel, '__author__')
    
    # Test core imports are available
    assert hasattr(financial_to_exel, 'CentralizedDataManager')
    assert hasattr(financial_to_exel, 'DCFValuator')
    assert hasattr(financial_to_exel, 'FinancialCalculator')


def test_error_handler_import():
    """Test error handler module imports"""
    from error_handler import (
        FinancialAnalysisError,
        ExcelDataError,
        ValidationError,
        CalculationError,
        log_error,
        validate_financial_data
    )
    
    assert FinancialAnalysisError is not None
    assert ExcelDataError is not None
    assert ValidationError is not None 
    assert CalculationError is not None
    assert log_error is not None
    assert validate_financial_data is not None


def test_data_sources_import():
    """Test data sources module imports"""
    from data_sources import FinancialDataRequest, DataQualityMetrics
    
    assert FinancialDataRequest is not None
    assert DataQualityMetrics is not None
    
    # Test basic instantiation
    request = FinancialDataRequest(ticker="TEST")
    assert request.ticker == "TEST"
    assert request.data_types == ['price', 'fundamentals']  # default value
    
    metrics = DataQualityMetrics()
    assert metrics.completeness == 0.0  # default value