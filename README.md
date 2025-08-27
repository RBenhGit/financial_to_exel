# Financial Analysis Project

A comprehensive Python-based financial analysis toolkit for calculating Free Cash Flow (FCF), Discounted Cash Flow (DCF), Dividend Discount Model (DDM), and Price-to-Book (P/B) valuations.

## 🏗️ Project Structure

This project has been reorganized into a clean, modular architecture:

```
financial_to_exel/
├── core/                           # Core business logic
│   ├── analysis/                   # Financial analysis modules
│   │   ├── engines/               # Main calculation engines
│   │   │   ├── financial_calculations.py
│   │   │   ├── financial_calculation_engine.py
│   │   │   └── calculation_engine_integration_example.py
│   │   ├── dcf/                   # DCF valuation
│   │   │   ├── dcf_valuation.py
│   │   │   └── debug_dcf_*.py
│   │   ├── ddm/                   # Dividend Discount Model
│   │   │   └── ddm_valuation.py
│   │   ├── pb/                    # Price-to-Book analysis
│   │   │   ├── pb_calculation_engine.py
│   │   │   ├── pb_fair_value_calculator.py
│   │   │   ├── pb_historical_analysis.py
│   │   │   ├── pb_statistical_analysis.py
│   │   │   ├── pb_valuation.py
│   │   │   └── pb_visualizer.py
│   │   ├── fcf_consolidated.py    # FCF calculations
│   │   └── fcf_date_correlation.py # FCF date correlation
│   ├── data_processing/           # Data handling and processing
│   │   ├── managers/             # Data management
│   │   │   ├── centralized_data_manager.py
│   │   │   └── enhanced_data_manager.py
│   │   ├── processors/           # Data processors
│   │   │   ├── data_processing.py
│   │   │   └── centralized_data_processor.py
│   │   ├── converters/           # API data converters
│   │   │   ├── alpha_vantage_converter.py
│   │   │   ├── fmp_converter.py
│   │   │   ├── polygon_converter.py
│   │   │   └── yfinance_converter.py
│   │   ├── data_validator.py
│   │   ├── unified_data_adapter.py
│   │   ├── universal_data_registry.py
│   │   └── streamlit_data_processing.py
│   ├── data_sources/             # External data sources
│   │   ├── interfaces/           # Data source interfaces
│   │   │   ├── data_source_interfaces.py
│   │   │   ├── data_source_manager.py
│   │   │   ├── data_source_bridge.py
│   │   │   └── data_sources.py
│   │   ├── api/                 # API-specific implementations
│   │   └── excel/               # Excel data processing
│   └── validation/               # Data validation framework
│       ├── financial_metric_validators.py
│       ├── validation_orchestrator.py
│       ├── validation_registry.py
│       └── validation_reporting.py
├── config/                       # Configuration management
│   ├── __init__.py
│   ├── constants.py
│   └── settings.py
├── data/                        # Data storage
│   ├── companies/              # Company-specific financial data
│   │   ├── GOOG/              # Google/Alphabet data
│   │   ├── MSFT/              # Microsoft data  
│   │   ├── NVDA/              # NVIDIA data
│   │   ├── TSLA/              # Tesla data
│   │   └── V/                 # Visa data
│   ├── cache/                 # Multi-tier caching system
│   │   ├── data/              # Data cache
│   │   ├── global/            # Global cache
│   │   ├── production/        # Production cache
│   │   └── test/              # Test cache
│   ├── exports/               # Analysis exports
│   └── test_data/             # Test datasets
├── docs/                       # Documentation
│   ├── api/                   # API documentation
│   │   └── Financial_Metrics_Schema.md
│   ├── architecture/          # Architecture documentation
│   │   ├── ARCHITECTURE_IMPROVEMENTS.md
│   │   └── UNIVERSAL_DATA_REGISTRY_README.md
│   ├── guides/                # User guides
│   │   ├── AGENT.md
│   │   ├── AGENTS.md
│   │   ├── GEMINI.md
│   │   ├── TESTING_STANDARDS.md
│   │   └── TEST_SUITE_README.md
│   └── completion_reports/    # Task completion reports
├── legacy/                     # Deprecated files
│   ├── backup/               # Backup files
│   └── deprecated/           # Deprecated components
├── presentation/               # UI and presentation layer
│   ├── base/                  # Base presentation components
│   ├── financial/             # Financial-specific UI
│   ├── base_presenter.py      # Base presenter class
│   └── financial_presenter.py # Financial presenter
├── reports/                   # Generated reports
│   ├── analysis/              # Analysis reports
│   ├── audit_reports/         # Audit reports
│   ├── completion_summaries/  # Task completion summaries
│   ├── dependency_reports/    # Dependency analysis
│   └── diagnostic_reports/    # Diagnostic reports
├── tests/                     # Comprehensive test suite
│   ├── unit/                  # Unit tests by module
│   │   ├── data_processing/   # Data processing tests
│   │   ├── dcf/              # DCF-specific tests
│   │   ├── pb/               # P/B analysis tests
│   │   └── streamlit/        # Streamlit UI tests
│   ├── integration/           # Integration tests
│   │   ├── api/              # API integration tests
│   │   ├── data_sources/     # Data source tests
│   │   └── end_to_end/       # End-to-end tests
│   ├── regression/            # Regression tests
│   ├── performance/           # Performance tests
│   ├── fixtures/              # Test fixtures and helpers
│   └── utils/                 # Testing utilities
├── tools/                     # Development and utility tools
│   ├── diagnostics/           # Diagnostic tools
│   │   ├── logs/              # Diagnostic logs
│   │   └── reports/           # Diagnostic reports
│   ├── scripts/               # Automation scripts
│   └── utilities/             # Utility functions
├── ui/                        # User interface components
│   ├── components/            # Reusable UI components
│   ├── layouts/               # Layout definitions
│   ├── widgets/               # Custom widgets
│   └── components.py          # Component definitions
└── utils/                     # General utilities
    ├── excel_processor.py
    ├── growth_calculator.py
    └── plotting_utils.py
```

