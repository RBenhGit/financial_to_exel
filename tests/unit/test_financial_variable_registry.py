"""
Unit Tests for Financial Variable Registry
==========================================

Comprehensive test suite for the FinancialVariableRegistry core class,
covering all functionality specified in Task #57:

1. Variable registration and retrieval
2. Category-based organization  
3. Source alias resolution
4. Data validation
5. Thread safety
6. JSON/YAML serialization

Test Categories:
- Basic functionality tests
- Thread safety tests
- Validation rule tests  
- Serialization tests
- Error handling tests
"""

import json
import threading
import time
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from core.data_processing.financial_variable_registry import (
    FinancialVariableRegistry,
    VariableDefinition, 
    VariableCategory,
    DataType,
    Units,
    ValidationRule,
    get_registry
)


class TestVariableDefinition:
    """Test VariableDefinition dataclass functionality"""
    
    def test_variable_definition_creation(self):
        """Test basic variable definition creation"""
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            units=Units.MILLIONS_USD,
            description="Total company revenue"
        )
        
        assert var_def.name == "revenue"
        assert var_def.category == VariableCategory.INCOME_STATEMENT
        assert var_def.data_type == DataType.FLOAT
        assert var_def.units == Units.MILLIONS_USD
        assert var_def.description == "Total company revenue"
        assert isinstance(var_def.created_at, datetime)
        assert var_def.updated_at is None
    
    def test_variable_name_normalization(self):
        """Test that variable names are normalized to snake_case"""
        var_def = VariableDefinition(
            name="Total Revenue-2023",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT
        )
        
        assert var_def.name == "total_revenue_2023"
    
    def test_add_alias(self):
        """Test adding aliases for different data sources"""
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT
        )
        
        var_def.add_alias("yfinance", "totalRevenue")
        var_def.add_alias("excel", "Revenue")
        
        assert var_def.aliases["yfinance"] == "totalRevenue"
        assert var_def.aliases["excel"] == "Revenue"
        assert var_def.updated_at is not None
    
    def test_validation_rules(self):
        """Test validation rule functionality"""
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            validation_rules=[
                ValidationRule("positive", error_message="Revenue must be positive"),
                ValidationRule("range", parameters={"min": 0, "max": 1000000}, warning_only=True)
            ]
        )
        
        # Test positive validation
        is_valid, errors = var_def.validate_value(100000)
        assert is_valid
        assert len(errors) == 0
        
        # Test negative value (should fail)
        is_valid, errors = var_def.validate_value(-1000)
        assert not is_valid
        assert "Revenue must be positive" in errors
        
        # Test None value (should pass for non-required)
        is_valid, errors = var_def.validate_value(None)
        assert is_valid
    
    def test_to_dict_serialization(self):
        """Test conversion to dictionary for serialization"""
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            units=Units.MILLIONS_USD,
            description="Test revenue",
            tags={"core", "income"}
        )
        
        data = var_def.to_dict()
        
        assert data["name"] == "revenue"
        assert data["category"] == "income_statement"
        assert data["data_type"] == "float"
        assert data["units"] == "millions_usd"
        assert isinstance(data["tags"], list)
        assert "core" in data["tags"]


class TestValidationRule:
    """Test ValidationRule functionality"""
    
    def test_positive_rule(self):
        """Test positive value validation rule"""
        rule = ValidationRule("positive", error_message="Must be positive")
        
        is_valid, message = rule.validate(100)
        assert is_valid
        assert message == ""
        
        is_valid, message = rule.validate(-10)
        assert not is_valid
        assert message == "Must be positive"
        
        is_valid, message = rule.validate(None)
        assert is_valid  # None allowed unless specifically checking not_null
    
    def test_range_rule(self):
        """Test range validation rule"""
        rule = ValidationRule(
            "range", 
            parameters={"min": 0, "max": 100},
            error_message="Value out of range"
        )
        
        is_valid, message = rule.validate(50)
        assert is_valid
        
        is_valid, message = rule.validate(150)
        assert not is_valid
        assert "Value out of range" in message
    
    def test_percentage_range_rule(self):
        """Test percentage range validation"""
        rule = ValidationRule(
            "percentage_range",
            parameters={"min": 0.0, "max": 1.0}
        )
        
        is_valid, message = rule.validate(0.5)  # 50%
        assert is_valid
        
        is_valid, message = rule.validate(1.5)  # 150% - invalid
        assert not is_valid


