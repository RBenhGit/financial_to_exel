# Monte Carlo Risk Analysis - Complete User Guide

## Introduction

The Monte Carlo Risk Analysis system provides sophisticated probabilistic financial modeling capabilities, allowing analysts to quantify uncertainty and assess risk in their valuations. This guide covers setup, usage, and advanced features of the Monte Carlo engine.

## Overview

Monte Carlo simulation uses random sampling to model the probability distribution of financial metrics under uncertainty. Our implementation provides:

- **Probabilistic DCF Analysis**: Monte Carlo simulation for DCF valuation with uncertainty modeling
- **Risk Assessment**: Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR) calculations
- **Scenario Analysis**: Best case, worst case, and most likely outcomes
- **Parameter Uncertainty**: Revenue growth, margin volatility, discount rate distributions
- **Portfolio Risk**: Multi-asset portfolio VaR calculations

## Getting Started

### Basic Setup

```python
from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine
from core.analysis.engines.financial_calculations import FinancialCalculator

# Initialize with company data
calc = FinancialCalculator('AAPL')
monte_carlo = MonteCarloEngine(calc)

# Run basic DCF simulation
result = monte_carlo.simulate_dcf_valuation(
    num_simulations=10000,
    revenue_growth_volatility=0.15,
    discount_rate_volatility=0.02
)

print(f"Expected Value: ${result.mean_value:.2f}")
print(f"95% Confidence Interval: ${result.ci_95[0]:.2f} - ${result.ci_95[1]:.2f}")
```

### Quick Start Templates

```python
from core.analysis.statistics.monte_carlo_engine import quick_dcf_simulation

# Low volatility simulation (conservative)
conservative_result = quick_dcf_simulation(
    calc,
    num_simulations=5000,
    volatility_level='low'
)

# High volatility simulation (aggressive scenarios)
aggressive_result = quick_dcf_simulation(
    calc,
    num_simulations=10000,
    volatility_level='high'
)
```

## Core Components

### 1. Parameter Distributions

The system supports multiple statistical distributions for modeling parameter uncertainty:

#### Normal Distribution
Most common for parameters like growth rates:
```python
from core.analysis.statistics.monte_carlo_engine import ParameterDistribution, DistributionType

revenue_growth_dist = ParameterDistribution(
    distribution=DistributionType.NORMAL,
    params={'mean': 0.05, 'std': 0.15},
    name='Revenue Growth Rate'
)
```

#### Lognormal Distribution
Ideal for parameters that can't be negative (like margins):
```python
margin_dist = ParameterDistribution(
    distribution=DistributionType.LOGNORMAL,
    params={'mean': 0.20, 'std': 0.05},
    name='Operating Margin'
)
```

#### Beta Distribution
Useful for bounded parameters (0-1):
```python
payout_ratio_dist = ParameterDistribution(
    distribution=DistributionType.BETA,
    params={'alpha': 2, 'beta': 3, 'low': 0.0, 'high': 1.0},
    name='Dividend Payout Ratio'
)
```

### 2. Risk Metrics

The system automatically calculates comprehensive risk metrics:

```python
# Access risk metrics from simulation results
risk_metrics = result.risk_metrics

print(f"Value at Risk (5%): ${risk_metrics.var_5:.2f}")
print(f"Conditional VaR (5%): ${risk_metrics.cvar_5:.2f}")
print(f"Maximum Drawdown: ${risk_metrics.max_drawdown:.2f}")
print(f"Probability of Loss: {risk_metrics.probability_of_loss:.2%}")
```

### 3. Statistical Analysis

Detailed statistical analysis of simulation results:

```python
# Generate comprehensive summary
summary_df = result.summary_table()
print(summary_df)

# Access specific statistics
print(f"Mean: ${result.statistics['mean']:.2f}")
print(f"Standard Deviation: ${result.statistics['std']:.2f}")
print(f"Skewness: {result.statistics['skewness']:.3f}")
print(f"Kurtosis: {result.statistics['kurtosis']:.3f}")
```

## Advanced Usage

### 1. Custom Parameter Distributions

Define custom distributions based on historical data:

```python
import pandas as pd

# Historical revenue growth data
historical_data = pd.DataFrame({
    'revenue_growth': [0.08, 0.12, 0.05, -0.02, 0.15, 0.09, 0.11]
})

# Estimate distributions from historical data
param_mapping = {'revenue_growth': 'revenue_growth'}
estimated_distributions = monte_carlo.estimate_parameter_distributions(
    historical_data,
    param_mapping
)

# Use estimated distributions in simulation
result = monte_carlo.simulate_dcf_valuation(
    num_simulations=10000,
    custom_distributions=estimated_distributions
)
```

