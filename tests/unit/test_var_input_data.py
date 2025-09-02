"""
Unit Tests for VarInputData Core Storage System
===============================================

Comprehensive unit tests covering all functionality of the VarInputData system including:
- Variable storage and retrieval
- Historical data management
- Data validation integration
- Event system
- Thread safety
- Cache operations
- Metadata tracking
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the components to test
from core.data_processing.var_input_data import (
    VarInputData,
    get_var_input_data,
    VariableMetadata,
    VariableValue,
    HistoricalDataPoint,
    DataChangeEvent,
    VarInputDataEventSystem,
    get_variable,
    set_variable,
    get_historical_data,
    clear_cache
)

from core.data_processing.financial_variable_registry import (
    VariableDefinition,
    VariableCategory,
    DataType,
    Units,
    ValidationRule,
    get_registry
)


class TestVariableMetadata:
    """Test the VariableMetadata dataclass"""
    
    def test_metadata_creation(self):
        """Test creating metadata with all fields"""
        metadata = VariableMetadata(
            source="excel",
            timestamp=datetime.now(),
            quality_score=0.95,
            validation_passed=True,
            period="2023"
        )
        
        assert metadata.source == "excel"
        assert metadata.quality_score == 0.95
        assert metadata.validation_passed is True
        assert metadata.period == "2023"
    
    def test_metadata_to_dict(self):
        """Test metadata serialization to dictionary"""
        timestamp = datetime.now()
        metadata = VariableMetadata(
            source="api",
            timestamp=timestamp,
            quality_score=0.8,
            period="Q1-2023"
        )
        
        result = metadata.to_dict()
        
        assert result['source'] == "api"
        assert result['timestamp'] == timestamp.isoformat()
        assert result['quality_score'] == 0.8
        assert result['period'] == "Q1-2023"
        assert isinstance(result, dict)


class TestVariableValue:
    """Test the VariableValue dataclass"""
    
    def test_variable_value_creation(self):
        """Test creating a variable value with metadata"""
        metadata = VariableMetadata(source="test", timestamp=datetime.now())
        var_value = VariableValue(value=100.5, metadata=metadata)
        
        assert var_value.value == 100.5
        assert var_value.metadata.source == "test"
        assert isinstance(var_value.metadata.timestamp, datetime)
    
    def test_variable_value_auto_timestamp(self):
        """Test that timestamp is auto-set if missing"""
        metadata = VariableMetadata(source="test", timestamp=None)
        var_value = VariableValue(value=100, metadata=metadata)
        
        # The __post_init__ should set timestamp
        assert var_value.metadata.timestamp is not None
        assert isinstance(var_value.metadata.timestamp, datetime)


class TestHistoricalDataPoint:
    """Test the HistoricalDataPoint dataclass"""
    
    def test_historical_point_creation(self):
        """Test creating a historical data point"""
        metadata = VariableMetadata(source="excel", timestamp=datetime.now())
        point = HistoricalDataPoint(
            symbol="AAPL",
            variable_name="revenue", 
            period="2023",
            value=394328,
            metadata=metadata
        )
        
        assert point.symbol == "AAPL"
        assert point.variable_name == "revenue"
        assert point.period == "2023"
        assert point.value == 394328
    
    def test_historical_point_normalization(self):
        """Test that symbol and variable names are normalized"""
        metadata = VariableMetadata(source="test", timestamp=datetime.now())
        point = HistoricalDataPoint(
            symbol="aapl",  # lowercase
            variable_name="REVENUE",  # uppercase
            period="2023",
            value=100,
            metadata=metadata
        )
        
        assert point.symbol == "AAPL"  # Should be uppercase
        assert point.variable_name == "revenue"  # Should be lowercase
    
    def test_historical_point_validation(self):
        """Test validation of required fields"""
        metadata = VariableMetadata(source="test", timestamp=datetime.now())
        
        with pytest.raises(ValueError):
            HistoricalDataPoint(
                symbol="",  # Empty symbol should raise error
                variable_name="revenue",
                period="2023",
                value=100,
                metadata=metadata
            )


class TestVarInputDataEventSystem:
    """Test the event system"""
    
    def setup_method(self):
        """Set up a fresh event system for each test"""
        self.event_system = VarInputDataEventSystem()
        self.callback_calls = []
    
    def test_subscribe_and_emit(self):
        """Test subscribing to events and receiving notifications"""
        def test_callback(**kwargs):
            self.callback_calls.append(kwargs)
        
        # Subscribe to variable set events
        self.event_system.subscribe(DataChangeEvent.VARIABLE_SET, test_callback)
        
        # Emit an event
        self.event_system.emit(
            DataChangeEvent.VARIABLE_SET,
            symbol="AAPL",
            variable_name="revenue",
            value=100
        )
        
        # Verify callback was called
        assert len(self.callback_calls) == 1
        assert self.callback_calls[0]['symbol'] == "AAPL"
        assert self.callback_calls[0]['variable_name'] == "revenue"
        assert self.callback_calls[0]['value'] == 100
    
    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        def test_callback(**kwargs):
            self.callback_calls.append(kwargs)
        
        # Subscribe then unsubscribe
        self.event_system.subscribe(DataChangeEvent.VARIABLE_SET, test_callback)
        self.event_system.unsubscribe(DataChangeEvent.VARIABLE_SET, test_callback)
        
        # Emit event
        self.event_system.emit(DataChangeEvent.VARIABLE_SET, symbol="TEST")
        
        # Should not receive any callbacks
        assert len(self.callback_calls) == 0


class TestVarInputData:
    """Test the main VarInputData class"""
    
    def setup_method(self):
        """Set up fresh instances for each test"""
        # Clear any existing singleton instance
        VarInputData._instance = None
        
        # Mock the dependencies to avoid side effects
        with patch('core.data_processing.var_input_data.get_registry') as mock_registry, \
             patch('core.data_processing.var_input_data.UniversalDataRegistry') as mock_data_registry:
            
            # Create a mock variable registry
            self.mock_var_registry = Mock()
            mock_registry.return_value = self.mock_var_registry
            
            # Create a mock data registry
            self.mock_data_registry = Mock()
            mock_data_registry.return_value = self.mock_data_registry
            
            # Create test variable definition
            self.test_var_def = VariableDefinition(
                name="revenue",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.CURRENCY,
                units=Units.MILLIONS_USD,
                description="Test revenue variable",
                validation_rules=[
                    ValidationRule("non_negative", error_message="Revenue cannot be negative")
                ]
            )
            
            # Configure mock registry to return our test variable
            self.mock_var_registry.get_variable_definition.return_value = self.test_var_def
            
            # Get the VarInputData instance
            self.var_data = get_var_input_data()
    
    def test_singleton_pattern(self):
        """Test that VarInputData follows singleton pattern"""
        instance1 = get_var_input_data()
        instance2 = get_var_input_data()
        
        assert instance1 is instance2
        assert VarInputData() is instance1
    
    def test_set_and_get_variable(self):
        """Test basic variable storage and retrieval"""
        # Set a variable
        success = self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        assert success is True
        
        # Get the variable back
        value = self.var_data.get_variable("AAPL", "revenue", "2023")
        assert value == 394328
    
    def test_get_variable_with_metadata(self):
        """Test getting variable with metadata"""
        # Set a variable
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        
        # Get with metadata
        value, metadata = self.var_data.get_variable("AAPL", "revenue", "2023", include_metadata=True)
        
        assert value == 394328
        assert metadata.source == "excel"
        assert metadata.period == "2023"
        assert isinstance(metadata.timestamp, datetime)
    
    def test_get_variable_latest_period(self):
        """Test getting latest period when period='latest'"""
        # Set multiple periods
        self.var_data.set_variable("AAPL", "revenue", 365817, "2022", "excel")
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        
        # Get latest should return 2023 (most recent)
        latest_value = self.var_data.get_variable("AAPL", "revenue", "latest")
        assert latest_value == 394328
    
    def test_get_nonexistent_variable(self):
        """Test getting a variable that doesn't exist"""
        value = self.var_data.get_variable("AAPL", "nonexistent", "2023")
        assert value is None
    
    def test_unknown_variable_registration(self):
        """Test setting unknown variable (not in registry)"""
        # Configure mock to return None for unknown variable
        self.mock_var_registry.get_variable_definition.return_value = None
        
        success = self.var_data.set_variable("AAPL", "unknown_var", 100, "2023")
        assert success is False
    
    def test_validation_failure(self):
        """Test setting variable with validation failure"""
        # Create a variable that should fail validation
        invalid_var_def = VariableDefinition(
            name="test_var",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.CURRENCY,
            validation_rules=[
                ValidationRule("positive", error_message="Must be positive")
            ]
        )
        
        # Mock validation to fail
        invalid_var_def.validate_value = Mock(return_value=(False, ["Must be positive"]))
        self.mock_var_registry.get_variable_definition.return_value = invalid_var_def
        
        # Should still set the variable but with validation_passed=False
        success = self.var_data.set_variable("AAPL", "test_var", -100, "2023")
        assert success is True  # Still sets the value
        
        # Check metadata shows validation failed
        value, metadata = self.var_data.get_variable("AAPL", "test_var", "2023", include_metadata=True)
        assert value == -100
        assert metadata.validation_passed is False
    
    def test_historical_data(self):
        """Test historical data functionality"""
        # Set historical data for multiple years
        years_data = [
            ("2019", 260174),
            ("2020", 274515), 
            ("2021", 365817),
            ("2022", 394328),
            ("2023", 383285)
        ]
        
        for year, revenue in years_data:
            self.var_data.set_variable("AAPL", "revenue", revenue, year, "excel")
        
        # Get historical data
        historical = self.var_data.get_historical_data("AAPL", "revenue", years=5)
        
        assert len(historical) == 5
        # Should be sorted by most recent first
        assert historical[0][0] == "2023"
        assert historical[0][1] == 383285
        assert historical[-1][0] == "2019" 
        assert historical[-1][1] == 260174
    
    def test_historical_data_with_metadata(self):
        """Test historical data with metadata"""
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        
        historical = self.var_data.get_historical_data("AAPL", "revenue", include_metadata=True)
        
        assert len(historical) == 1
        period, value, metadata = historical[0]
        assert period == "2023"
        assert value == 394328
        assert metadata.source == "excel"
    
    def test_clear_cache_all(self):
        """Test clearing all cached data"""
        # Set some data
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("MSFT", "revenue", 211915, "2023")
        
        # Verify data exists
        assert self.var_data.get_variable("AAPL", "revenue", "2023") == 394328
        assert self.var_data.get_variable("MSFT", "revenue", "2023") == 211915
        
        # Clear all cache
        self.var_data.clear_cache()
        
        # Verify data is gone
        assert self.var_data.get_variable("AAPL", "revenue", "2023") is None
        assert self.var_data.get_variable("MSFT", "revenue", "2023") is None
    
    def test_clear_cache_specific_symbol(self):
        """Test clearing cache for specific symbol"""
        # Set data for two symbols
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("MSFT", "revenue", 211915, "2023")
        
        # Clear cache for AAPL only
        self.var_data.clear_cache(symbol="AAPL")
        
        # AAPL data should be gone, MSFT should remain
        assert self.var_data.get_variable("AAPL", "revenue", "2023") is None
        assert self.var_data.get_variable("MSFT", "revenue", "2023") == 211915
    
    def test_clear_cache_specific_variable(self):
        """Test clearing cache for specific variable"""
        # Set multiple variables for same symbol
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("AAPL", "net_income", 99803, "2023")
        
        # Clear only revenue
        self.var_data.clear_cache(symbol="AAPL", variable_name="revenue")
        
        # Revenue should be gone, net_income should remain
        assert self.var_data.get_variable("AAPL", "revenue", "2023") is None
        assert self.var_data.get_variable("AAPL", "net_income", "2023") == 99803
    
    def test_bulk_update(self):
        """Test bulk updating multiple variables"""
        # Mock registry to accept all variables
        def mock_get_variable_def(name):
            return VariableDefinition(
                name=name,
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.CURRENCY
            )
        
        self.mock_var_registry.get_variable_definition.side_effect = mock_get_variable_def
        
        bulk_data = {
            "AAPL": {
                "revenue": {"2023": 394328, "2022": 365817},
                "net_income": {"2023": 99803, "2022": 94680}
            },
            "MSFT": {
                "revenue": {"2023": 211915, "2022": 198270}
            }
        }
        
        results = self.var_data.bulk_update(bulk_data, source="bulk_test")
        
        assert results['successful'] == 6  # 6 data points: AAPL revenue(2), net_income(2), MSFT revenue(2)
        assert results['failed'] == 0
        
        # Verify data was stored
        assert self.var_data.get_variable("AAPL", "revenue", "2023") == 394328
        assert self.var_data.get_variable("AAPL", "net_income", "2022") == 94680
        assert self.var_data.get_variable("MSFT", "revenue", "2023") == 211915
    
    def test_available_symbols(self):
        """Test getting available symbols"""
        # Initially should be empty
        assert self.var_data.get_available_symbols() == []
        
        # Add some data
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("MSFT", "revenue", 211915, "2023")
        
        symbols = self.var_data.get_available_symbols()
        assert set(symbols) == {"AAPL", "MSFT"}
        assert symbols == sorted(symbols)  # Should be sorted
    
    def test_available_variables(self):
        """Test getting available variables"""
        # Add data for testing
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("AAPL", "net_income", 99803, "2023")
        self.var_data.set_variable("MSFT", "revenue", 211915, "2023")
        
        # Get variables for specific symbol
        aapl_vars = self.var_data.get_available_variables("AAPL")
        assert set(aapl_vars) == {"revenue", "net_income"}
        
        # Get all variables across all symbols
        all_vars = self.var_data.get_available_variables()
        assert set(all_vars) == {"revenue", "net_income"}
    
    def test_available_periods(self):
        """Test getting available periods for a variable"""
        # Add data for multiple periods
        self.var_data.set_variable("AAPL", "revenue", 260174, "2019")
        self.var_data.set_variable("AAPL", "revenue", 274515, "2020")
        self.var_data.set_variable("AAPL", "revenue", 365817, "2021")
        
        periods = self.var_data.get_available_periods("AAPL", "revenue")
        
        # Should be sorted by most recent first
        assert periods == ["2021", "2020", "2019"]
    
    def test_has_variable(self):
        """Test checking if a variable exists"""
        # Initially should not exist
        assert self.var_data.has_variable("AAPL", "revenue", "2023") is False
        
        # Set the variable
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        
        # Now should exist
        assert self.var_data.has_variable("AAPL", "revenue", "2023") is True
        assert self.var_data.has_variable("AAPL", "revenue", "latest") is True
        assert self.var_data.has_variable("AAPL", "revenue", "2022") is False
    
    def test_update_metadata(self):
        """Test updating metadata for existing variable"""
        # Set initial variable
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        
        # Update metadata
        success = self.var_data.update_metadata(
            "AAPL", "revenue", "2023",
            {"quality_score": 0.95, "calculation_method": "Updated method"}
        )
        
        assert success is True
        
        # Verify metadata was updated
        value, metadata = self.var_data.get_variable("AAPL", "revenue", "2023", include_metadata=True)
        assert metadata.quality_score == 0.95
        assert metadata.calculation_method == "Updated method"
    
    def test_export_data(self):
        """Test exporting data"""
        # Set some test data
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023", "excel")
        self.var_data.set_variable("AAPL", "net_income", 99803, "2023", "excel")
        
        # Export as dictionary
        export_dict = self.var_data.export_data(format="dict", include_metadata=False)
        
        assert "AAPL" in export_dict
        assert "revenue" in export_dict["AAPL"]
        assert export_dict["AAPL"]["revenue"]["2023"] == 394328
        assert export_dict["AAPL"]["net_income"]["2023"] == 99803
        
        # Export with metadata
        export_with_metadata = self.var_data.export_data(format="dict", include_metadata=True)
        assert "value" in export_with_metadata["AAPL"]["revenue"]["2023"]
        assert "metadata" in export_with_metadata["AAPL"]["revenue"]["2023"]
    
    def test_statistics(self):
        """Test getting system statistics"""
        # Mock registry to return variable definition
        self.mock_var_registry.list_all_variables.return_value = ["revenue"]
        
        # Add some test data
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        self.var_data.set_variable("AAPL", "revenue", 365817, "2022") 
        self.var_data.set_variable("MSFT", "revenue", 211915, "2023")
        
        stats = self.var_data.get_statistics()
        
        assert stats['data_storage']['symbols'] == 2
        assert stats['data_storage']['total_data_points'] == 3
        assert 'performance' in stats
        assert 'cache_hit_rate' in stats
        assert 'system_info' in stats
    
    def test_period_parsing_for_sorting(self):
        """Test period string parsing for sorting"""
        # Mock registry to accept TEST symbol
        def mock_get_variable_def(name):
            return VariableDefinition(
                name=name,
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.CURRENCY
            )
        
        self.mock_var_registry.get_variable_definition.side_effect = mock_get_variable_def
        
        # Test various period formats
        test_periods = ["2023", "2022", "Q1-2023", "Q4-2022", "latest"]
        
        # Set data with different periods
        for i, period in enumerate(test_periods):
            self.var_data.set_variable("TEST", "revenue", i * 1000, period)
        
        periods = self.var_data.get_available_periods("TEST", "revenue")
        
        # latest should be first, then periods sorted by year
        assert periods[0] == "latest"
        # Check that we have all periods (order may vary based on parsing logic)
        expected_periods = {"latest", "2023", "2022", "Q1-2023", "Q4-2022"}
        assert set(periods) == expected_periods


