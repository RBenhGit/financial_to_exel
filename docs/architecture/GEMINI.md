# Gemini Code Assistant - Project Guide

This document provides a comprehensive guide for Gemini to understand and interact with the Financial Analysis Toolkit project.

## Project Overview

This project is a comprehensive Python-based financial analysis toolkit for calculating Free Cash Flow (FCF), Discounted Cash Flow (DCF), Dividend Discount Model (DDM), and Price-to-Book (P/B) valuations.

It features a modular architecture with the following key components:

*   **Core Engine**: A central engine for all financial calculations, ensuring mathematical purity and consistency.
*   **Data Processing**: A robust system for handling data from multiple sources, including Excel files and financial APIs.
*   **Universal Data Registry**: A centralized data management system with caching, validation, and source prioritization.
*   **Streamlit Web Interface**: A modern, responsive web interface for interactive analysis and visualization.

### Key Technologies

*   **Backend**: Python
*   **Data Analysis**: pandas, NumPy, SciPy
*   **Web Interface**: Streamlit
*   **Data Visualization**: Plotly
*   **Testing**: pytest, Hypothesis

## Building and Running

### Installation

To set up the development environment, install the required dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Application

The project includes a Streamlit web interface for interactive analysis. To launch the application, use the following command:

```bash
# On Windows
run_fcf_streamlit.bat

# On other platforms
streamlit run fcf_analysis_streamlit.py
```

The application will be available at `http://localhost:8501`.

### Running Tests

The project has a comprehensive test suite. To run the tests, use the following command:

```bash
pytest
```

You can also run specific categories of tests using markers:

```bash
# Run unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

## Development Conventions

### Code Style

The project follows the PEP 8 style guide and uses the following tools to enforce code quality:

*   **Black**: for code formatting
*   **isort**: for import sorting
*   **Flake8**: for linting
*   **Ruff**: for linting
*   **Pylint**: for static analysis
*   **Bandit**: for security analysis

Use the `Makefile` to easily format and lint the code:

```bash
# Format the code
make format

# Lint the code
make lint
```

### Testing

The project has a strong emphasis on testing. All new features should be accompanied by comprehensive tests. The tests are organized into the following categories:

*   **Unit tests**: for testing individual components in isolation.
*   **Integration tests**: for testing the interaction between different components.
*   **Regression tests**: for ensuring that new changes do not break existing functionality.

### Configuration

The project uses a centralized configuration system with the following files:

*   `config.py`: Main application configuration.
*   `app_config.json`: Runtime configuration.
*   `registry_config.yaml`: Universal Data Registry configuration.

These files allow for flexible customization of the application's behavior without modifying the source code.