### 2. Correlated Parameters

Model parameter correlations for realistic scenarios:

```python
import numpy as np

# Define correlation matrix for revenue growth and margins
correlation_matrix = np.array([
    [1.0, 0.7],   # Revenue growth with itself and margins
    [0.7, 1.0]    # Margins with revenue growth and itself
])

# Set correlation for simulation
monte_carlo.set_correlation_matrix(
    param_names=['revenue_growth', 'operating_margin'],
    correlation_matrix=correlation_matrix
)

# Run correlated simulation
correlated_result = monte_carlo.simulate_dcf_valuation(num_simulations=10000)
```

### 3. Scenario Analysis

Run predefined scenarios alongside Monte Carlo analysis:

```python
from core.analysis.statistics.monte_carlo_engine import create_standard_scenarios

# Get standard scenarios
scenarios = create_standard_scenarios()

# Add custom scenario
scenarios['Tech Bubble'] = {
    'revenue_growth': 0.30,
    'discount_rate': 0.06,
    'terminal_growth': 0.06,
    'operating_margin': 0.35
}

# Run scenario analysis
scenario_results = monte_carlo.run_scenario_analysis(scenarios, 'dcf')

for scenario, value in scenario_results.items():
    print(f"{scenario}: ${value:.2f}")
```

### 4. Dividend Discount Model Simulation

Monte Carlo analysis for dividend-focused stocks:

```python
ddm_result = monte_carlo.simulate_dividend_discount_model(
    num_simulations=10000,
    dividend_growth_volatility=0.20,
    required_return_volatility=0.02,
    payout_ratio_volatility=0.10
)

print(f"Expected DDM Value: ${ddm_result.mean_value:.2f}")
print(f"DDM Risk Metrics: {ddm_result.risk_metrics.to_dict()}")
```

## Portfolio Risk Analysis

### Multi-Asset Portfolio VaR

Calculate portfolio-level risk metrics:

```python
# Simulate individual assets
aapl_result = monte_carlo_aapl.simulate_dcf_valuation(10000)
msft_result = monte_carlo_msft.simulate_dcf_valuation(10000)
googl_result = monte_carlo_googl.simulate_dcf_valuation(10000)

# Define portfolio weights
portfolio_weights = {
    'AAPL': 0.4,
    'MSFT': 0.35,
    'GOOGL': 0.25
}

# Individual simulation results
individual_simulations = {
    'AAPL': aapl_result,
    'MSFT': msft_result,
    'GOOGL': googl_result
}

# Calculate portfolio VaR
portfolio_var = monte_carlo.calculate_portfolio_var(
    portfolio_weights=portfolio_weights,
    individual_simulations=individual_simulations,
    confidence_level=0.05
)

print(f"Portfolio VaR (5%): ${portfolio_var['portfolio_var']:.2f}")
print(f"Portfolio CVaR (5%): ${portfolio_var['portfolio_cvar']:.2f}")
```

## Visualization Integration

### Streamlit Dashboard Integration

```python
import streamlit as st
from ui.visualization.monte_carlo_visualizer import MonteCarloVisualizer

# In your Streamlit app
st.title("Monte Carlo Risk Analysis")

# Run simulation
if st.button("Run Monte Carlo Simulation"):
    with st.spinner("Running simulation..."):
        result = monte_carlo.simulate_dcf_valuation(
            num_simulations=st.slider("Number of Simulations", 1000, 20000, 10000)
        )

    # Visualize results
    visualizer = MonteCarloVisualizer()

    # Distribution plot
    st.plotly_chart(visualizer.create_distribution_chart(result))

    # Risk metrics dashboard
    st.plotly_chart(visualizer.create_risk_dashboard(result))

    # Summary statistics
    st.dataframe(result.summary_table())
```

### Custom Visualization

```python
import plotly.graph_objects as go
import plotly.express as px

def create_custom_risk_chart(result):
    """Create custom risk visualization"""
    fig = go.Figure()

    # Add histogram
    fig.add_trace(go.Histogram(
        x=result.values,
        name="Simulation Results",
        nbinsx=50,
        opacity=0.7
    ))

    # Add VaR line
    fig.add_vline(
        x=result.risk_metrics.var_5,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR (5%): ${result.risk_metrics.var_5:.2f}"
    )

    # Add mean line
    fig.add_vline(
        x=result.mean_value,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Expected: ${result.mean_value:.2f}"
    )

    fig.update_layout(
        title="Monte Carlo Valuation Distribution",
        xaxis_title="Valuation ($)",
        yaxis_title="Frequency"
    )

    return fig
```