class TestThreadSafety:
    """Test thread safety of VarInputData operations"""
    
    def setup_method(self):
        """Set up for thread safety tests"""
        VarInputData._instance = None
        
        with patch('core.data_processing.var_input_data.get_registry') as mock_registry, \
             patch('core.data_processing.var_input_data.UniversalDataRegistry'):
            
            mock_var_registry = Mock()
            mock_registry.return_value = mock_var_registry
            
            test_var_def = VariableDefinition(
                name="test_var",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.CURRENCY
            )
            mock_var_registry.get_variable_definition.return_value = test_var_def
            
            self.var_data = get_var_input_data()
            self.thread_results = []
            self.thread_errors = []
    
    def test_concurrent_writes(self):
        """Test concurrent write operations"""
        def write_worker(worker_id):
            try:
                for i in range(10):
                    success = self.var_data.set_variable(
                        "TEST", "test_var", worker_id * 100 + i, f"period_{i}", f"worker_{worker_id}"
                    )
                    self.thread_results.append((worker_id, i, success))
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                self.thread_errors.append(f"Worker {worker_id}: {e}")
        
        # Start multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=write_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(self.thread_errors) == 0
        assert len(self.thread_results) == 50  # 5 workers * 10 operations each
        
        # Verify all operations succeeded
        assert all(result[2] for result in self.thread_results)
    
    def test_concurrent_reads_and_writes(self):
        """Test concurrent read and write operations"""
        # Pre-populate some data
        for i in range(10):
            self.var_data.set_variable("TEST", "test_var", i * 100, f"period_{i}")
        
        def read_worker():
            try:
                for i in range(20):
                    value = self.var_data.get_variable("TEST", "test_var", f"period_{i % 10}")
                    self.thread_results.append(('read', i, value))
                    time.sleep(0.001)
            except Exception as e:
                self.thread_errors.append(f"Reader: {e}")
        
        def write_worker():
            try:
                for i in range(20):
                    success = self.var_data.set_variable("TEST", "test_var", i + 1000, f"new_period_{i}")
                    self.thread_results.append(('write', i, success))
                    time.sleep(0.001)
            except Exception as e:
                self.thread_errors.append(f"Writer: {e}")
        
        # Start reader and writer threads
        reader_thread = threading.Thread(target=read_worker)
        writer_thread = threading.Thread(target=write_worker)
        
        reader_thread.start()
        writer_thread.start()
        
        reader_thread.join()
        writer_thread.join()
        
        # Verify no errors occurred
        assert len(self.thread_errors) == 0
        assert len(self.thread_results) == 40  # 20 reads + 20 writes


