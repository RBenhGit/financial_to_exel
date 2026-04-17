# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Python-based financial analysis toolkit for calculating Free Cash Flow (FCF), Discounted Cash Flow (DCF), Dividend Discount Model (DDM), and Price-to-Book (P/B) valuations. The project features a modern, modular architecture with both a Streamlit web interface and programmatic API access.

## Essential Commands

### Development Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Launch the web interface
python run_streamlit_app.py
# OR use the batch file
run_fcf_streamlit.bat
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/regression/     # Regression tests

# Run with coverage
pytest --cov=core --cov=config --cov=utils

# Run specific test markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m slow             # Long-running tests
pytest -m api_dependent    # Tests requiring API access
pytest -m excel_dependent  # Tests requiring Excel files
```

### Coverage Analysis
```bash
# Comprehensive coverage analysis workflow
make coverage-analysis

# Or run the Python script directly  
python scripts/run_coverage_analysis.py

# Generate basic coverage report only
make coverage-report

# Windows batch script (alternative)
scripts\run_coverage_analysis.bat

# Manual coverage run
pytest tests/test_basic.py --cov=core --cov=config --cov=utils --cov-report=html --cov-report=term-missing --cov-report=json
python tools/coverage_analysis.py
```

### Code Quality
```bash
# Format code with Black
black --line-length 100 .

# Sort imports with isort
isort .

# Run linting with flake8
flake8 .

# Run type checking with mypy (if configured)
mypy .

# Run security checks with bandit
bandit -r .

# Run all quality checks with ruff
ruff check .
ruff format .
```

## Architecture

### Core Modules Structure
- `core/analysis/engines/` - Main calculation engines (Financial Calculator, DCF, etc.)
- `core/analysis/dcf/` - DCF-specific valuation models
- `core/analysis/ddm/` - Dividend Discount Model implementation
- `core/analysis/pb/` - Price-to-Book analysis and historical comparison
- `core/data_processing/` - Data handling, validation, and processing
- `core/data_sources/` - External data source interfaces and API integrations

### Key Components
- **FinancialCalculator**: Main calculation engine (`core/analysis/engines/financial_calculations.py`)
- **Enhanced Data Manager**: Multi-source data integration with caching
- **Universal Data Registry**: Centralized configuration-driven data management
- **Streamlit Interface**: Web-based UI (`fcf_analysis_streamlit.py`)

### Extended Module Reference

**core/data_processing/ (additional modules)**
- `api_batch_manager.py` — batch API request management
- `background_refresh.py` — async background data refresh
- `calculation_cache.py` — calculation result caching
- `data_contracts.py` — data structure contracts/schemas
- `financial_variable_registry.py` — financial variable registry
- `standard_financial_variables.py` — standard variable definitions
- `variable_processor.py` — variable processing pipeline
- `adapters/excel_adapter.py` — Excel-specific adapter layer
- `converters/twelve_data_converter.py` — Twelve Data API converter
- `rate_limiting/enhanced_rate_limiter.py` — enhanced rate limiting with circuit breaker

**core/data_sources/ (additional modules)**
- `real_time_price_service.py` — real-time price feed
- `industry_data_service.py` — industry/sector data service
- `price_service_integration.py` — price service integration bridge

**core/error_handling/ (full module)**
- `__init__.py` — package init; exports `get_error_handler`, `with_api_error_handling` and other convenience helpers
- `api_error_handler.py` — API error handling with exponential backoff retry logic, circuit breaker pattern, and failure categorisation
- `data_quality_validator.py` — multi-dimensional data quality scoring: completeness, accuracy, freshness, consistency, and confidence intervals
- `graceful_degradation.py` — fallback strategies when external sources fail; supports historical-only and reduced-feature modes
- `user_message_handler.py` — translates technical errors into user-friendly, actionable guidance with Streamlit UI integration

**core/ root utilities**
- `dependency_injection.py` — dependency injection container
- `module_adapter.py` — module compatibility adapter
- `register_variables.py` — variable registration
- `registry_config_loader.py` — registry configuration loader
- `registry_integration_adapter.py` — registry integration adapter

**presentation/ (flat Python files)**
- `base_presenter.py` — base presenter class
- `dcf_presenter.py` — DCF analysis presenter
- `financial_presenter.py` — financial data presenter
- `settings_presenter.py` — settings presenter
- `watchlist_presenter.py` — watch list presenter
- `report_generator.py` — report generation
- `watch_list_visualizer.py` — watch list visualization components
- `streamlit_app_refactored.py` — refactored Streamlit app entry point
- `analysis_capture.py` — analysis result capture/export
- `streamlit_help.py` — help system for Streamlit UI
- `streamlit_utils.py` — Streamlit utility functions

**ui/ (flat Python files)**
- `components.py` — reusable UI components
- `layouts.py` — page layout definitions
- `widgets.py` — custom widget implementations

**performance/**
- `concurrent_watch_list_optimizer.py` — concurrent watch list optimization
- `performance_benchmark.py` — performance benchmarking tools
- `streamlit_performance_integration.py` — Streamlit performance integration

### Data Sources
- **Excel Files**: Primary data source in `data/companies/{TICKER}/` with FY/ and LTM/ folders
- **APIs**: yfinance, Alpha Vantage, FMP, Polygon with automatic fallback
- **Caching**: Multi-tier caching system in `data/cache/`

## Development Guidelines

### Calculation Verification
When implementing new calculations, verify first that the calculation doesn't already exist in the financial calculation engine. If not, add it to the engine rather than duplicating logic.

### File Organization
- Place new analysis features in appropriate `core/analysis/` subdirectories
- Add tests in corresponding `tests/` subdirectories
- Follow the modular architecture with clear separation of concerns

### Data Handling
- Use the Enhanced Data Manager for multi-source data integration
- Implement proper error handling and fallback mechanisms
- Follow the Universal Data Registry patterns for configuration

### Testing Standards
- Maintain comprehensive test coverage
- Use appropriate test markers for different test types
- Include both unit and integration tests for new features
- Test with real data when possible, avoid artificial data

## Configuration

### Environment Variables
Configure API keys in `.env` file:
```
ALPHA_VANTAGE_API_KEY=your_key_here
FMP_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

