"""
Comprehensive Risk Analysis Example
===================================

This example demonstrates the complete risk analysis workflow using the integrated
Monte Carlo simulation engine with DCF, DDM, and P/B valuation models.

Features Demonstrated
--------------------
- Monte Carlo DCF simulation with risk assessment
- Dividend Discount Model uncertainty analysis
- Price-to-Book ratio Monte Carlo analysis
- Portfolio-level Value at Risk calculation
- Scenario analysis and stress testing
- Performance optimization with parallel processing
- Comprehensive risk reporting and visualization

Usage
-----
Run this script to see a complete risk analysis workflow:
    python tools/risk_analysis_example.py

Requirements
-----------
- Financial data for a company (Excel files or API access)
- All valuation modules properly configured
- Sufficient computational resources for Monte Carlo simulations
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
import time
from pathlib import Path

# Import core modules
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.statistics.monte_carlo_engine import (
    MonteCarloEngine,
    ParameterDistribution,
    DistributionType,
    quick_dcf_simulation,
    create_standard_scenarios
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RiskAnalysisWorkflow:
    """Complete risk analysis workflow demonstration."""

    def __init__(self, ticker_symbol: str, data_path: str = None):
        """
        Initialize risk analysis workflow.

        Args:
            ticker_symbol: Stock ticker symbol
            data_path: Path to financial data (optional)
        """
        self.ticker_symbol = ticker_symbol
        self.data_path = data_path
        self.financial_calculator = None
        self.monte_carlo_engine = None
        self.results = {}

        logger.info(f"Initializing risk analysis for {ticker_symbol}")

    def setup_financial_data(self):
        """Setup financial calculator with data."""
        try:
            if self.data_path:
                self.financial_calculator = FinancialCalculator(self.data_path)
                self.financial_calculator.load_financial_data()
            else:
                # Use API-based data loading
                self.financial_calculator = FinancialCalculator(self.ticker_symbol)
                self.financial_calculator.load_financial_data()

            logger.info(f"Financial data loaded successfully for {self.ticker_symbol}")

        except Exception as e:
            logger.error(f"Failed to load financial data: {e}")
            raise

    def setup_monte_carlo_engine(self):
        """Setup Monte Carlo engine with performance optimization."""
        self.monte_carlo_engine = MonteCarloEngine(self.financial_calculator)

        # Configure for optimal performance
        self.monte_carlo_engine.configure_performance(
            use_parallel_processing=True,
            max_workers=None,  # Use all available CPU cores
            chunk_size=2000,   # Larger chunks for better performance
            use_gpu_acceleration=False  # Future feature
        )

        logger.info("Monte Carlo engine configured with parallel processing")

    def run_dcf_risk_analysis(self, num_simulations: int = 10000):
        """Run comprehensive DCF risk analysis."""
        logger.info(f"Running DCF Monte Carlo simulation with {num_simulations:,} iterations...")

        start_time = time.time()

        # Run DCF Monte Carlo simulation
        dcf_result = self.monte_carlo_engine.simulate_dcf_valuation(
            num_simulations=num_simulations,
            revenue_growth_volatility=0.15,  # 15% volatility in revenue growth
            discount_rate_volatility=0.02,   # 2% volatility in discount rate
            terminal_growth_volatility=0.01, # 1% volatility in terminal growth
            margin_volatility=0.05,          # 5% volatility in margins
            random_state=42  # For reproducible results
        )

        execution_time = time.time() - start_time
        sims_per_second = num_simulations / execution_time

        logger.info(f"DCF simulation completed in {execution_time:.2f}s ({sims_per_second:.0f} sims/sec)")

        # Store results
        self.results['dcf'] = dcf_result

        # Generate summary statistics
        summary = self._generate_dcf_summary(dcf_result)
        self.results['dcf_summary'] = summary

        logger.info(f"DCF Risk Analysis Summary:")
        logger.info(f"  Mean Value: ${summary['mean_value']:.2f}")
        logger.info(f"  95% Confidence Interval: ${summary['ci_95_lower']:.2f} - ${summary['ci_95_upper']:.2f}")
        logger.info(f"  Value at Risk (5%): ${summary['var_5']:.2f}")
        logger.info(f"  Upside Potential (95%): ${summary['upside_95']:.2f}")
        logger.info(f"  Probability of Loss: {summary['prob_loss']:.1%}")

        return dcf_result

    def run_ddm_risk_analysis(self, num_simulations: int = 5000):
        """Run DDM risk analysis for dividend-paying stocks."""
        logger.info(f"Running DDM Monte Carlo simulation with {num_simulations:,} iterations...")

        try:
            ddm_result = self.monte_carlo_engine.simulate_dividend_discount_model(
                num_simulations=num_simulations,
                dividend_growth_volatility=0.20,  # 20% volatility in dividend growth
                required_return_volatility=0.02,  # 2% volatility in required return
                payout_ratio_volatility=0.10,     # 10% volatility in payout ratio
                random_state=42
            )

            self.results['ddm'] = ddm_result

            # Generate summary
            summary = self._generate_ddm_summary(ddm_result)
            self.results['ddm_summary'] = summary

            logger.info(f"DDM Risk Analysis Summary:")
            logger.info(f"  Mean Value: ${summary['mean_value']:.2f}")
            logger.info(f"  Valid Simulations: {summary['valid_simulations']:,}")
            logger.info(f"  VaR (5%): ${summary['var_5']:.2f}")

            return ddm_result

        except Exception as e:
            logger.warning(f"DDM analysis failed: {e}")
            return None

    def run_pb_risk_analysis(self, num_simulations: int = 5000):
        """Run P/B risk analysis."""
        logger.info(f"Running P/B Monte Carlo simulation with {num_simulations:,} iterations...")

        try:
            pb_result = self.monte_carlo_engine.simulate_pb_valuation(
                num_simulations=num_simulations,
                pb_ratio_volatility=0.25,           # 25% volatility in P/B ratio
                book_value_growth_volatility=0.10,  # 10% volatility in book value growth
                roe_volatility=0.15,                # 15% volatility in ROE
                random_state=42
            )

            self.results['pb'] = pb_result

            # Generate summary
            summary = self._generate_pb_summary(pb_result)
            self.results['pb_summary'] = summary

            logger.info(f"P/B Risk Analysis Summary:")
            logger.info(f"  Mean Value: ${summary['mean_value']:.2f}")
            logger.info(f"  VaR (5%): ${summary['var_5']:.2f}")

            return pb_result

        except Exception as e:
            logger.warning(f"P/B analysis failed: {e}")
            return None

    def run_scenario_analysis(self):
        """Run comprehensive scenario analysis."""
        logger.info("Running scenario analysis...")

        # Create standard scenarios
        scenarios = create_standard_scenarios()

        # Add custom scenarios
        scenarios.update({
            'High Inflation': {
                'revenue_growth': 0.03,
                'discount_rate': 0.14,
                'terminal_growth': 0.02,
                'operating_margin': 0.18
            },
            'Economic Boom': {
                'revenue_growth': 0.20,
                'discount_rate': 0.09,
                'terminal_growth': 0.05,
                'operating_margin': 0.25
            }
        })

        # Run scenario analysis
        scenario_results = self.monte_carlo_engine.run_scenario_analysis(
            scenarios, base_valuation_method='dcf'
        )

        self.results['scenarios'] = scenario_results

        # Log scenario results
        logger.info("Scenario Analysis Results:")
        for scenario_name, value in scenario_results.items():
            if value is not None:
                logger.info(f"  {scenario_name}: ${value:.2f}")
            else:
                logger.warning(f"  {scenario_name}: Failed")

        return scenario_results

    def calculate_portfolio_var(self):
        """Calculate portfolio-level VaR if multiple assets are analyzed."""
        if len(self.results) < 2:
            logger.info("Portfolio VaR requires multiple assets - skipping")
            return None

        logger.info("Calculating portfolio Value at Risk...")

        try:
            # Example portfolio weights (would be user-defined in practice)
            portfolio_weights = {
                'dcf': 0.6,  # 60% weight based on DCF
                'ddm': 0.4   # 40% weight based on DDM
            }

            # Prepare simulation results for portfolio calculation
            individual_simulations = {}
            if 'dcf' in self.results:
                individual_simulations['dcf'] = self.results['dcf']
            if 'ddm' in self.results:
                individual_simulations['ddm'] = self.results['ddm']

            if len(individual_simulations) >= 2:
                portfolio_var = self.monte_carlo_engine.calculate_portfolio_var(
                    portfolio_weights=portfolio_weights,
                    individual_simulations=individual_simulations,
                    confidence_level=0.05
                )

                self.results['portfolio_var'] = portfolio_var

                logger.info(f"Portfolio VaR Analysis:")
                logger.info(f"  Portfolio VaR (5%): ${portfolio_var['portfolio_var']:.2f}")
                logger.info(f"  Portfolio CVaR (5%): ${portfolio_var['portfolio_cvar']:.2f}")
                logger.info(f"  Portfolio Mean: ${portfolio_var['portfolio_mean']:.2f}")

                return portfolio_var

        except Exception as e:
            logger.warning(f"Portfolio VaR calculation failed: {e}")
            return None

    def generate_risk_report(self):
        """Generate comprehensive risk analysis report."""
        logger.info("Generating comprehensive risk report...")

        report = {
            'ticker_symbol': self.ticker_symbol,
            'analysis_date': datetime.now().isoformat(),
            'summary': {},
            'detailed_results': self.results
        }

        # Compile summary statistics
        if 'dcf' in self.results:
            report['summary']['dcf'] = self.results['dcf_summary']

        if 'ddm' in self.results:
            report['summary']['ddm'] = self.results['ddm_summary']

        if 'pb' in self.results:
            report['summary']['pb'] = self.results['pb_summary']

        if 'scenarios' in self.results:
            report['summary']['scenarios'] = self.results['scenarios']

        if 'portfolio_var' in self.results:
            report['summary']['portfolio_var'] = self.results['portfolio_var']

        # Save report to file
        report_path = Path(f"risk_analysis_report_{self.ticker_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        try:
            import json
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Risk analysis report saved to: {report_path}")

        except Exception as e:
            logger.warning(f"Failed to save report: {e}")

        return report

    def visualize_results(self):
        """Create risk analysis visualizations."""
        logger.info("Creating risk analysis visualizations...")

        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'Risk Analysis for {self.ticker_symbol}', fontsize=16)

            # DCF distribution plot
            if 'dcf' in self.results:
                self._plot_value_distribution(axes[0, 0], self.results['dcf'], 'DCF Valuation Distribution')

            # DDM distribution plot
            if 'ddm' in self.results:
                self._plot_value_distribution(axes[0, 1], self.results['ddm'], 'DDM Valuation Distribution')

            # P/B distribution plot
            if 'pb' in self.results:
                self._plot_value_distribution(axes[1, 0], self.results['pb'], 'P/B Valuation Distribution')

            # Scenario analysis plot
            if 'scenarios' in self.results:
                self._plot_scenario_analysis(axes[1, 1], self.results['scenarios'])

            plt.tight_layout()
            plt.savefig(f'risk_analysis_{self.ticker_symbol}.png', dpi=300, bbox_inches='tight')
            logger.info(f"Risk analysis charts saved to: risk_analysis_{self.ticker_symbol}.png")

        except Exception as e:
            logger.warning(f"Visualization failed: {e}")

    def _generate_dcf_summary(self, result):
        """Generate DCF summary statistics."""
        return {
            'mean_value': result.statistics['mean'],
            'median_value': result.statistics['median'],
            'std_dev': result.statistics['std'],
            'ci_95_lower': result.percentiles['ci_95'][0],
            'ci_95_upper': result.percentiles['ci_95'][1],
            'var_5': result.risk_metrics.var_5,
            'cvar_5': result.risk_metrics.cvar_5,
            'upside_95': result.risk_metrics.upside_potential,
            'prob_loss': result.risk_metrics.probability_of_loss,
            'num_simulations': result.statistics['count']
        }

    def _generate_ddm_summary(self, result):
        """Generate DDM summary statistics."""
        return {
            'mean_value': result.statistics['mean'],
            'median_value': result.statistics['median'],
            'var_5': result.risk_metrics.var_5,
            'valid_simulations': result.parameters.get('valid_simulations', 0),
            'total_simulations': result.parameters.get('num_simulations', 0)
        }

    def _generate_pb_summary(self, result):
        """Generate P/B summary statistics."""
        return {
            'mean_value': result.statistics['mean'],
            'median_value': result.statistics['median'],
            'var_5': result.risk_metrics.var_5,
            'num_simulations': result.statistics['count']
        }

    def _plot_value_distribution(self, ax, result, title):
        """Plot value distribution with risk metrics."""
        values = result.values
        ax.hist(values, bins=50, alpha=0.7, density=True, color='skyblue', edgecolor='black')

        # Add risk lines
        ax.axvline(result.statistics['mean'], color='green', linestyle='--', label=f"Mean: ${result.statistics['mean']:.2f}")
        ax.axvline(result.risk_metrics.var_5, color='red', linestyle='--', label=f"VaR(5%): ${result.risk_metrics.var_5:.2f}")
        ax.axvline(result.risk_metrics.upside_potential, color='orange', linestyle='--', label=f"95th %ile: ${result.risk_metrics.upside_potential:.2f}")

        ax.set_title(title)
        ax.set_xlabel('Value per Share ($)')
        ax.set_ylabel('Probability Density')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_scenario_analysis(self, ax, scenarios):
        """Plot scenario analysis results."""
        scenario_names = list(scenarios.keys())
        scenario_values = [v for v in scenarios.values() if v is not None]

        if scenario_values:
            colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(scenario_values)))
            bars = ax.bar(range(len(scenario_values)), scenario_values, color=colors)

            ax.set_title('Scenario Analysis Results')
            ax.set_xlabel('Scenarios')
            ax.set_ylabel('Valuation ($)')
            ax.set_xticks(range(len(scenario_names)))
            ax.set_xticklabels(scenario_names, rotation=45)
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar, value in zip(bars, scenario_values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'${value:.0f}', ha='center', va='bottom')

    def run_complete_analysis(self):
        """Run the complete risk analysis workflow."""
        try:
            logger.info(f"Starting complete risk analysis for {self.ticker_symbol}")

            # Setup
            self.setup_financial_data()
            self.setup_monte_carlo_engine()

            # Run individual analyses
            self.run_dcf_risk_analysis(num_simulations=15000)
            self.run_ddm_risk_analysis(num_simulations=8000)
            self.run_pb_risk_analysis(num_simulations=8000)

            # Run scenario and portfolio analysis
            self.run_scenario_analysis()
            self.calculate_portfolio_var()

            # Generate outputs
            report = self.generate_risk_report()
            self.visualize_results()

            logger.info("Complete risk analysis finished successfully")
            return report

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            raise


def main():
    """Main function to demonstrate risk analysis workflow."""
    # Example usage with Microsoft (MSFT)
    ticker = "MSFT"
    data_path = None  # Use API data, or specify path to Excel files

    # Create and run risk analysis
    risk_analysis = RiskAnalysisWorkflow(ticker, data_path)

    try:
        # Run complete analysis
        report = risk_analysis.run_complete_analysis()

        print("\n" + "="*80)
        print("RISK ANALYSIS COMPLETE")
        print("="*80)
        print(f"Ticker: {ticker}")
        print(f"Analysis Date: {report['analysis_date']}")

        if 'dcf' in report['summary']:
            dcf_summary = report['summary']['dcf']
            print(f"\nDCF Analysis:")
            print(f"  Mean Value: ${dcf_summary['mean_value']:.2f}")
            print(f"  95% CI: ${dcf_summary['ci_95_lower']:.2f} - ${dcf_summary['ci_95_upper']:.2f}")
            print(f"  VaR (5%): ${dcf_summary['var_5']:.2f}")

        if 'scenarios' in report['summary']:
            print(f"\nScenario Analysis:")
            for scenario, value in report['summary']['scenarios'].items():
                if value:
                    print(f"  {scenario}: ${value:.2f}")

        print(f"\nReports and charts saved to current directory.")

    except Exception as e:
        print(f"Error running risk analysis: {e}")
        logger.exception("Full error details:")


if __name__ == "__main__":
    main()