## 🚀 Features

### Financial Analysis Capabilities
- **Free Cash Flow (FCF) Analysis**: Calculate FCFF, FCFE, and LFCF
- **DCF Valuation**: Comprehensive discounted cash flow modeling
- **DDM Analysis**: Dividend discount model for dividend-paying stocks
- **P/B Analysis**: Price-to-book ratio analysis with historical comparison

### Data Sources
- **Excel Integration**: Import financial statements from Excel files
- **API Support**: Multiple financial data APIs (yfinance, Alpha Vantage, FMP, Polygon)
- **Universal Data Registry**: Centralized data management with caching

### Advanced Features
- **Multi-source validation**: Cross-validate data across multiple sources
- **Caching system**: Intelligent data caching for performance
- **Error handling**: Comprehensive error handling and reporting
- **Export capabilities**: Export analysis to Excel and CSV formats

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd financial_to_exel
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys** (optional):
   Create a `.env` file with your API keys:
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   FMP_API_KEY=your_key_here
   POLYGON_API_KEY=your_key_here
   ```

## 🔧 Quick Start

### Using the Streamlit Web Interface

1. **Launch the application:**
   ```bash
   # Windows
   run_fcf_streamlit.bat
   
   # Or manually
   streamlit run fcf_analysis_streamlit.py
   ```

2. **Access the interface:**
   Open your browser to `http://localhost:8501`

### Using the Python API

```python
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator

# Initialize with company data
calc = FinancialCalculator('data/companies/MSFT')  # Microsoft example

# Load financial statements
calc.load_financial_statements()
calc.fetch_market_data('MSFT')

# Calculate FCF
fcf_results = calc.calculate_all_fcf_types()

# Perform DCF analysis
dcf = DCFValuator(calc)
dcf_results = dcf.calculate_dcf_projections()

print(f"Intrinsic Value: ${dcf_results['value_per_share']:.2f}")
```

## 📊 Data Input Methods

### Excel Files
1. Place company financial statements in `data/companies/{TICKER}/`
2. Organize as:
   - `FY/` folder: Full year statements (10-year historical data)
   - `LTM/` folder: Latest twelve months statements
   - Required files: Income Statement, Balance Sheet, Cash Flow Statement
3. Examples available: `data/companies/GOOG/`, `data/companies/MSFT/`, etc.

### API Mode
The system automatically fetches data from configured APIs when Excel files are not available.

## 🔬 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/regression/     # Regression tests

# Run with coverage
pytest --cov=core --cov=config --cov=utils
```

## 📈 Analysis Types

### 1. Free Cash Flow Analysis
- **FCFF**: Free Cash Flow to Firm
- **FCFE**: Free Cash Flow to Equity  
- **LFCF**: Levered Free Cash Flow
- Growth rate calculations
- Historical trend analysis

### 2. DCF Valuation
- Multi-stage growth models
- Terminal value calculations
- Sensitivity analysis
- Risk-adjusted discount rates

### 3. DDM Analysis
- Gordon Growth Model
- Multi-stage dividend models
- Dividend sustainability analysis

### 4. P/B Analysis
- Current ratio analysis
- Historical P/B trends
- Fair value estimates
- Industry comparisons

## 🛠️ Development

### Code Organization Principles
- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Injection**: Loose coupling between components
- **Configuration-Driven**: Externalized configuration
- **Test Coverage**: Comprehensive test suite

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement in appropriate `core/` subdirectory
3. Add comprehensive tests in `tests/`
4. Update documentation
5. Submit pull request

## 🔧 Configuration

Configuration files:
- `config.py`: Main application configuration
- `app_config.json`: Runtime configuration
- `registry_config.yaml`: Data registry settings
- `pyproject.toml`: Development tools configuration

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:
- **API Reference**: `docs/api/`
- **Architecture**: `docs/architecture/`
- **User Guides**: `docs/guides/`

## 🚨 Error Handling

The project includes comprehensive error handling:
- **Graceful Degradation**: Falls back to alternative data sources
- **Detailed Logging**: Comprehensive logging throughout
- **Error Reports**: Automatic error report generation
- **Validation Framework**: Multi-layer data validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information

---

**Last Updated**: August 2025  
**Project Version**: 2.0 (Post-Reorganization)