### Configuration Files
- `config.py` - Main application configuration with dataclass-based settings
- `pyproject.toml` - Development tools configuration (Black, isort, pytest, etc.)
- `registry_config.yaml` - Data registry settings
- `.flake8` - Linting configuration

### Documentation
- `UNIFIED_DATA_SYSTEM_GUIDE.md` — comprehensive guide to the unified data system
- `TESTING_DOCUMENTATION.md` — testing standards and coverage documentation
- `PERFORMANCE_OPTIMIZATIONS.md` — performance optimization details and benchmarks

### Code Style
- Line length: 100 characters (configured in Black and flake8)
- Python version: 3.13+ target
- Use type hints where appropriate
- Follow Google docstring conventions
- Import organization handled by isort with sections: FUTURE, STDLIB, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

## Common Tasks

### Adding New Financial Calculations
1. Check if calculation exists in `core/analysis/engines/financial_calculation_engine.py`
2. If new, add to the appropriate engine class
3. Add comprehensive unit tests
4. Update documentation

### Excel Data Integration
> **Note**: The `data/companies/` directory is empty by default. Company financial data is loaded on-demand via APIs (yfinance, Alpha Vantage, FMP, Polygon). To use Excel files as the primary data source, place financial statements in `data/companies/{TICKER}/FY/` and `data/companies/{TICKER}/LTM/` following the naming convention: "Income Statement.xlsx", "Balance Sheet.xlsx", "Cash Flow Statement.xlsx".

1. Place company data in `data/companies/{TICKER}/FY/` and `data/companies/{TICKER}/LTM/`
2. Ensure files follow expected naming: "Income Statement.xlsx", "Balance Sheet.xlsx", "Cash Flow Statement.xlsx"
3. Use the FinancialCalculator class for automatic loading

### Adding New Data Sources
1. Create converter in `core/data_processing/converters/`
2. Implement interface following existing patterns
3. Add to Enhanced Data Manager configuration
4. Include comprehensive error handling and rate limiting

## Task Master AI Integration

This project uses Task Master AI for development workflow management. Essential Task Master commands:

```bash
# Core Workflow Commands
task-master init                                    # Initialize Task Master in current project
task-master parse-prd .taskmaster/docs/prd.txt      # Generate tasks from PRD document
task-master models --setup                        # Configure AI models interactively

# Daily Development Workflow
task-master list                                   # Show all tasks with status
task-master next                                   # Get next available task to work on
task-master show <id>                             # View detailed task information
task-master set-status --id=<id> --status=done    # Mark task complete

# Task Management
task-master add-task --prompt="description" --research        # Add new task with AI assistance
task-master expand --id=<id> --research --force              # Break task into subtasks
task-master update-task --id=<id> --prompt="changes"         # Update specific task
task-master update --from=<id> --prompt="changes"            # Update multiple tasks from ID onwards
task-master update-subtask --id=<id> --prompt="notes"        # Add implementation notes to subtask

# Analysis & Planning
task-master analyze-complexity --research          # Analyze task complexity
task-master complexity-report                      # View complexity analysis
task-master expand --all --research               # Expand all eligible tasks
```

See `.taskmaster/CLAUDE.md` for complete Task Master integration details and MCP configuration.
- there should be no hard coded values. all values should be aquired from the input sources
- The application shoul not hard code specific companies. Hard code of specific companies is restricted for tests only.