class TestConvenienceFunctions:
    """Test the module-level convenience functions"""
    
    def setup_method(self):
        """Set up for convenience function tests"""
        VarInputData._instance = None
        
        # Create patches that persist for the whole test
        self.registry_patcher = patch('core.data_processing.var_input_data.get_registry')
        self.data_registry_patcher = patch('core.data_processing.var_input_data.UniversalDataRegistry')
        
        mock_registry = self.registry_patcher.start()
        mock_data_registry_class = self.data_registry_patcher.start()
        
        mock_var_registry = Mock()
        mock_registry.return_value = mock_var_registry
        
        # Mock the Universal Data Registry to return None (no data found)
        mock_data_registry_instance = Mock()
        mock_data_registry_instance.get_data.return_value = None
        mock_data_registry_class.return_value = mock_data_registry_instance
        
        test_var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.CURRENCY
        )
        mock_var_registry.get_variable_definition.return_value = test_var_def
    
    def teardown_method(self):
        """Clean up patches"""
        self.registry_patcher.stop()
        self.data_registry_patcher.stop()
    
    def test_convenience_get_variable(self):
        """Test module-level get_variable function"""
        # Use convenience function to set and get
        assert set_variable("AAPL", "revenue", 394328, "2023") is True
        assert get_variable("AAPL", "revenue", "2023") == 394328
    
    def test_convenience_get_historical_data(self):
        """Test module-level get_historical_data function"""
        # Set some historical data
        set_variable("AAPL", "revenue", 365817, "2022")
        set_variable("AAPL", "revenue", 394328, "2023")
        
        historical = get_historical_data("AAPL", "revenue", years=2)
        
        assert len(historical) == 2
        assert historical[0][0] == "2023"
        assert historical[0][1] == 394328
    
    def test_convenience_clear_cache(self):
        """Test module-level clear_cache function"""
        # Set some data
        set_variable("AAPL", "revenue", 394328, "2023")
        assert get_variable("AAPL", "revenue", "2023") == 394328
        
        # Clear using convenience function
        clear_cache()
        
        # Data should be gone
        assert get_variable("AAPL", "revenue", "2023") is None


