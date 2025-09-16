# Unified Data System - User Guide

## Overview

The Unified Data System is a comprehensive financial analysis platform that integrates multiple data sources (Excel files, APIs) through a centralized variable registry for consistent DCF, DDM, and P/B analysis.

## Quick Start

### Basic Usage

```python
# Import the unified data system
from core.data_processing.var_input_data import VarInputData
from core.data_processing.financial_variable_registry import FinancialVariableRegistry
from core.analysis.engines.financial_calculations import FinancialCalculator

# Initialize the system
data_system = VarInputData()
registry = FinancialVariableRegistry()
calculator = FinancialCalculator()

# Load data for a company
ticker = "MSFT"
calculator.load_company_data(ticker)

# Perform analysis
dcf_results = calculator.calculate_dcf()
pb_analysis = calculator.calculate_pb_analysis()
```

### Streamlit Interface

Launch the web interface:
```bash
python run_streamlit_app.py
```

The interface provides:
- **Company Selection**: Choose from available Excel data or enter ticker
- **Analysis Options**: DCF, DDM, P/B analysis with customizable parameters
- **Visualization**: Interactive charts and detailed breakdowns
- **Export**: CSV export of results and calculations

## Data Sources

### Excel Data Structure

Place company financial data in:
```
data/companies/{TICKER}/
├── FY/                          # Fiscal Year data
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx
│   └── Cash Flow Statement.xlsx
└── LTM/                         # Last Twelve Months data
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx
```

### API Data Sources

The system automatically integrates:
- **yfinance**: Stock prices, market data
- **Alpha Vantage**: Financial statements (with API key)
- **FMP**: Financial Modeling Prep data (with API key)
- **Polygon**: Market data (with API key)

Configure API keys in `.env`:
```
ALPHA_VANTAGE_API_KEY=your_key_here
FMP_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

## Core Features

### 1. Financial Variable Registry

Centralized registry for all financial variables with:
- **Standardized Names**: Consistent variable naming across sources
- **Data Type Validation**: Automatic type checking and conversion
- **Source Mapping**: Maps Excel column names to standard variables
- **Unit Conversion**: Handles different unit scales (thousands, millions)

### 2. Multi-Source Data Integration

- **Excel Priority**: Primary data from Excel files when available
- **API Fallback**: Automatic fallback to API data for missing information
- **Data Caching**: Intelligent caching to reduce API calls
- **Data Quality Scoring**: Tracks data completeness and reliability

### 3. Advanced Calculations

#### DCF (Discounted Cash Flow)
- **Free Cash Flow variants**: FCFF, FCFE, Levered FCF
- **Growth rate modeling**: Multiple growth scenarios
- **Terminal value calculation**: Gordon Growth Model and Exit Multiple
- **Sensitivity analysis**: Monte Carlo simulations

#### DDM (Dividend Discount Model)
- **Multiple DDM variants**: Gordon Growth, Two-Stage, H-Model
- **Dividend sustainability**: Payout ratio analysis
- **Growth assumptions**: Historical and projected growth rates

#### P/B (Price-to-Book) Analysis
- **Historical P/B trends**: Multi-year analysis (2015-2024)
- **Industry comparisons**: Relative valuation metrics
- **Book value quality**: Tangible book value adjustments
- **Fair value estimation**: P/B-based intrinsic value

### 4. Performance Optimization

- **Lazy Loading**: Data loaded only when needed
- **Memory Management**: Configurable memory limits with LRU eviction
- **Calculation Caching**: Results cached with dependency invalidation
- **Background Refresh**: Automatic data updates for frequently accessed variables

## Migration from Legacy System

### Step-by-Step Migration

1. **Backup Existing Data**
   ```bash
   # Create backup of current data
   cp -r data/ data_backup/
   ```

2. **Update Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migration Tests**
   ```bash
   cd tests
   python test_runner_simple.py
   ```

4. **Verify Data Compatibility**
   - Check Excel file structure matches expected format
   - Validate existing calculations produce same results
   - Test API connectivity

### Legacy Compatibility

The unified system maintains backward compatibility with:
- ✅ Existing Excel file formats
- ✅ Previous calculation methods
- ✅ Current API integrations
- ✅ Streamlit interface layouts

## Configuration

### System Configuration

Edit `config.py` for:
```python
# Excel structure settings
excel_structure = {
    'data_start_column': 4,
    'ltm_column': 15, 
    'max_scan_rows': 59
}

