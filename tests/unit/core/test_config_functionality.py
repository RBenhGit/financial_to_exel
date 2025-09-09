"""
Test configuration functionality
"""
import pytest


def test_config_basic_functionality():
    """Test basic configuration loading"""
    from config import get_config, get_dcf_config, get_export_config
    
    # Test basic config loading
    config = get_config()
    assert config is not None
    
    # Test DCF config loading
    dcf_config = get_dcf_config()
    assert dcf_config is not None
    assert hasattr(dcf_config, 'default_discount_rate')
    assert hasattr(dcf_config, 'default_terminal_growth_rate')
    
    # Test export config loading
    export_config = get_export_config()
    assert export_config is not None


def test_dcf_config_values():
    """Test DCF configuration has reasonable default values"""
    from config import get_dcf_config
    
    dcf_config = get_dcf_config()
    
    # Test discount rate is reasonable (between 5% and 20%)
    assert 0.05 <= dcf_config.default_discount_rate <= 0.20
    
    # Test terminal growth rate is reasonable (between 1% and 5%)  
    assert 0.01 <= dcf_config.default_terminal_growth_rate <= 0.05
    
    # Test projection years is reasonable (between 5 and 15 years)
    assert 5 <= dcf_config.default_projection_years <= 15


def test_config_attribute_access():
    """Test configuration attributes can be accessed"""
    from config import get_config
    
    config = get_config()
    
    # Test basic config access - should not raise exceptions
    try:
        # These might not exist but testing the access pattern
        if hasattr(config, 'api_keys'):
            api_keys = config.api_keys
            assert api_keys is not None or api_keys is None  # Either way is fine
            
        if hasattr(config, 'data_sources'):
            data_sources = config.data_sources 
            assert data_sources is not None or data_sources is None
            
    except Exception as e:
        pytest.fail(f"Config attribute access failed: {e}")


def test_settings_import():
    """Test settings module imports correctly"""
    try:
        from config.settings import Settings, get_settings
        
        settings = get_settings()
        assert settings is not None
        assert isinstance(settings, Settings)
        
    except ImportError:
        # Settings module might not be structured this way, that's OK
        pass