class TestEventSystem:
    """Test the event system integration"""
    
    def setup_method(self):
        """Set up for event system tests"""
        VarInputData._instance = None
        
        with patch('core.data_processing.var_input_data.get_registry') as mock_registry, \
             patch('core.data_processing.var_input_data.UniversalDataRegistry'):
            
            mock_var_registry = Mock()
            mock_registry.return_value = mock_var_registry
            
            test_var_def = VariableDefinition(
                name="revenue",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.CURRENCY
            )
            mock_var_registry.get_variable_definition.return_value = test_var_def
            
            self.var_data = get_var_input_data()
            self.events_received = []
    
    def test_variable_set_event(self):
        """Test that setting a variable emits an event"""
        def event_callback(**kwargs):
            self.events_received.append(kwargs)
        
        # Subscribe to variable set events
        self.var_data.subscribe_to_events(DataChangeEvent.VARIABLE_SET, event_callback)
        
        # Set a variable
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        
        # Verify event was emitted
        assert len(self.events_received) == 1
        event = self.events_received[0]
        assert event['event_type'] == DataChangeEvent.VARIABLE_SET
        assert event['symbol'] == "AAPL"
        assert event['variable_name'] == "revenue"
        assert event['value'] == 394328
    
    def test_variable_update_event(self):
        """Test that updating a variable emits an update event"""
        def event_callback(**kwargs):
            self.events_received.append(kwargs)
        
        # Set initial value
        self.var_data.set_variable("AAPL", "revenue", 394328, "2023")
        
        # Subscribe to update events
        self.var_data.subscribe_to_events(DataChangeEvent.VARIABLE_UPDATED, event_callback)
        
        # Update the same variable
        self.var_data.set_variable("AAPL", "revenue", 400000, "2023")
        
        # Verify update event was emitted
        assert len(self.events_received) == 1
        event = self.events_received[0]
        assert event['event_type'] == DataChangeEvent.VARIABLE_UPDATED
        assert event['value'] == 400000
    
    def test_bulk_update_event(self):
        """Test that bulk updates emit a single bulk event"""
        def event_callback(**kwargs):
            self.events_received.append(kwargs)
        
        # Subscribe to bulk update events
        self.var_data.subscribe_to_events(DataChangeEvent.BULK_UPDATE, event_callback)
        
        # Perform bulk update
        bulk_data = {
            "AAPL": {"revenue": {"2023": 394328}},
            "MSFT": {"revenue": {"2023": 211915}}
        }
        
        self.var_data.bulk_update(bulk_data)
        
        # Should receive one bulk update event, not individual events
        assert len(self.events_received) == 1
        event = self.events_received[0]
        assert event['event_type'] == DataChangeEvent.BULK_UPDATE
        assert event['data_count'] == 2