# DCF default parameters
dcf = {
    'default_discount_rate': 0.10,
    'default_terminal_growth_rate': 0.025,
    'growth_rate_periods': [1, 3, 5, 10]
}

# Data validation settings
validation = {
    'min_data_completeness': 0.7,
    'strict_validation': False
}
```

### Registry Configuration

Customize variable mappings in `registry_config.yaml`:
```yaml
financial_variables:
  total_revenue:
    excel_names: ["Total Revenue", "Revenue", "Net Sales"]
    data_type: "float"
    unit_scale: "millions"
    required: true
  
  net_income:
    excel_names: ["Net Income", "Net Earnings"]
    data_type: "float"
    unit_scale: "millions"
    required: true
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Fix relative import issues
   import sys
   sys.path.append('/path/to/project/root')
   ```

2. **Missing Excel Data**
   - Verify file names match expected format
   - Check data placement in FY/ and LTM/ directories
   - Ensure Excel files contain expected sheet names

3. **API Rate Limits**
   - Implement delays between calls
   - Use caching to reduce API requests
   - Configure multiple API keys for failover

4. **Calculation Discrepancies**
   - Check data units (thousands vs millions)
   - Verify fiscal year-end dates
   - Review currency conversions

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

Monitor performance:
```bash
# Run performance tests
cd tests
python -m pytest tests/performance/ -v
```

## API Reference

### Core Classes

#### VarInputData
```python
class VarInputData:
    def __init__(self, config_path="registry_config.yaml"):
        """Initialize variable input data system"""
    
    def get_variable(self, variable_name: str, ticker: str) -> Any:
        """Get variable value for specific company"""
    
    def set_variable(self, variable_name: str, ticker: str, value: Any):
        """Set variable value for specific company"""
```

#### FinancialVariableRegistry
```python
class FinancialVariableRegistry:
    def register_variable(self, name: str, config: dict):
        """Register new financial variable"""
    
    def get_variable_config(self, name: str) -> dict:
        """Get variable configuration"""
    
    def list_variables(self) -> List[str]:
        """List all registered variables"""
```

#### FinancialCalculator
```python
class FinancialCalculator:
    def load_company_data(self, ticker: str):
        """Load data for specific company"""
    
    def calculate_dcf(self, **kwargs) -> dict:
        """Calculate DCF valuation"""
    
    def calculate_ddm(self, **kwargs) -> dict:
        """Calculate DDM valuation"""
    
    def calculate_pb_analysis(self, **kwargs) -> dict:
        """Calculate P/B analysis"""
```

## Best Practices

### Data Management
1. **Consistent Naming**: Use standardized variable names
2. **Data Validation**: Always validate input data before calculations
3. **Error Handling**: Implement robust error handling for missing data
4. **Caching**: Use caching for expensive calculations
5. **Documentation**: Document custom variables and calculations

### Performance
1. **Lazy Loading**: Load data only when needed
2. **Memory Management**: Monitor memory usage with large datasets
3. **API Limits**: Respect API rate limits and implement delays
4. **Batch Operations**: Process multiple calculations together when possible

### Testing
1. **Unit Tests**: Test individual components thoroughly
2. **Integration Tests**: Validate multi-component workflows
3. **Data Validation**: Test with real company data
4. **Regression Tests**: Ensure updates don't break existing functionality

## Support and Resources

### Documentation
- **Testing Guide**: See `TESTING_DOCUMENTATION.md`
- **API Documentation**: Generated from code docstrings
- **Configuration Reference**: See `config.py` and `registry_config.yaml`

### Community
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions for tips and best practices
- **Contributions**: Follow contribution guidelines for code submissions

### Getting Help
1. Check this documentation first
2. Review error messages and logs
3. Search existing issues and discussions
4. Create detailed bug reports with reproducible examples

---

*For additional support, consult the comprehensive testing documentation and API reference materials.*