class TestFinancialVariableRegistry:
    """Test FinancialVariableRegistry functionality"""
    
    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry instance for testing"""
        # Clear the singleton instance to ensure clean tests
        if hasattr(FinancialVariableRegistry, '_instance'):
            FinancialVariableRegistry._instance = None
        return FinancialVariableRegistry()
    
    def test_singleton_pattern(self):
        """Test that FinancialVariableRegistry follows singleton pattern"""
        registry1 = FinancialVariableRegistry()
        registry2 = FinancialVariableRegistry()
        registry3 = get_registry()
        
        assert registry1 is registry2
        assert registry1 is registry3
    
    def test_register_variable(self, fresh_registry):
        """Test variable registration"""
        registry = fresh_registry
        
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            description="Total revenue"
        )
        
        result = registry.register_variable(var_def)
        assert result is True
        
        # Test duplicate registration
        result = registry.register_variable(var_def)
        assert result is False
    
    def test_get_variable_definition(self, fresh_registry):
        """Test variable retrieval"""
        registry = fresh_registry
        
        var_def = VariableDefinition(
            name="net_income",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT
        )
        
        registry.register_variable(var_def)
        
        retrieved = registry.get_variable_definition("net_income")
        assert retrieved is not None
        assert retrieved.name == "net_income"
        assert retrieved.category == VariableCategory.INCOME_STATEMENT
        
        # Test non-existent variable
        not_found = registry.get_variable_definition("nonexistent")
        assert not_found is None
    
    def test_category_filtering(self, fresh_registry):
        """Test filtering variables by category"""
        registry = fresh_registry
        
        # Register variables in different categories
        income_var = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT
        )
        
        balance_var = VariableDefinition(
            name="total_assets",
            category=VariableCategory.BALANCE_SHEET,
            data_type=DataType.FLOAT
        )
        
        market_var = VariableDefinition(
            name="stock_price",
            category=VariableCategory.MARKET_DATA,
            data_type=DataType.FLOAT
        )
        
        registry.register_variable(income_var)
        registry.register_variable(balance_var)
        registry.register_variable(market_var)
        
        # Test category filtering
        income_vars = registry.get_variables_by_category(VariableCategory.INCOME_STATEMENT)
        assert len(income_vars) == 1
        assert income_vars[0].name == "revenue"
        
        balance_vars = registry.get_variables_by_category(VariableCategory.BALANCE_SHEET)
        assert len(balance_vars) == 1
        assert balance_vars[0].name == "total_assets"
        
        # Test empty category
        cash_vars = registry.get_variables_by_category(VariableCategory.CASH_FLOW)
        assert len(cash_vars) == 0
    
    def test_alias_resolution(self, fresh_registry):
        """Test source alias resolution"""
        registry = fresh_registry
        
        var_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            aliases={
                "yfinance": "totalRevenue",
                "excel": "Revenue",
                "fmp": "revenue"
            }
        )
        
        registry.register_variable(var_def)
        
        # Test alias resolution
        assert registry.resolve_alias("yfinance", "totalRevenue") == "revenue"
        assert registry.resolve_alias("excel", "Revenue") == "revenue"
        assert registry.resolve_alias("fmp", "revenue") == "revenue"
        
        # Test non-existent alias
        assert registry.resolve_alias("yfinance", "nonexistent") is None
        assert registry.resolve_alias("unknown_source", "anything") is None
    
    def test_get_aliases_for_source(self, fresh_registry):
        """Test retrieving all aliases for a specific source"""
        registry = fresh_registry
        
        # Register multiple variables with yfinance aliases
        var1 = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            aliases={"yfinance": "totalRevenue"}
        )
        
        var2 = VariableDefinition(
            name="net_income",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            aliases={"yfinance": "netIncome"}
        )
        
        registry.register_variable(var1)
        registry.register_variable(var2)
        
        yfinance_aliases = registry.get_aliases_for_source("yfinance")
        assert len(yfinance_aliases) == 2
        assert yfinance_aliases["totalRevenue"] == "revenue"
        assert yfinance_aliases["netIncome"] == "net_income"
    
    def test_tag_filtering(self, fresh_registry):
        """Test filtering variables by tags"""
        registry = fresh_registry
        
        var1 = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            tags={"core", "income"}
        )
        
        var2 = VariableDefinition(
            name="ebitda",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            tags={"calculated", "income"}
        )
        
        var3 = VariableDefinition(
            name="market_cap",
            category=VariableCategory.MARKET_DATA,
            data_type=DataType.FLOAT,
            tags={"core", "market"}
        )
        
        registry.register_variable(var1)
        registry.register_variable(var2)
        registry.register_variable(var3)
        
        # Test tag filtering
        core_vars = registry.get_variables_by_tag("core")
        assert len(core_vars) == 2
        
        income_vars = registry.get_variables_by_tag("income")
        assert len(income_vars) == 2
        
        # Test non-existent tag
        nonexistent_vars = registry.get_variables_by_tag("nonexistent")
        assert len(nonexistent_vars) == 0
    
    def test_validation(self, fresh_registry):
        """Test value validation through registry"""
        registry = fresh_registry
        
        var_def = VariableDefinition(
            name="profit_margin",
            category=VariableCategory.RATIOS,
            data_type=DataType.PERCENTAGE,
            validation_rules=[
                ValidationRule("range", parameters={"min": -1.0, "max": 1.0})
            ]
        )
        
        registry.register_variable(var_def)
        
        # Test valid value
        is_valid, errors = registry.validate_value("profit_margin", 0.15)
        assert is_valid
        assert len(errors) == 0
        
        # Test invalid value
        is_valid, errors = registry.validate_value("profit_margin", 2.0)
        assert not is_valid
        assert len(errors) > 0
        
        # Test non-existent variable
        is_valid, errors = registry.validate_value("nonexistent", 0.5)
        assert not is_valid
        assert "not found in registry" in errors[0]
    
    def test_statistics(self, fresh_registry):
        """Test registry statistics"""
        registry = fresh_registry
        
        # Add some variables
        vars_to_add = [
            VariableDefinition("revenue", VariableCategory.INCOME_STATEMENT, DataType.FLOAT),
            VariableDefinition("assets", VariableCategory.BALANCE_SHEET, DataType.FLOAT),
            VariableDefinition("price", VariableCategory.MARKET_DATA, DataType.FLOAT, 
                             aliases={"yfinance": "regularMarketPrice"})
        ]
        
        for var_def in vars_to_add:
            registry.register_variable(var_def)
        
        stats = registry.get_statistics()
        
        assert stats["total_variables"] == 3
        assert stats["categories"]["income_statement"] == 1
        assert stats["categories"]["balance_sheet"] == 1
        assert stats["categories"]["market_data"] == 1
        assert "yfinance" in stats["sources_with_aliases"]
        assert stats["total_aliases"] == 1


class TestThreadSafety:
    """Test thread safety of FinancialVariableRegistry"""
    
    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry instance for testing"""
        if hasattr(FinancialVariableRegistry, '_instance'):
            FinancialVariableRegistry._instance = None
        return FinancialVariableRegistry()
    
    def test_concurrent_registration(self, fresh_registry):
        """Test concurrent variable registration from multiple threads"""
        registry = fresh_registry
        results = []
        num_threads = 10
        
        def register_variable(thread_id):
            var_def = VariableDefinition(
                name=f"variable_{thread_id}",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.FLOAT
            )
            result = registry.register_variable(var_def)
            results.append((thread_id, result))
            return result
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(register_variable, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # All registrations should succeed
        assert len(results) == num_threads
        assert all(result[1] for result in results)
        
        # Verify all variables were registered
        assert len(registry.list_all_variables()) == num_threads
    
    def test_concurrent_read_operations(self, fresh_registry):
        """Test concurrent read operations"""
        registry = fresh_registry
        
        # Pre-populate registry
        for i in range(5):
            var_def = VariableDefinition(
                name=f"test_var_{i}",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.FLOAT,
                aliases={"source1": f"alias_{i}"}
            )
            registry.register_variable(var_def)
        
        read_results = []
        num_threads = 20
        
        def perform_reads(thread_id):
            # Perform various read operations
            vars_list = registry.list_all_variables()
            category_vars = registry.get_variables_by_category(VariableCategory.INCOME_STATEMENT)
            alias_result = registry.resolve_alias("source1", "alias_1")
            stats = registry.get_statistics()
            
            read_results.append({
                "thread_id": thread_id,
                "vars_count": len(vars_list),
                "category_count": len(category_vars),
                "alias_found": alias_result is not None,
                "stats_total": stats["total_variables"]
            })
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(perform_reads, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                future.result()
        
        # All reads should return consistent results
        assert len(read_results) == num_threads
        assert all(r["vars_count"] == 5 for r in read_results)
        assert all(r["category_count"] == 5 for r in read_results)
        assert all(r["alias_found"] for r in read_results)
        assert all(r["stats_total"] == 5 for r in read_results)


class TestSerialization:
    """Test JSON/YAML serialization functionality"""
    
    @pytest.fixture
    def populated_registry(self):
        """Create registry populated with test data"""
        if hasattr(FinancialVariableRegistry, '_instance'):
            FinancialVariableRegistry._instance = None
        registry = FinancialVariableRegistry()
        
        # Add test variables
        test_vars = [
            VariableDefinition(
                name="revenue",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.FLOAT,
                units=Units.MILLIONS_USD,
                description="Total revenue",
                aliases={"yfinance": "totalRevenue", "excel": "Revenue"},
                validation_rules=[ValidationRule("positive")]
            ),
            VariableDefinition(
                name="book_value",
                category=VariableCategory.BALANCE_SHEET,
                data_type=DataType.FLOAT,
                units=Units.DOLLARS,
                description="Book value per share",
                tags={"per_share", "valuation"}
            )
        ]
        
        for var_def in test_vars:
            registry.register_variable(var_def)
        
        return registry
    
    def test_json_export(self, populated_registry):
        """Test JSON export functionality"""
        registry = populated_registry
        
        json_str = registry.export_to_json()
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        
        assert "schema_version" in data
        assert "exported_at" in data
        assert "variables" in data
        assert len(data["variables"]) == 2
        
        # Verify variable data structure
        revenue_data = data["variables"]["revenue"]
        assert revenue_data["name"] == "revenue"
        assert revenue_data["category"] == "income_statement"
        assert revenue_data["data_type"] == "float"
        assert "totalRevenue" in revenue_data["aliases"]["yfinance"]
    
    def test_json_export_to_file(self, populated_registry):
        """Test JSON export to file"""
        registry = populated_registry
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            registry.export_to_json(temp_path)
            
            # Verify file was created and contains valid JSON
            assert temp_path.exists()
            data = json.loads(temp_path.read_text())
            assert len(data["variables"]) == 2
            
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_yaml_export(self, populated_registry):
        """Test YAML export functionality"""
        registry = populated_registry
        
        yaml_str = registry.export_to_yaml()
        
        # Verify it contains expected YAML content
        assert "schema_version:" in yaml_str
        assert "variables:" in yaml_str
        assert "revenue:" in yaml_str
        assert "book_value:" in yaml_str
    
    def test_json_import(self, populated_registry):
        """Test importing variables from JSON"""
        registry = populated_registry
        
        # Export current state
        json_str = registry.export_to_json()
        
        # Clear registry
        registry.clear_registry()
        assert len(registry.list_all_variables()) == 0
        
        # Import from JSON
        imported_count = registry.import_from_json(json_str)
        
        assert imported_count == 2
        assert len(registry.list_all_variables()) == 2
        
        # Verify data integrity
        revenue_var = registry.get_variable_definition("revenue")
        assert revenue_var is not None
        assert revenue_var.category == VariableCategory.INCOME_STATEMENT
        assert revenue_var.aliases["yfinance"] == "totalRevenue"
    
    def test_json_import_from_file(self, populated_registry):
        """Test importing from JSON file"""
        registry = populated_registry
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Export to file
            registry.export_to_json(temp_path)
            
            # Clear and import
            registry.clear_registry()
            imported_count = registry.import_from_json(temp_path)
            
            assert imported_count == 2
            assert len(registry.list_all_variables()) == 2
            
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def fresh_registry(self):
        if hasattr(FinancialVariableRegistry, '_instance'):
            FinancialVariableRegistry._instance = None
        return FinancialVariableRegistry()
    
    def test_invalid_variable_name(self):
        """Test handling of invalid variable names"""
        with pytest.raises(ValueError, match="Variable name is required"):
            VariableDefinition(
                name="",
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.FLOAT
            )
        
        with pytest.raises(ValueError, match="Variable name is required"):
            VariableDefinition(
                name=None,
                category=VariableCategory.INCOME_STATEMENT,
                data_type=DataType.FLOAT
            )
    
    def test_malformed_json_import(self, fresh_registry):
        """Test handling of malformed JSON during import"""
        registry = fresh_registry
        
        # Test invalid JSON
        with pytest.raises(json.JSONDecodeError):
            registry.import_from_json("invalid json")
        
        # Test JSON without variables key
        valid_json_no_vars = '{"schema_version": "1.0.0"}'
        imported_count = registry.import_from_json(valid_json_no_vars)
        assert imported_count == 0
    
    def test_validation_rule_edge_cases(self):
        """Test edge cases in validation rules"""
        rule = ValidationRule("unknown_rule_type")
        
        # Unknown rule types should pass validation
        is_valid, message = rule.validate("any_value")
        assert is_valid
        assert message == ""
    
    def test_registry_clear(self, fresh_registry):
        """Test registry clearing functionality"""
        registry = fresh_registry
        
        # Add some variables
        var_def = VariableDefinition(
            name="test_var",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT
        )
        registry.register_variable(var_def)
        
        assert len(registry.list_all_variables()) == 1
        
        # Clear registry
        registry.clear_registry()
        
        assert len(registry.list_all_variables()) == 0
        stats = registry.get_statistics()
        assert stats["total_variables"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])