# Integration tests with actual registry system
class TestVarInputDataIntegration:
    """Integration tests with real Financial Variable Registry"""
    
    def setup_method(self):
        """Set up with real registry"""
        VarInputData._instance = None
        
        # Register a real test variable
        registry = get_registry()
        test_var = VariableDefinition(
            name="test_revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.CURRENCY,
            units=Units.MILLIONS_USD,
            validation_rules=[
                ValidationRule("non_negative", error_message="Revenue cannot be negative")
            ]
        )
        registry.register_variable(test_var)
        
        with patch('core.data_processing.var_input_data.UniversalDataRegistry'):
            self.var_data = get_var_input_data()
    
    def test_real_validation(self):
        """Test with real validation from registry"""
        # Valid value should work
        success = self.var_data.set_variable("AAPL", "test_revenue", 394328, "2023")
        assert success is True
        
        # Invalid negative value should still be stored but marked as invalid
        success = self.var_data.set_variable("AAPL", "test_revenue", -1000, "2022")
        assert success is True
        
        # Check metadata shows validation failure
        value, metadata = self.var_data.get_variable("AAPL", "test_revenue", "2022", include_metadata=True)
        assert value == -1000
        assert metadata.validation_passed is False


if __name__ == "__main__":
    pytest.main([__file__])