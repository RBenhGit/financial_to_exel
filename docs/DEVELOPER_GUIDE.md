# Developer Guide: Extending Valuation Models

## Overview

This guide provides instructions for developers who want to extend the existing valuation framework with new models or enhance existing functionality.

## Architecture Overview

The valuation system follows a modular architecture:

```
Financial Analysis Framework
├── Core Data Layer
│   ├── financial_calculations.py (FCF and metrics)
│   ├── centralized_data_manager.py (Data management)
│   └── config.py (Configuration system)
├── Valuation Models
│   ├── dcf_valuation.py (DCF analysis)
│   ├── ddm_valuation.py (Dividend analysis)
│   └── pb_valuation.py (Price-to-book analysis)
├── Data Sources
│   ├── enhanced_data_manager.py (Multi-source data)
│   └── Various API converters
└── User Interface
    └── fcf_analysis_streamlit.py (Web interface)
```

## Adding a New Valuation Model

### Step 1: Create the Valuation Module

Create a new file following the naming convention: `{model_name}_valuation.py`

```python
"""
{Model Name} Valuation Module
==============================

Brief description of the valuation model and its purpose.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class {ModelName}Valuator:
    """
    Handles {Model Name} valuation calculations and analysis
    """
    
    def __init__(self, financial_calculator):
        """
        Initialize valuator with financial calculator
        
        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator
        # Initialize model-specific parameters
    
    def calculate_{model}_valuation(self, assumptions=None):
        """
        Calculate {model} valuation
        
        Parameters
        ----------
        assumptions : dict, optional
            Model-specific assumptions
            
        Returns
        -------
        dict
            Valuation results
        """
        # Implementation here
        pass
```

### Step 2: Add Configuration Support

Add model-specific configuration in `config.py`:

```python
@dataclass
class {ModelName}Config:
    """Configuration for {Model Name} valuation"""
    default_parameter_1: float = 0.10
    default_parameter_2: int = 5
    # Add other model-specific parameters
```

### Step 3: Integration with Financial Calculator

Add a method to `FinancialCalculator` class:

```python
def get_{model}_valuator(self):
    """Get {Model Name} valuator instance"""
    from {model}_valuation import {ModelName}Valuator
    return {ModelName}Valuator(self)
```

### Step 4: Streamlit Integration

Add the new model to the Streamlit interface in `fcf_analysis_streamlit.py`:

```python
# In the valuation section
if st.button("Run {Model Name} Analysis"):
    {model}_valuator = calculator.get_{model}_valuator()
    {model}_result = {model}_valuator.calculate_{model}_valuation()
    
    # Display results
    st.subheader("{Model Name} Valuation Results")
    st.metric("Valuation", f"${model}_result.get('value_per_share', 0):.2f}")
```

## Extending Existing Models

### Adding New Features to DCF Model

1. Add new calculation methods to `DCFValuator` class
2. Update the `calculate_dcf_projections` method to include new features
3. Add configuration parameters in `DCFConfig`
4. Update the Streamlit interface to expose new features

### Example: Adding Monte Carlo Simulation

```python
def monte_carlo_simulation(self, assumptions, num_simulations=1000):
    """
    Perform Monte Carlo simulation on DCF valuation
    
    Parameters
    ----------
    assumptions : dict
        Base assumptions with uncertainty ranges
    num_simulations : int
        Number of simulation runs
        
    Returns
    -------
    dict
        Simulation results with statistics
    """
    results = []
    
    for _ in range(num_simulations):
        # Generate random assumptions within ranges
        sim_assumptions = self._generate_random_assumptions(assumptions)
        
        # Calculate DCF with random assumptions
        dcf_result = self.calculate_dcf_projections(sim_assumptions)
        results.append(dcf_result.get('value_per_share', 0))
    
    return {
        'mean': np.mean(results),
        'std': np.std(results),
        'percentiles': np.percentile(results, [5, 25, 50, 75, 95]),
        'all_results': results
    }
```

## Best Practices

### 1. Documentation Standards

- Use NumPy-style docstrings
- Include comprehensive examples
- Document all parameters and return values
- Add module-level documentation

### 2. Error Handling

```python
try:
    # Calculation logic
    result = complex_calculation()
except Exception as e:
    logger.error(f"Error in {model} calculation: {e}")
    return {
        'error': 'calculation_failed',
        'error_message': str(e),
        'model_type': '{model}'
    }
```

### 3. Data Validation

```python
def _validate_inputs(self, assumptions):
    """Validate input assumptions"""
    if assumptions.get('discount_rate', 0) <= 0:
        raise ValueError("Discount rate must be positive")
    
    if assumptions.get('growth_rate', 0) >= assumptions.get('discount_rate', 0):
        raise ValueError("Growth rate must be less than discount rate")
```

### 4. Configuration Integration

```python
from config import get_{model}_config

def __init__(self, financial_calculator):
    self.financial_calculator = financial_calculator
    {model}_config = get_{model}_config()
    self.default_assumptions = {
        'parameter_1': {model}_config.default_parameter_1,
        'parameter_2': {model}_config.default_parameter_2
    }
```

## Testing New Models

### Unit Tests

Create test files following the pattern: `test_{model}_valuation.py`

```python
import pytest
from {model}_valuation import {ModelName}Valuator
from financial_calculations import FinancialCalculator

class Test{ModelName}Valuator:
    def test_basic_calculation(self):
        # Test basic valuation calculation
        pass
    
    def test_edge_cases(self):
        # Test edge cases and error conditions
        pass
    
    def test_sensitivity_analysis(self):
        # Test sensitivity analysis if implemented
        pass
```

### Integration Tests

Test the model within the full application context:

```python
def test_{model}_integration():
    calculator = FinancialCalculator("test_data/AAPL")
    {model}_valuator = calculator.get_{model}_valuator()
    result = {model}_valuator.calculate_{model}_valuation()
    
    assert 'value_per_share' in result
    assert result['value_per_share'] > 0
```

## Performance Considerations

### Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _expensive_calculation(self, param1, param2):
    """Cache expensive calculations"""
    # Expensive computation here
    return result
```

### Vectorized Operations

Use NumPy and Pandas for efficient calculations:

```python
# Instead of loops
values = []
for i in range(len(data)):
    values.append(data[i] * factor)

# Use vectorized operations
values = data * factor
```

## Deployment Checklist

- [ ] Add comprehensive docstrings
- [ ] Include usage examples
- [ ] Add unit tests
- [ ] Update configuration system
- [ ] Integrate with Streamlit interface
- [ ] Add error handling
- [ ] Performance optimization
- [ ] Documentation updates

## Common Patterns

### Model Selection Logic

```python
def _select_model_variant(self, data_characteristics):
    """Automatically select the best model variant"""
    if data_characteristics['stability'] > 0.8:
        return 'stable_model'
    elif data_characteristics['growth_pattern'] == 'two_stage':
        return 'two_stage_model'
    else:
        return 'multi_stage_model'
```

### Sensitivity Analysis Framework

```python
def sensitivity_analysis(self, parameters, ranges):
    """Generic sensitivity analysis framework"""
    results = []
    
    for param in parameters:
        for value in ranges[param]:
            assumptions = self.default_assumptions.copy()
            assumptions[param] = value
            
            result = self.calculate_valuation(assumptions)
            results.append({
                'parameter': param,
                'value': value,
                'valuation': result['value_per_share']
            })
    
    return self._format_sensitivity_results(results)
```

This guide provides the foundation for extending the valuation framework. For specific implementation questions, refer to the existing model implementations as examples.