## Performance Optimization

### Simulation Size Guidelines

- **Quick Analysis**: 1,000 - 5,000 simulations
- **Standard Analysis**: 10,000 simulations (recommended)
- **High Precision**: 50,000 - 100,000 simulations
- **Research/Academic**: 100,000+ simulations

### Memory Management

```python
# For large simulations, process in batches
def run_large_simulation(monte_carlo, total_simulations=100000, batch_size=10000):
    """Run large simulation in batches to manage memory"""
    all_results = []

    num_batches = total_simulations // batch_size

    for i in range(num_batches):
        batch_result = monte_carlo.simulate_dcf_valuation(
            num_simulations=batch_size,
            random_state=i  # Ensure different random seeds
        )
        all_results.extend(batch_result.values)

    # Combine results
    combined_values = np.array(all_results)
    return SimulationResult(combined_values)
```

### Caching Results

```python
import pickle
from pathlib import Path

# Cache simulation results
def save_simulation_result(result, filename):
    """Save simulation result to file"""
    cache_path = Path("data/cache/monte_carlo")
    cache_path.mkdir(parents=True, exist_ok=True)

    with open(cache_path / f"{filename}.pkl", 'wb') as f:
        pickle.dump(result, f)

def load_simulation_result(filename):
    """Load cached simulation result"""
    cache_path = Path("data/cache/monte_carlo")

    with open(cache_path / f"{filename}.pkl", 'rb') as f:
        return pickle.load(f)

# Usage
save_simulation_result(result, "aapl_dcf_20241201")
cached_result = load_simulation_result("aapl_dcf_20241201")
```

## Best Practices

### 1. Parameter Selection
- Use historical data when available for distribution estimation
- Consider business cycle impacts on parameter volatility
- Validate parameters with industry benchmarks
- Test sensitivity to different distribution choices

### 2. Simulation Configuration
- Start with 10,000 simulations for most analyses
- Use random seeds for reproducible results
- Set realistic bounds on all parameters
- Consider parameter correlations

### 3. Risk Interpretation
- Focus on VaR and CVaR for risk assessment
- Consider the full distribution, not just point estimates
- Validate results with stress testing
- Combine with scenario analysis for comprehensive view

### 4. Performance Optimization
- Use appropriate simulation sizes for the analysis purpose
- Cache results for repeated analyses
- Monitor memory usage for large simulations
- Consider parallel processing for very large analyses

## Error Handling and Validation

### Parameter Validation

```python
def validate_simulation_parameters(params):
    """Validate Monte Carlo parameters"""
    errors = []

    # Check for negative volatilities
    for key, value in params.items():
        if 'volatility' in key and value < 0:
            errors.append(f"{key} cannot be negative")

    # Check for unrealistic values
    if params.get('discount_rate_volatility', 0) > 0.10:
        errors.append("Discount rate volatility seems unrealistically high")

    return errors

# Usage
params = {
    'revenue_growth_volatility': 0.15,
    'discount_rate_volatility': 0.02
}

validation_errors = validate_simulation_parameters(params)
if validation_errors:
    for error in validation_errors:
        st.warning(error)
```

### Result Validation

```python
def validate_simulation_results(result):
    """Validate simulation results for reasonableness"""
    warnings = []

    # Check for extreme values
    if result.statistics['std'] / result.statistics['mean'] > 2.0:
        warnings.append("High coefficient of variation - results may be unstable")

    # Check for negative values in equity valuation
    negative_count = len(result.values[result.values < 0])
    if negative_count > len(result.values) * 0.05:  # More than 5% negative
        warnings.append("High probability of negative values - check parameters")

    return warnings
```

## Troubleshooting

### Common Issues

1. **Slow Performance**
   - Reduce simulation count
   - Simplify parameter distributions
   - Use caching for repeated runs

2. **Unrealistic Results**
   - Check parameter bounds
   - Validate distribution parameters
   - Review correlation assumptions

3. **High Variability**
   - Examine parameter volatility settings
   - Consider reducing uncertainty ranges
   - Add parameter constraints

4. **Memory Errors**
   - Use batch processing
   - Reduce simulation count
   - Clear unnecessary variables

---

*This guide covers the core functionality of the Monte Carlo Risk Analysis system. For advanced customization and integration, refer to the API documentation and source code examples.*