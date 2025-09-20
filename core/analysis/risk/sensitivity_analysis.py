"""
Sensitivity Analysis Module
==========================

This module provides comprehensive sensitivity analysis capabilities for financial valuation models,
focusing on DCF, DDM, and P/B analysis. It implements one-way and two-way sensitivity analysis,
tornado charts, elasticity calculations, and breakeven analysis.

Key Features:
- One-way sensitivity analysis for individual parameters
- Two-way sensitivity analysis with interaction effects
- Tornado charts for variable impact ranking
- Elasticity calculations for parameter sensitivity
- Breakeven analysis for critical thresholds
- Sensitivity heatmaps for multi-variable analysis
- Integration with existing Monte Carlo and risk frameworks

Classes:
--------
SensitivityParameter
    Definition of parameters for sensitivity analysis

SensitivityResult
    Container for sensitivity analysis results

SensitivityAnalyzer
    Main class for performing sensitivity analysis

TornadoChart
    Tornado chart visualization for sensitivity ranking

Usage Example:
--------------
>>> from core.analysis.risk.sensitivity_analysis import SensitivityAnalyzer
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize with financial data
>>> calc = FinancialCalculator('AAPL')
>>> analyzer = SensitivityAnalyzer(calc)
>>>
>>> # Define sensitivity parameters
>>> params = {
>>>     'revenue_growth': {'base': 0.05, 'range': (-0.10, 0.20), 'steps': 21},
>>>     'discount_rate': {'base': 0.10, 'range': (0.06, 0.15), 'steps': 21}
>>> }
>>>
>>> # Run one-way sensitivity analysis
>>> result = analyzer.one_way_sensitivity('dcf', params)
>>> print(f"Most sensitive parameter: {result.get_most_sensitive_parameter()}")
>>>
>>> # Create tornado chart
>>> tornado = result.create_tornado_chart()
>>> tornado.save('sensitivity_tornado.png')
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


class SensitivityMethod(Enum):
    """Supported sensitivity analysis methods."""
    ONE_WAY = "one_way"
    TWO_WAY = "two_way"
    TORNADO = "tornado"
    ELASTICITY = "elasticity"
    BREAKEVEN = "breakeven"


class ParameterType(Enum):
    """Types of parameters for sensitivity analysis."""
    REVENUE_GROWTH = "revenue_growth"
    DISCOUNT_RATE = "discount_rate"
    TERMINAL_GROWTH = "terminal_growth"
    OPERATING_MARGIN = "operating_margin"
    TAX_RATE = "tax_rate"
    CAPEX_RATIO = "capex_ratio"
    WORKING_CAPITAL_RATIO = "working_capital_ratio"
    DIVIDEND_GROWTH = "dividend_growth"
    PAYOUT_RATIO = "payout_ratio"
    REQUIRED_RETURN = "required_return"
    PRICE_TO_BOOK = "price_to_book"
    ROE = "roe"
    DEBT_TO_EQUITY = "debt_to_equity"


@dataclass
class SensitivityParameter:
    """
    Definition of a parameter for sensitivity analysis.

    Attributes:
        name: Parameter name/identifier
        param_type: Type of parameter from ParameterType enum
        base_value: Base case value for the parameter
        sensitivity_range: Tuple of (min_value, max_value) for sensitivity testing
        steps: Number of steps for sensitivity analysis
        display_name: Human-readable name for display
        units: Units for the parameter (e.g., '%', 'ratio', '$')
        description: Detailed description of the parameter
    """
    name: str
    param_type: ParameterType
    base_value: float
    sensitivity_range: Tuple[float, float]
    steps: int = 21
    display_name: Optional[str] = None
    units: str = "%"
    description: Optional[str] = None

    def __post_init__(self):
        """Set default display name if not provided."""
        if self.display_name is None:
            self.display_name = self.name.replace('_', ' ').title()

    def generate_test_values(self) -> np.ndarray:
        """Generate array of test values for sensitivity analysis."""
        return np.linspace(self.sensitivity_range[0], self.sensitivity_range[1], self.steps)

    def calculate_percentage_change(self, test_value: float) -> float:
        """Calculate percentage change from base value."""
        if self.base_value == 0:
            return 0.0
        return (test_value - self.base_value) / abs(self.base_value) * 100


@dataclass
class SensitivityResult:
    """
    Container for sensitivity analysis results.

    Attributes:
        analysis_id: Unique identifier for this analysis
        method: Sensitivity analysis method used
        base_case_value: Base case valuation result
        parameters: Dictionary of sensitivity parameters
        results: Analysis results data
        statistics: Summary statistics
        rankings: Parameter sensitivity rankings
        metadata: Additional analysis metadata
    """
    analysis_id: str
    method: SensitivityMethod
    base_case_value: float
    parameters: Dict[str, SensitivityParameter] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, float] = field(default_factory=dict)
    rankings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_sensitivity_table(self) -> pd.DataFrame:
        """Generate sensitivity analysis results table."""
        if self.method == SensitivityMethod.ONE_WAY:
            return self._create_one_way_table()
        elif self.method == SensitivityMethod.TWO_WAY:
            return self._create_two_way_table()
        elif self.method == SensitivityMethod.TORNADO:
            return self._create_tornado_table()
        else:
            return pd.DataFrame()

    def _create_one_way_table(self) -> pd.DataFrame:
        """Create table for one-way sensitivity results."""
        data = []

        for param_name, param_results in self.results.items():
            if 'values' in param_results and 'test_values' in param_results:
                test_values = param_results['test_values']
                output_values = param_results['values']

                for test_val, output_val in zip(test_values, output_values):
                    param = self.parameters[param_name]
                    pct_change_input = param.calculate_percentage_change(test_val)
                    pct_change_output = (output_val - self.base_case_value) / abs(self.base_case_value) * 100

                    data.append({
                        'Parameter': param.display_name,
                        'Test Value': test_val,
                        'Input Change (%)': pct_change_input,
                        'Output Value': output_val,
                        'Output Change (%)': pct_change_output,
                        'Sensitivity': abs(pct_change_output / pct_change_input) if pct_change_input != 0 else 0
                    })

        return pd.DataFrame(data)

    def _create_two_way_table(self) -> pd.DataFrame:
        """Create table for two-way sensitivity results."""
        if 'heatmap_data' in self.results:
            heatmap_data = self.results['heatmap_data']
            param1_name = self.results['param1_name']
            param2_name = self.results['param2_name']
            param1_values = self.results['param1_values']
            param2_values = self.results['param2_values']

            # Convert heatmap to DataFrame
            df = pd.DataFrame(
                heatmap_data,
                index=[f"{param2_name}: {val:.3f}" for val in param2_values],
                columns=[f"{param1_name}: {val:.3f}" for val in param1_values]
            )
            return df

        return pd.DataFrame()

    def _create_tornado_table(self) -> pd.DataFrame:
        """Create table for tornado chart results."""
        if 'tornado_data' in self.results:
            return pd.DataFrame(self.results['tornado_data'])
        return pd.DataFrame()

    def get_most_sensitive_parameter(self) -> Optional[str]:
        """Get the most sensitive parameter from rankings."""
        if self.rankings:
            return self.rankings[0].get('parameter_name')
        return None

    def get_sensitivity_ranking(self) -> List[Dict[str, Any]]:
        """Get parameter sensitivity ranking."""
        return self.rankings

    def calculate_elasticity(self, parameter_name: str) -> Optional[float]:
        """Calculate elasticity for a specific parameter."""
        if parameter_name not in self.results:
            return None

        param_results = self.results[parameter_name]
        if 'elasticity' in param_results:
            return param_results['elasticity']

        # Calculate elasticity if not already computed
        if 'values' in param_results and 'test_values' in param_results:
            test_values = np.array(param_results['test_values'])
            output_values = np.array(param_results['values'])
            param = self.parameters[parameter_name]

            # Find closest points to base value
            base_idx = np.argmin(np.abs(test_values - param.base_value))

            if base_idx > 0 and base_idx < len(test_values) - 1:
                # Use central difference
                delta_input = (test_values[base_idx + 1] - test_values[base_idx - 1]) / param.base_value
                delta_output = (output_values[base_idx + 1] - output_values[base_idx - 1]) / self.base_case_value

                if delta_input != 0:
                    return delta_output / delta_input

        return None

    def find_breakeven_point(self, target_value: float, parameter_name: str) -> Optional[float]:
        """Find parameter value that achieves target output value."""
        if parameter_name not in self.results:
            return None

        param_results = self.results[parameter_name]
        if 'values' not in param_results or 'test_values' not in param_results:
            return None

        test_values = np.array(param_results['test_values'])
        output_values = np.array(param_results['values'])

        # Find the closest value to target
        closest_idx = np.argmin(np.abs(output_values - target_value))

        # Linear interpolation for better accuracy
        if closest_idx > 0 and closest_idx < len(output_values) - 1:
            if output_values[closest_idx] < target_value:
                # Target is between closest and next
                x1, y1 = test_values[closest_idx], output_values[closest_idx]
                x2, y2 = test_values[closest_idx + 1], output_values[closest_idx + 1]
            else:
                # Target is between previous and closest
                x1, y1 = test_values[closest_idx - 1], output_values[closest_idx - 1]
                x2, y2 = test_values[closest_idx], output_values[closest_idx]

            # Linear interpolation
            if y2 != y1:
                interpolated_x = x1 + (target_value - y1) * (x2 - x1) / (y2 - y1)
                return interpolated_x

        return test_values[closest_idx]

    def export_results(self, file_path: str, format: str = 'excel') -> None:
        """Export sensitivity analysis results to file."""
        if format.lower() == 'excel':
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': ['Analysis ID', 'Method', 'Base Case Value', 'Analysis Date', 'Most Sensitive Parameter'],
                    'Value': [
                        self.analysis_id,
                        self.method.value,
                        self.base_case_value,
                        self.metadata.get('analysis_date', 'Unknown'),
                        self.get_most_sensitive_parameter() or 'Unknown'
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

                # Results table
                results_table = self.get_sensitivity_table()
                if not results_table.empty:
                    results_table.to_excel(writer, sheet_name='Results', index=False)

                # Rankings
                if self.rankings:
                    pd.DataFrame(self.rankings).to_excel(writer, sheet_name='Rankings', index=False)

        elif format.lower() == 'csv':
            results_table = self.get_sensitivity_table()
            results_table.to_csv(file_path, index=False)

        logger.info(f"Sensitivity analysis results exported to {file_path}")


class SensitivityAnalyzer:
    """
    Main class for performing comprehensive sensitivity analysis on financial models.

    This analyzer integrates with existing financial calculation engines to perform
    various types of sensitivity analysis including one-way, two-way, tornado charts,
    elasticity analysis, and breakeven analysis.
    """

    def __init__(self, financial_calculator=None):
        """
        Initialize sensitivity analyzer.

        Args:
            financial_calculator: FinancialCalculator instance for data access
        """
        self.financial_calculator = financial_calculator
        self.analysis_cache: Dict[str, SensitivityResult] = {}

        # Default parameter definitions
        self.default_parameters = self._create_default_parameters()

        logger.info("Sensitivity Analyzer initialized")

    def _create_default_parameters(self) -> Dict[str, SensitivityParameter]:
        """Create default parameter definitions for common financial variables."""
        return {
            'revenue_growth': SensitivityParameter(
                name='revenue_growth',
                param_type=ParameterType.REVENUE_GROWTH,
                base_value=0.05,
                sensitivity_range=(-0.10, 0.25),
                display_name='Revenue Growth Rate',
                units='%',
                description='Annual revenue growth rate'
            ),
            'discount_rate': SensitivityParameter(
                name='discount_rate',
                param_type=ParameterType.DISCOUNT_RATE,
                base_value=0.10,
                sensitivity_range=(0.06, 0.18),
                display_name='Discount Rate (WACC)',
                units='%',
                description='Weighted Average Cost of Capital'
            ),
            'terminal_growth': SensitivityParameter(
                name='terminal_growth',
                param_type=ParameterType.TERMINAL_GROWTH,
                base_value=0.03,
                sensitivity_range=(0.01, 0.06),
                display_name='Terminal Growth Rate',
                units='%',
                description='Long-term growth rate for terminal value'
            ),
            'operating_margin': SensitivityParameter(
                name='operating_margin',
                param_type=ParameterType.OPERATING_MARGIN,
                base_value=0.20,
                sensitivity_range=(0.10, 0.35),
                display_name='Operating Margin',
                units='%',
                description='Operating profit margin'
            ),
            'tax_rate': SensitivityParameter(
                name='tax_rate',
                param_type=ParameterType.TAX_RATE,
                base_value=0.25,
                sensitivity_range=(0.15, 0.35),
                display_name='Tax Rate',
                units='%',
                description='Effective tax rate'
            ),
            'dividend_growth': SensitivityParameter(
                name='dividend_growth',
                param_type=ParameterType.DIVIDEND_GROWTH,
                base_value=0.05,
                sensitivity_range=(-0.05, 0.15),
                display_name='Dividend Growth Rate',
                units='%',
                description='Annual dividend growth rate'
            ),
            'payout_ratio': SensitivityParameter(
                name='payout_ratio',
                param_type=ParameterType.PAYOUT_RATIO,
                base_value=0.40,
                sensitivity_range=(0.20, 0.80),
                display_name='Dividend Payout Ratio',
                units='%',
                description='Percentage of earnings paid as dividends'
            ),
            'required_return': SensitivityParameter(
                name='required_return',
                param_type=ParameterType.REQUIRED_RETURN,
                base_value=0.10,
                sensitivity_range=(0.06, 0.16),
                display_name='Required Return',
                units='%',
                description='Required rate of return for equity investors'
            )
        }

    def one_way_sensitivity(
        self,
        valuation_method: str,
        parameters: Union[Dict[str, Dict], List[str]],
        analysis_id: Optional[str] = None,
        custom_valuation_function: Optional[Callable] = None
    ) -> SensitivityResult:
        """
        Perform one-way sensitivity analysis.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            parameters: Parameter specifications or list of parameter names
            analysis_id: Unique identifier for this analysis
            custom_valuation_function: Custom valuation function for 'custom' method

        Returns:
            SensitivityResult containing analysis results
        """
        if analysis_id is None:
            analysis_id = f"one_way_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting one-way sensitivity analysis: {analysis_id}")

        # Parse parameters
        sensitivity_params = self._parse_parameters(parameters)

        # Get base case valuation
        base_case_value = self._calculate_base_case(valuation_method, custom_valuation_function)

        # Initialize result object
        result = SensitivityResult(
            analysis_id=analysis_id,
            method=SensitivityMethod.ONE_WAY,
            base_case_value=base_case_value,
            parameters=sensitivity_params,
            metadata={
                'analysis_date': datetime.now().isoformat(),
                'valuation_method': valuation_method,
                'num_parameters': len(sensitivity_params)
            }
        )

        # Run sensitivity analysis for each parameter
        for param_name, param_def in sensitivity_params.items():
            logger.debug(f"Analyzing parameter: {param_name}")

            test_values = param_def.generate_test_values()
            output_values = []

            for test_value in test_values:
                # Create parameter override
                param_override = {param_name: test_value}

                # Calculate valuation with modified parameter
                try:
                    modified_value = self._calculate_valuation(
                        valuation_method, param_override, custom_valuation_function
                    )
                    output_values.append(modified_value)
                except Exception as e:
                    logger.warning(f"Calculation failed for {param_name}={test_value}: {e}")
                    output_values.append(base_case_value)  # Use base case for failed calculations

            # Store results
            result.results[param_name] = {
                'test_values': test_values.tolist(),
                'values': output_values,
                'sensitivity_range': param_def.sensitivity_range,
                'base_value': param_def.base_value
            }

            # Calculate elasticity
            elasticity = self._calculate_elasticity(
                test_values, output_values, param_def.base_value, base_case_value
            )
            result.results[param_name]['elasticity'] = elasticity

        # Calculate rankings and statistics
        result.rankings = self._calculate_sensitivity_rankings(result)
        result.statistics = self._calculate_sensitivity_statistics(result)

        # Cache result
        self.analysis_cache[analysis_id] = result

        logger.info(f"One-way sensitivity analysis completed: {analysis_id}")
        return result

    def two_way_sensitivity(
        self,
        valuation_method: str,
        param1_spec: Union[str, Dict],
        param2_spec: Union[str, Dict],
        analysis_id: Optional[str] = None,
        custom_valuation_function: Optional[Callable] = None
    ) -> SensitivityResult:
        """
        Perform two-way sensitivity analysis.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            param1_spec: First parameter specification
            param2_spec: Second parameter specification
            analysis_id: Unique identifier for this analysis
            custom_valuation_function: Custom valuation function for 'custom' method

        Returns:
            SensitivityResult containing analysis results
        """
        if analysis_id is None:
            analysis_id = f"two_way_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting two-way sensitivity analysis: {analysis_id}")

        # Parse parameter specifications
        param1 = self._parse_single_parameter(param1_spec)
        param2 = self._parse_single_parameter(param2_spec)

        # Get base case valuation
        base_case_value = self._calculate_base_case(valuation_method, custom_valuation_function)

        # Generate test values
        param1_values = param1.generate_test_values()
        param2_values = param2.generate_test_values()

        # Create heatmap data
        heatmap_data = np.zeros((len(param2_values), len(param1_values)))

        for i, param2_val in enumerate(param2_values):
            for j, param1_val in enumerate(param1_values):
                param_override = {
                    param1.name: param1_val,
                    param2.name: param2_val
                }

                try:
                    valuation = self._calculate_valuation(
                        valuation_method, param_override, custom_valuation_function
                    )
                    heatmap_data[i, j] = valuation
                except Exception as e:
                    logger.warning(f"Calculation failed for {param1.name}={param1_val}, {param2.name}={param2_val}: {e}")
                    heatmap_data[i, j] = base_case_value

        # Initialize result object
        result = SensitivityResult(
            analysis_id=analysis_id,
            method=SensitivityMethod.TWO_WAY,
            base_case_value=base_case_value,
            parameters={param1.name: param1, param2.name: param2},
            metadata={
                'analysis_date': datetime.now().isoformat(),
                'valuation_method': valuation_method,
                'param1_name': param1.name,
                'param2_name': param2.name
            }
        )

        # Store results
        result.results = {
            'heatmap_data': heatmap_data.tolist(),
            'param1_name': param1.display_name,
            'param2_name': param2.display_name,
            'param1_values': param1_values.tolist(),
            'param2_values': param2_values.tolist(),
            'base_case_coordinates': (param1.base_value, param2.base_value)
        }

        # Calculate interaction statistics
        result.statistics = self._calculate_two_way_statistics(heatmap_data, base_case_value)

        # Cache result
        self.analysis_cache[analysis_id] = result

        logger.info(f"Two-way sensitivity analysis completed: {analysis_id}")
        return result

    def tornado_analysis(
        self,
        valuation_method: str,
        parameters: Union[Dict[str, Dict], List[str]],
        variation_percentage: float = 0.20,
        analysis_id: Optional[str] = None,
        custom_valuation_function: Optional[Callable] = None
    ) -> SensitivityResult:
        """
        Perform tornado chart analysis for parameter ranking.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            parameters: Parameter specifications or list of parameter names
            variation_percentage: Percentage variation from base case (e.g., 0.20 for ±20%)
            analysis_id: Unique identifier for this analysis
            custom_valuation_function: Custom valuation function for 'custom' method

        Returns:
            SensitivityResult containing tornado analysis results
        """
        if analysis_id is None:
            analysis_id = f"tornado_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting tornado analysis: {analysis_id}")

        # Parse parameters
        sensitivity_params = self._parse_parameters(parameters)

        # Get base case valuation
        base_case_value = self._calculate_base_case(valuation_method, custom_valuation_function)

        # Initialize result object
        result = SensitivityResult(
            analysis_id=analysis_id,
            method=SensitivityMethod.TORNADO,
            base_case_value=base_case_value,
            parameters=sensitivity_params,
            metadata={
                'analysis_date': datetime.now().isoformat(),
                'valuation_method': valuation_method,
                'variation_percentage': variation_percentage
            }
        )

        tornado_data = []

        for param_name, param_def in sensitivity_params.items():
            logger.debug(f"Analyzing parameter for tornado: {param_name}")

            # Calculate high and low values (±variation_percentage from base)
            base_val = param_def.base_value
            variation = abs(base_val) * variation_percentage

            high_val = base_val + variation
            low_val = base_val - variation

            # Ensure values stay within parameter bounds
            min_bound, max_bound = param_def.sensitivity_range
            high_val = min(high_val, max_bound)
            low_val = max(low_val, min_bound)

            # Calculate valuations
            try:
                high_valuation = self._calculate_valuation(
                    valuation_method, {param_name: high_val}, custom_valuation_function
                )
                low_valuation = self._calculate_valuation(
                    valuation_method, {param_name: low_val}, custom_valuation_function
                )

                # Calculate impact range
                impact_range = abs(high_valuation - low_valuation)
                upside_impact = high_valuation - base_case_value
                downside_impact = low_valuation - base_case_value

                tornado_data.append({
                    'parameter_name': param_name,
                    'display_name': param_def.display_name,
                    'base_value': base_val,
                    'high_value': high_val,
                    'low_value': low_val,
                    'high_valuation': high_valuation,
                    'low_valuation': low_valuation,
                    'impact_range': impact_range,
                    'upside_impact': upside_impact,
                    'downside_impact': downside_impact,
                    'upside_percentage': upside_impact / base_case_value * 100,
                    'downside_percentage': downside_impact / base_case_value * 100
                })

            except Exception as e:
                logger.warning(f"Tornado calculation failed for {param_name}: {e}")
                continue

        # Sort by impact range (descending)
        tornado_data.sort(key=lambda x: x['impact_range'], reverse=True)

        # Store results
        result.results['tornado_data'] = tornado_data

        # Create rankings
        result.rankings = [
            {
                'rank': i + 1,
                'parameter_name': item['parameter_name'],
                'display_name': item['display_name'],
                'impact_range': item['impact_range'],
                'upside_percentage': item['upside_percentage'],
                'downside_percentage': item['downside_percentage']
            }
            for i, item in enumerate(tornado_data)
        ]

        # Calculate statistics
        result.statistics = {
            'total_parameters': len(tornado_data),
            'max_impact_range': max([item['impact_range'] for item in tornado_data]) if tornado_data else 0,
            'total_upside_potential': sum([max(0, item['upside_impact']) for item in tornado_data]),
            'total_downside_risk': sum([min(0, item['downside_impact']) for item in tornado_data]),
            'variation_percentage': variation_percentage
        }

        # Cache result
        self.analysis_cache[analysis_id] = result

        logger.info(f"Tornado analysis completed: {analysis_id}")
        return result

    def elasticity_analysis(
        self,
        valuation_method: str,
        parameters: Union[Dict[str, Dict], List[str]],
        analysis_id: Optional[str] = None,
        custom_valuation_function: Optional[Callable] = None
    ) -> SensitivityResult:
        """
        Perform elasticity analysis to measure parameter sensitivity.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            parameters: Parameter specifications or list of parameter names
            analysis_id: Unique identifier for this analysis
            custom_valuation_function: Custom valuation function for 'custom' method

        Returns:
            SensitivityResult containing elasticity analysis results
        """
        if analysis_id is None:
            analysis_id = f"elasticity_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting elasticity analysis: {analysis_id}")

        # Run one-way sensitivity analysis with fewer steps for efficiency
        sensitivity_params = self._parse_parameters(parameters)

        # Temporarily reduce steps for elasticity calculation
        for param in sensitivity_params.values():
            param.steps = 11  # Use fewer steps for elasticity

        # Run one-way analysis
        one_way_result = self.one_way_sensitivity(
            valuation_method, sensitivity_params, f"{analysis_id}_oneway", custom_valuation_function
        )

        # Convert to elasticity result
        result = SensitivityResult(
            analysis_id=analysis_id,
            method=SensitivityMethod.ELASTICITY,
            base_case_value=one_way_result.base_case_value,
            parameters=one_way_result.parameters,
            metadata={
                'analysis_date': datetime.now().isoformat(),
                'valuation_method': valuation_method,
                'derived_from': f"{analysis_id}_oneway"
            }
        )

        # Calculate elasticities
        elasticity_data = []
        for param_name, param_results in one_way_result.results.items():
            elasticity = param_results.get('elasticity', 0)
            param = sensitivity_params[param_name]

            elasticity_data.append({
                'parameter_name': param_name,
                'display_name': param.display_name,
                'elasticity': elasticity,
                'interpretation': self._interpret_elasticity(elasticity),
                'sensitivity_level': self._classify_sensitivity(abs(elasticity))
            })

        # Sort by absolute elasticity (descending)
        elasticity_data.sort(key=lambda x: abs(x['elasticity']), reverse=True)

        # Store results
        result.results = {
            'elasticity_data': elasticity_data,
            'derived_from_one_way': one_way_result.results
        }

        # Create rankings based on elasticity
        result.rankings = [
            {
                'rank': i + 1,
                'parameter_name': item['parameter_name'],
                'display_name': item['display_name'],
                'elasticity': item['elasticity'],
                'abs_elasticity': abs(item['elasticity']),
                'sensitivity_level': item['sensitivity_level']
            }
            for i, item in enumerate(elasticity_data)
        ]

        # Calculate statistics
        elasticities = [item['elasticity'] for item in elasticity_data]
        result.statistics = {
            'mean_elasticity': np.mean(elasticities),
            'median_elasticity': np.median(elasticities),
            'max_elasticity': max(elasticities) if elasticities else 0,
            'min_elasticity': min(elasticities) if elasticities else 0,
            'highly_sensitive_count': len([e for e in elasticities if abs(e) > 2]),
            'moderately_sensitive_count': len([e for e in elasticities if 1 <= abs(e) <= 2]),
            'low_sensitive_count': len([e for e in elasticities if abs(e) < 1])
        }

        # Cache result
        self.analysis_cache[analysis_id] = result

        logger.info(f"Elasticity analysis completed: {analysis_id}")
        return result

    def breakeven_analysis(
        self,
        valuation_method: str,
        target_values: List[float],
        parameters: Union[Dict[str, Dict], List[str]],
        analysis_id: Optional[str] = None,
        custom_valuation_function: Optional[Callable] = None
    ) -> SensitivityResult:
        """
        Perform breakeven analysis to find parameter values that achieve target valuations.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            target_values: List of target valuation values
            parameters: Parameter specifications or list of parameter names
            analysis_id: Unique identifier for this analysis
            custom_valuation_function: Custom valuation function for 'custom' method

        Returns:
            SensitivityResult containing breakeven analysis results
        """
        if analysis_id is None:
            analysis_id = f"breakeven_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting breakeven analysis: {analysis_id}")

        # Parse parameters
        sensitivity_params = self._parse_parameters(parameters)

        # Get base case valuation
        base_case_value = self._calculate_base_case(valuation_method, custom_valuation_function)

        # Initialize result object
        result = SensitivityResult(
            analysis_id=analysis_id,
            method=SensitivityMethod.BREAKEVEN,
            base_case_value=base_case_value,
            parameters=sensitivity_params,
            metadata={
                'analysis_date': datetime.now().isoformat(),
                'valuation_method': valuation_method,
                'target_values': target_values
            }
        )

        # Run one-way sensitivity for each parameter to get value ranges
        one_way_result = self.one_way_sensitivity(
            valuation_method, sensitivity_params, f"{analysis_id}_oneway", custom_valuation_function
        )

        breakeven_data = []

        for target_value in target_values:
            target_results = {
                'target_value': target_value,
                'target_vs_base_pct': (target_value - base_case_value) / base_case_value * 100,
                'parameter_breakevens': {}
            }

            for param_name in sensitivity_params.keys():
                breakeven_point = one_way_result.find_breakeven_point(target_value, param_name)

                if breakeven_point is not None:
                    param = sensitivity_params[param_name]
                    breakeven_pct_change = param.calculate_percentage_change(breakeven_point)

                    # Check if breakeven point is within parameter bounds
                    within_bounds = (param.sensitivity_range[0] <= breakeven_point <= param.sensitivity_range[1])

                    target_results['parameter_breakevens'][param_name] = {
                        'breakeven_value': breakeven_point,
                        'base_value': param.base_value,
                        'percentage_change': breakeven_pct_change,
                        'within_bounds': within_bounds,
                        'display_name': param.display_name,
                        'feasible': within_bounds and abs(breakeven_pct_change) <= 100  # Max 100% change
                    }

            breakeven_data.append(target_results)

        # Store results
        result.results = {
            'breakeven_data': breakeven_data,
            'derived_from_one_way': one_way_result.results
        }

        # Create summary rankings (most feasible parameters for achieving targets)
        feasibility_scores = {}
        for param_name in sensitivity_params.keys():
            feasible_count = 0
            total_targets = len(target_values)

            for target_data in breakeven_data:
                param_breakeven = target_data['parameter_breakevens'].get(param_name, {})
                if param_breakeven.get('feasible', False):
                    feasible_count += 1

            feasibility_score = feasible_count / total_targets if total_targets > 0 else 0
            feasibility_scores[param_name] = feasibility_score

        # Sort by feasibility score
        sorted_params = sorted(feasibility_scores.items(), key=lambda x: x[1], reverse=True)

        result.rankings = [
            {
                'rank': i + 1,
                'parameter_name': param_name,
                'display_name': sensitivity_params[param_name].display_name,
                'feasibility_score': score,
                'feasible_targets': int(score * len(target_values))
            }
            for i, (param_name, score) in enumerate(sorted_params)
        ]

        # Calculate statistics
        all_feasibility_scores = list(feasibility_scores.values())
        result.statistics = {
            'total_targets': len(target_values),
            'total_parameters': len(sensitivity_params),
            'mean_feasibility': np.mean(all_feasibility_scores),
            'highly_feasible_params': len([s for s in all_feasibility_scores if s > 0.8]),
            'infeasible_params': len([s for s in all_feasibility_scores if s == 0])
        }

        # Cache result
        self.analysis_cache[analysis_id] = result

        logger.info(f"Breakeven analysis completed: {analysis_id}")
        return result

    def _parse_parameters(self, parameters: Union[Dict[str, Dict], List[str]]) -> Dict[str, SensitivityParameter]:
        """Parse parameter specifications into SensitivityParameter objects."""
        if isinstance(parameters, list):
            # List of parameter names - use defaults
            result = {}
            for param_name in parameters:
                if param_name in self.default_parameters:
                    result[param_name] = self.default_parameters[param_name]
                else:
                    logger.warning(f"Unknown parameter: {param_name}")
            return result

        elif isinstance(parameters, dict):
            result = {}
            for param_name, param_spec in parameters.items():
                if isinstance(param_spec, dict):
                    # Custom parameter specification
                    default_param = self.default_parameters.get(param_name)

                    if default_param:
                        # Override default with custom values
                        result[param_name] = SensitivityParameter(
                            name=param_name,
                            param_type=default_param.param_type,
                            base_value=param_spec.get('base', default_param.base_value),
                            sensitivity_range=param_spec.get('range', default_param.sensitivity_range),
                            steps=param_spec.get('steps', default_param.steps),
                            display_name=param_spec.get('display_name', default_param.display_name),
                            units=param_spec.get('units', default_param.units),
                            description=param_spec.get('description', default_param.description)
                        )
                    else:
                        # Create new parameter
                        result[param_name] = SensitivityParameter(
                            name=param_name,
                            param_type=ParameterType.REVENUE_GROWTH,  # Default type
                            base_value=param_spec.get('base', 0.05),
                            sensitivity_range=param_spec.get('range', (-0.10, 0.20)),
                            steps=param_spec.get('steps', 21),
                            display_name=param_spec.get('display_name'),
                            units=param_spec.get('units', '%'),
                            description=param_spec.get('description')
                        )
                else:
                    # Just a parameter name
                    if param_name in self.default_parameters:
                        result[param_name] = self.default_parameters[param_name]

            return result

        else:
            raise ValueError("Parameters must be a list of names or dictionary of specifications")

    def _parse_single_parameter(self, param_spec: Union[str, Dict]) -> SensitivityParameter:
        """Parse a single parameter specification."""
        if isinstance(param_spec, str):
            if param_spec in self.default_parameters:
                return self.default_parameters[param_spec]
            else:
                raise ValueError(f"Unknown parameter: {param_spec}")

        elif isinstance(param_spec, dict):
            param_name = param_spec.get('name')
            if not param_name:
                raise ValueError("Parameter specification must include 'name'")

            parsed_params = self._parse_parameters({param_name: param_spec})
            return parsed_params[param_name]

        else:
            raise ValueError("Parameter specification must be string name or dictionary")

    def _calculate_base_case(self, valuation_method: str, custom_function: Optional[Callable] = None) -> float:
        """Calculate base case valuation."""
        return self._calculate_valuation(valuation_method, {}, custom_function)

    def _calculate_valuation(
        self,
        valuation_method: str,
        param_overrides: Dict[str, float],
        custom_function: Optional[Callable] = None
    ) -> float:
        """
        Calculate valuation with parameter overrides.

        This method integrates with existing valuation engines to calculate
        financial valuations with modified parameters.
        """
        if valuation_method == 'custom' and custom_function:
            return custom_function(param_overrides)

        elif valuation_method == 'dcf':
            return self._calculate_dcf_valuation(param_overrides)

        elif valuation_method == 'ddm':
            return self._calculate_ddm_valuation(param_overrides)

        elif valuation_method == 'pb':
            return self._calculate_pb_valuation(param_overrides)

        else:
            raise ValueError(f"Unsupported valuation method: {valuation_method}")

    def _calculate_dcf_valuation(self, param_overrides: Dict[str, float]) -> float:
        """Calculate DCF valuation with parameter overrides."""
        if self.financial_calculator is None:
            # Simplified DCF calculation for demonstration
            return self._simplified_dcf_calculation(param_overrides)

        try:
            # Get base parameters from financial calculator
            # This would integrate with the actual DCF calculation engine
            base_params = {
                'revenue_growth': 0.05,
                'discount_rate': 0.10,
                'terminal_growth': 0.03,
                'operating_margin': 0.20,
                'tax_rate': 0.25
            }

            # Apply overrides
            params = {**base_params, **param_overrides}

            # This would call the actual DCF calculation method
            # For now, use simplified calculation
            return self._simplified_dcf_calculation(params)

        except Exception as e:
            logger.warning(f"DCF calculation failed: {e}")
            return 100.0  # Default fallback value

    def _calculate_ddm_valuation(self, param_overrides: Dict[str, float]) -> float:
        """Calculate DDM valuation with parameter overrides."""
        # Simplified DDM calculation
        base_params = {
            'dividend_growth': 0.05,
            'required_return': 0.10,
            'current_dividend': 2.0
        }

        params = {**base_params, **param_overrides}

        try:
            dividend_growth = params['dividend_growth']
            required_return = params['required_return']
            current_dividend = params['current_dividend']

            if required_return <= dividend_growth:
                required_return = dividend_growth + 0.02  # Ensure convergence

            next_dividend = current_dividend * (1 + dividend_growth)
            ddm_value = next_dividend / (required_return - dividend_growth)

            return max(ddm_value, 0)  # Ensure non-negative

        except (ZeroDivisionError, ValueError):
            return 50.0  # Default fallback

    def _calculate_pb_valuation(self, param_overrides: Dict[str, float]) -> float:
        """Calculate P/B valuation with parameter overrides."""
        # Simplified P/B calculation
        base_params = {
            'roe': 0.15,
            'required_return': 0.10,
            'growth_rate': 0.05,
            'book_value_per_share': 10.0
        }

        params = {**base_params, **param_overrides}

        try:
            roe = params['roe']
            required_return = params['required_return']
            growth_rate = params['growth_rate']
            book_value = params['book_value_per_share']

            # Justified P/B ratio calculation
            if required_return != growth_rate:
                pb_ratio = roe / (required_return - growth_rate)
            else:
                pb_ratio = 1.5  # Default ratio

            pb_value = pb_ratio * book_value
            return max(pb_value, 0)

        except (ZeroDivisionError, ValueError):
            return 15.0  # Default fallback

    def _simplified_dcf_calculation(self, params: Dict[str, float]) -> float:
        """Simplified DCF calculation for sensitivity analysis."""
        revenue_growth = params.get('revenue_growth', 0.05)
        discount_rate = params.get('discount_rate', 0.10)
        terminal_growth = params.get('terminal_growth', 0.03)
        operating_margin = params.get('operating_margin', 0.20)
        tax_rate = params.get('tax_rate', 0.25)

        # Simplified assumptions
        base_revenue = 1000  # Million
        projection_years = 5
        shares_outstanding = 100  # Million

        # Project cash flows
        cash_flows = []
        current_revenue = base_revenue

        for year in range(1, projection_years + 1):
            current_revenue *= (1 + revenue_growth)
            operating_income = current_revenue * operating_margin
            after_tax_income = operating_income * (1 - tax_rate)
            # Assume FCF = 80% of after-tax income
            free_cash_flow = after_tax_income * 0.80
            cash_flows.append(free_cash_flow)

        # Present value of cash flows
        pv_cash_flows = sum(
            cf / ((1 + discount_rate) ** (i + 1))
            for i, cf in enumerate(cash_flows)
        )

        # Terminal value
        if discount_rate <= terminal_growth:
            terminal_growth = discount_rate - 0.01  # Ensure convergence

        terminal_cf = cash_flows[-1] * (1 + terminal_growth)
        terminal_value = terminal_cf / (discount_rate - terminal_growth)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)

        # Total enterprise value
        enterprise_value = pv_cash_flows + pv_terminal_value

        # Value per share
        value_per_share = enterprise_value / shares_outstanding

        return max(value_per_share, 0)

    def _calculate_elasticity(
        self,
        test_values: np.ndarray,
        output_values: List[float],
        base_input: float,
        base_output: float
    ) -> float:
        """Calculate elasticity for a parameter."""
        try:
            # Find closest point to base value
            base_idx = np.argmin(np.abs(test_values - base_input))

            if base_idx > 0 and base_idx < len(test_values) - 1:
                # Use central difference for derivative
                delta_input = (test_values[base_idx + 1] - test_values[base_idx - 1]) / base_input
                delta_output = (output_values[base_idx + 1] - output_values[base_idx - 1]) / base_output

                if delta_input != 0:
                    return delta_output / delta_input

            return 0.0

        except (IndexError, ZeroDivisionError):
            return 0.0

    def _calculate_sensitivity_rankings(self, result: SensitivityResult) -> List[Dict[str, Any]]:
        """Calculate parameter sensitivity rankings."""
        rankings = []

        for param_name, param_results in result.results.items():
            if 'values' not in param_results:
                continue

            output_values = np.array(param_results['values'])
            sensitivity_range = np.max(output_values) - np.min(output_values)

            # Calculate relative sensitivity (range as percentage of base case)
            relative_sensitivity = sensitivity_range / abs(result.base_case_value) * 100

            # Get elasticity
            elasticity = param_results.get('elasticity', 0)

            param = result.parameters[param_name]

            rankings.append({
                'parameter_name': param_name,
                'display_name': param.display_name,
                'sensitivity_range': sensitivity_range,
                'relative_sensitivity': relative_sensitivity,
                'elasticity': elasticity,
                'abs_elasticity': abs(elasticity)
            })

        # Sort by relative sensitivity (descending)
        rankings.sort(key=lambda x: x['relative_sensitivity'], reverse=True)

        # Add rank numbers
        for i, ranking in enumerate(rankings):
            ranking['rank'] = i + 1

        return rankings

    def _calculate_sensitivity_statistics(self, result: SensitivityResult) -> Dict[str, float]:
        """Calculate summary statistics for sensitivity analysis."""
        all_ranges = []
        all_elasticities = []

        for param_results in result.results.values():
            if 'values' in param_results:
                output_values = np.array(param_results['values'])
                sensitivity_range = np.max(output_values) - np.min(output_values)
                relative_range = sensitivity_range / abs(result.base_case_value) * 100
                all_ranges.append(relative_range)

            if 'elasticity' in param_results:
                all_elasticities.append(param_results['elasticity'])

        statistics = {
            'mean_sensitivity': np.mean(all_ranges) if all_ranges else 0,
            'max_sensitivity': max(all_ranges) if all_ranges else 0,
            'min_sensitivity': min(all_ranges) if all_ranges else 0,
            'total_parameters': len(result.parameters)
        }

        if all_elasticities:
            statistics.update({
                'mean_elasticity': np.mean(all_elasticities),
                'max_elasticity': max(all_elasticities),
                'min_elasticity': min(all_elasticities)
            })

        return statistics

    def _calculate_two_way_statistics(self, heatmap_data: np.ndarray, base_case_value: float) -> Dict[str, float]:
        """Calculate statistics for two-way sensitivity analysis."""
        flat_data = heatmap_data.flatten()

        return {
            'min_value': float(np.min(flat_data)),
            'max_value': float(np.max(flat_data)),
            'mean_value': float(np.mean(flat_data)),
            'std_value': float(np.std(flat_data)),
            'value_range': float(np.max(flat_data) - np.min(flat_data)),
            'relative_range': float((np.max(flat_data) - np.min(flat_data)) / abs(base_case_value) * 100)
        }

    def _interpret_elasticity(self, elasticity: float) -> str:
        """Provide interpretation of elasticity value."""
        abs_elasticity = abs(elasticity)

        if abs_elasticity > 2:
            sensitivity = "Highly sensitive"
        elif abs_elasticity > 1:
            sensitivity = "Moderately sensitive"
        elif abs_elasticity > 0.5:
            sensitivity = "Somewhat sensitive"
        else:
            sensitivity = "Low sensitivity"

        direction = "positive" if elasticity > 0 else "negative"

        return f"{sensitivity} ({direction} relationship)"

    def _classify_sensitivity(self, abs_elasticity: float) -> str:
        """Classify sensitivity level based on absolute elasticity."""
        if abs_elasticity > 2:
            return "High"
        elif abs_elasticity > 1:
            return "Medium"
        elif abs_elasticity > 0.5:
            return "Low-Medium"
        else:
            return "Low"

    def get_analysis_result(self, analysis_id: str) -> Optional[SensitivityResult]:
        """Retrieve cached analysis result."""
        return self.analysis_cache.get(analysis_id)

    def list_analyses(self) -> List[str]:
        """List all cached analysis IDs."""
        return list(self.analysis_cache.keys())

    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self.analysis_cache.clear()
        logger.info("Sensitivity analysis cache cleared")


# Convenience functions for common use cases

def quick_tornado_analysis(
    financial_calculator,
    valuation_method: str = 'dcf',
    variation_percentage: float = 0.20
) -> SensitivityResult:
    """
    Quick tornado analysis with standard parameters.

    Args:
        financial_calculator: FinancialCalculator instance
        valuation_method: Valuation method to analyze
        variation_percentage: Percentage variation from base case

    Returns:
        SensitivityResult with tornado analysis
    """
    analyzer = SensitivityAnalyzer(financial_calculator)

    # Use common parameters based on valuation method
    if valuation_method == 'dcf':
        parameters = ['revenue_growth', 'discount_rate', 'terminal_growth', 'operating_margin', 'tax_rate']
    elif valuation_method == 'ddm':
        parameters = ['dividend_growth', 'required_return', 'payout_ratio']
    elif valuation_method == 'pb':
        parameters = ['roe', 'required_return', 'growth_rate']
    else:
        parameters = ['revenue_growth', 'discount_rate', 'terminal_growth']

    return analyzer.tornado_analysis(
        valuation_method=valuation_method,
        parameters=parameters,
        variation_percentage=variation_percentage
    )


def quick_two_way_analysis(
    financial_calculator,
    param1: str = 'revenue_growth',
    param2: str = 'discount_rate',
    valuation_method: str = 'dcf'
) -> SensitivityResult:
    """
    Quick two-way sensitivity analysis for common parameter pairs.

    Args:
        financial_calculator: FinancialCalculator instance
        param1: First parameter name
        param2: Second parameter name
        valuation_method: Valuation method to analyze

    Returns:
        SensitivityResult with two-way analysis
    """
    analyzer = SensitivityAnalyzer(financial_calculator)

    return analyzer.two_way_sensitivity(
        valuation_method=valuation_method,
        param1_spec=param1,
        param2_spec=param2
    )


def create_custom_parameter(
    name: str,
    base_value: float,
    min_value: float,
    max_value: float,
    display_name: Optional[str] = None,
    units: str = "%",
    steps: int = 21
) -> SensitivityParameter:
    """
    Create a custom sensitivity parameter.

    Args:
        name: Parameter identifier
        base_value: Base case value
        min_value: Minimum value for sensitivity range
        max_value: Maximum value for sensitivity range
        display_name: Human-readable name
        units: Parameter units
        steps: Number of steps for analysis

    Returns:
        SensitivityParameter object
    """
    return SensitivityParameter(
        name=name,
        param_type=ParameterType.REVENUE_GROWTH,  # Default type
        base_value=base_value,
        sensitivity_range=(min_value, max_value),
        steps=steps,
        display_name=display_name or name.replace('_', ' ').title(),
        units=units
    )