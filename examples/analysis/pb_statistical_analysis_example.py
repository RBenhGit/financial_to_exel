"""
P/B Statistical Analysis Example - Advanced Statistical Features Demo
===================================================================

This example demonstrates the advanced statistical analysis capabilities
for P/B trends, market cycles, and volatility assessment implemented in Task #35.

Features Demonstrated:
- Advanced trend detection with statistical significance
- Market cycle detection and regime analysis  
- Volatility assessment and risk scoring
- Correlation analysis capabilities
- Enhanced P/B analysis integration
- Comprehensive reporting and visualization

Usage:
------
python examples/analysis/pb_statistical_analysis_example.py

Requirements:
- Historical financial data (mock data generated if not available)
- Optional: matplotlib for visualizations
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import warnings

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib not available - visualizations will be skipped")
    PLOTTING_AVAILABLE = False

# Import our P/B analysis modules
from core.analysis.pb.pb_statistical_analysis import (
    PBStatisticalAnalysisEngine,
    create_statistical_analysis_report,
    validate_statistical_analysis_inputs
)
from core.analysis.pb.pb_enhanced_analysis import (
    EnhancedPBAnalysisEngine,
    create_enhanced_analysis_report,
    quick_pb_analysis
)
from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    PBDataPoint
)
from core.data_sources.data_sources import DataSourceResponse


class StatisticalAnalysisDemo:
    """Demo class for P/B statistical analysis features."""
    
    def __init__(self):
        """Initialize the demo."""
        self.statistical_engine = PBStatisticalAnalysisEngine()
        self.enhanced_engine = EnhancedPBAnalysisEngine()
        self.historical_engine = PBHistoricalAnalysisEngine()
        
        logger.info("P/B Statistical Analysis Demo initialized")
    
    def generate_demo_data(self, 
                          ticker: str = "DEMO",
                          scenario: str = "mixed") -> DataSourceResponse:
        """
        Generate demonstration data with different market scenarios.
        
        Args:
            ticker (str): Ticker symbol for demo
            scenario (str): Market scenario - "bull", "bear", "volatile", "mixed"
            
        Returns:
            DataSourceResponse: Mock data response for analysis
        """
        logger.info(f"Generating demo data for scenario: {scenario}")
        
        periods = 60  # 5 years of monthly data
        np.random.seed(42)  # For reproducible results
        
        # Generate base data
        pb_data = []
        base_pb = 1.5
        base_book_value = 25.0
        
        for i in range(periods):
            date = datetime.now() - timedelta(days=30 * (periods - i - 1))
            
            # Apply scenario-specific patterns
            if scenario == "bull":
                # Strong upward trend with moderate volatility
                trend_component = base_pb * (1 + 0.6 * (i / periods))
                noise = np.random.normal(0, 0.15 * base_pb)
                cycle_component = 0.2 * np.sin(2 * np.pi * i / 18)  # 18-month cycles
                
            elif scenario == "bear":
                # Downward trend with increasing volatility
                trend_component = base_pb * (1 - 0.4 * (i / periods))
                noise = np.random.normal(0, 0.25 * base_pb * (1 + i / periods))
                cycle_component = 0.1 * np.sin(2 * np.pi * i / 24)
                
            elif scenario == "volatile":
                # High volatility with regime changes
                if i < periods // 3:
                    trend_component = base_pb * (1 + 0.3 * (i / (periods // 3)))
                    vol_factor = 0.4
                elif i < 2 * periods // 3:
                    trend_component = base_pb * 1.3 * (1 - 0.5 * ((i - periods // 3) / (periods // 3)))
                    vol_factor = 0.6
                else:
                    trend_component = base_pb * 0.8 * (1 + 0.4 * ((i - 2 * periods // 3) / (periods // 3)))
                    vol_factor = 0.3
                
                noise = np.random.normal(0, vol_factor * base_pb)
                cycle_component = 0.3 * np.sin(2 * np.pi * i / 12)
                
            else:  # mixed scenario
                # Mixed patterns with multiple cycles
                trend_component = base_pb * (1 + 0.2 * np.sin(2 * np.pi * i / periods))
                noise = np.random.normal(0, 0.2 * base_pb)
                cycle_component = (0.2 * np.sin(2 * np.pi * i / 12) + 
                                 0.1 * np.sin(2 * np.pi * i / 36))
            
            pb_ratio = max(0.1, trend_component + cycle_component + noise)
            
            # Generate corresponding financial metrics
            book_value = base_book_value + np.random.normal(0, 1.0)
            market_price = pb_ratio * book_value
            market_cap = market_price * 1000000  # 1M shares
            
            pb_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'pb_ratio': pb_ratio,
                'book_value_per_share': book_value,
                'market_price': market_price,
                'market_cap': market_cap,
                'shares_outstanding': 1000000
            })
        
        # Create mock financial statements
        mock_data = {
            'ticker': ticker,
            'company_name': f"{ticker} Corporation",
            'pb_historical_data': pb_data,
            'balance_sheets': [{'date': pb_data[-1]['date'], 'total_equity': 25000000}],  # Mock data
            'income_statements': [{'date': pb_data[-1]['date'], 'net_income': 2000000}],
            'cash_flows': [{'date': pb_data[-1]['date'], 'free_cash_flow': 1500000}]
        }
        
        return DataSourceResponse(
            success=True,
            data=mock_data,
            source_type="demo",
            timestamp=datetime.now().isoformat()
        )
    
    def run_statistical_analysis_demo(self, scenario: str = "mixed"):
        """
        Run comprehensive statistical analysis demonstration.
        
        Args:
            scenario (str): Market scenario to demonstrate
        """
        print(f"\n{'='*80}")
        print(f"P/B STATISTICAL ANALYSIS DEMO - {scenario.upper()} MARKET SCENARIO")
        print(f"{'='*80}")
        
        try:
            # Generate demo data
            response = self.generate_demo_data(scenario=scenario)
            current_book_value = 25.50
            current_price = 35.75
            
            print(f"\n📊 Demo Data Generated:")
            print(f"   Ticker: {response.data['ticker']}")
            print(f"   Data Points: {len(response.data['pb_historical_data'])}")
            print(f"   Current Book Value: ${current_book_value:.2f}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Current P/B Ratio: {current_price/current_book_value:.2f}")
            
            # Step 1: Historical Analysis
            print(f"\n🔍 Step 1: Historical P/B Analysis")
            historical_result = self.historical_engine.analyze_historical_performance(response, years=5)
            
            if historical_result.success:
                print(f"   ✅ Historical analysis completed")
                print(f"   Data Quality Score: {historical_result.quality_metrics.overall_score:.2f}")
                print(f"   Mean P/B: {historical_result.statistics.mean_pb:.2f}")
                print(f"   P/B Volatility: {historical_result.statistics.std_pb:.2f}")
            else:
                print(f"   ❌ Historical analysis failed: {historical_result.error_message}")
                return
            
            # Step 2: Statistical Analysis
            print(f"\n📈 Step 2: Advanced Statistical Analysis")
            statistical_result = self.statistical_engine.analyze_pb_statistics(historical_result)
            
            if statistical_result.success:
                print(f"   ✅ Statistical analysis completed")
                self._display_statistical_results(statistical_result)
            else:
                print(f"   ❌ Statistical analysis failed: {statistical_result.error_message}")
                return
            
            # Step 3: Enhanced Integrated Analysis
            print(f"\n🚀 Step 3: Enhanced Integrated Analysis")
            enhanced_result = self.enhanced_engine.perform_complete_analysis(
                response, current_book_value, current_price, years=5
            )
            
            if enhanced_result.success:
                print(f"   ✅ Enhanced analysis completed")
                self._display_enhanced_results(enhanced_result)
            else:
                print(f"   ❌ Enhanced analysis failed: {enhanced_result.error_message}")
                return
            
            # Step 4: Generate Reports
            print(f"\n📄 Step 4: Generate Comprehensive Reports")
            self._generate_reports(statistical_result, enhanced_result)
            
            # Step 5: Visualizations (if available)
            if PLOTTING_AVAILABLE:
                print(f"\n📊 Step 5: Generate Visualizations")
                self._create_visualizations(response, statistical_result, enhanced_result)
            else:
                print(f"\n⚠️  Step 5: Visualizations skipped (matplotlib not available)")
            
            print(f"\n✅ Demo completed successfully for {scenario} scenario!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {str(e)}")
    
    def _display_statistical_results(self, result):
        """Display statistical analysis results."""
        print(f"\n   📊 Trend Analysis:")
        if result.trend_analysis:
            trend = result.trend_analysis
            print(f"      Direction: {trend.trend_direction}")
            print(f"      Strength: {trend.trend_strength:.3f}")
            print(f"      Statistical Significance: {trend.statistical_significance:.3f}")
            print(f"      R-squared: {trend.r_squared:.3f}")
            print(f"      Trend Consistency: {trend.trend_consistency:.3f}")
            
            if trend.trend_patterns:
                print(f"      Patterns: {', '.join(trend.trend_patterns)}")
        
        print(f"\n   🔄 Market Cycle Analysis:")
        if result.cycle_analysis:
            cycle = result.cycle_analysis
            print(f"      Cycles Detected: {cycle.cycles_detected}")
            print(f"      Current Position: {cycle.current_cycle_position}")
            print(f"      Current Regime: {cycle.current_regime}")
            if cycle.avg_cycle_duration_months > 0:
                print(f"      Avg Cycle Duration: {cycle.avg_cycle_duration_months:.1f} months")
        
        print(f"\n   ⚡ Volatility Assessment:")
        if result.volatility_analysis:
            vol = result.volatility_analysis
            print(f"      Historical Volatility: {vol.historical_volatility:.3f}")
            print(f"      Overall Risk Score: {vol.overall_risk_score:.3f}")
            print(f"      Current Vol Regime: {vol.current_vol_regime}")
            print(f"      Maximum Drawdown: {vol.maximum_drawdown:.3f}")
            print(f"      Volatility Trend: {vol.volatility_trend}")
        
        print(f"\n   🎯 Market Timing Signal:")
        print(f"      Signal: {result.market_timing_signal}")
        print(f"      Signal Strength: {result.signal_strength:.3f}")
        print(f"      Statistical Confidence: {result.statistical_confidence:.3f}")
    
    def _display_enhanced_results(self, result):
        """Display enhanced analysis results."""
        print(f"\n   💡 Investment Recommendation:")
        print(f"      Recommendation: {result.investment_recommendation}")
        print(f"      Confidence: {result.recommendation_confidence:.3f}")
        print(f"      Risk Assessment: {result.risk_assessment}")
        
        print(f"\n   📊 Key Metrics:")
        if result.fair_value_estimate:
            print(f"      Fair Value Estimate: ${result.fair_value_estimate:.2f}")
        if result.upside_potential:
            print(f"      Upside Potential: {result.upside_potential:.1%}")
        if result.downside_risk:
            print(f"      Downside Risk: {result.downside_risk:.1%}")
        
        print(f"\n   ⏱️  Timing & Positioning:")
        print(f"      Market Timing Score: {result.market_timing_score:.3f}")
        print(f"      Position Sizing Score: {result.position_sizing_score:.3f}")
        print(f"      Holding Period: {result.holding_period_estimate}")
        
        print(f"\n   🎯 Action Recommendations:")
        for i, rec in enumerate(result.action_recommendations[:3], 1):
            print(f"      {i}. {rec}")
        
        if result.analysis_warnings:
            print(f"\n   ⚠️  Warnings:")
            for warning in result.analysis_warnings[:2]:
                print(f"      • {warning}")
    
    def _generate_reports(self, statistical_result, enhanced_result):
        """Generate comprehensive analysis reports."""
        try:
            # Statistical analysis report
            stats_report = create_statistical_analysis_report(statistical_result)
            print(f"   📈 Statistical Analysis Report Generated")
            print(f"      Trend Direction: {stats_report['trend_analysis']['direction']}")
            print(f"      Market Timing: {stats_report['market_timing']['signal']}")
            
            # Enhanced analysis report
            enhanced_report = create_enhanced_analysis_report(enhanced_result)
            print(f"   🚀 Enhanced Analysis Report Generated")
            print(f"      Investment Signal: {enhanced_report['executive_summary']['investment_recommendation']}")
            print(f"      Risk Level: {enhanced_report['executive_summary']['risk_assessment']}")
            
            # Quick analysis demonstration
            print(f"\n   ⚡ Quick Analysis Demo:")
            response = self.generate_demo_data()
            quick_result = quick_pb_analysis(response, 25.50, 35.75)
            
            if quick_result['success']:
                print(f"      Recommendation: {quick_result['recommendation']}")
                print(f"      Fair Value: ${quick_result['fair_value']:.2f}")
                print(f"      Risk Level: {quick_result['risk_level']}")
            
        except Exception as e:
            print(f"   ❌ Report generation error: {str(e)}")
    
    def _create_visualizations(self, response, statistical_result, enhanced_result):
        """Create visualizations for the analysis results."""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('P/B Statistical Analysis Results', fontsize=16)
            
            # Extract P/B data for plotting
            pb_data = response.data['pb_historical_data']
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in pb_data]
            pb_ratios = [d['pb_ratio'] for d in pb_data]
            
            # Plot 1: P/B Ratio Time Series with Trend
            ax1 = axes[0, 0]
            ax1.plot(dates, pb_ratios, 'b-', alpha=0.7, linewidth=1.5, label='P/B Ratio')
            
            # Add trend line if available
            if statistical_result.trend_analysis and statistical_result.trend_analysis.trend_direction != "neutral":
                slope = statistical_result.trend_analysis.linear_slope
                x_numeric = np.arange(len(pb_ratios))
                trend_line = np.mean(pb_ratios) + slope * (x_numeric - np.mean(x_numeric))
                ax1.plot(dates, trend_line, 'r--', alpha=0.8, linewidth=2, label='Trend Line')
            
            ax1.set_title('P/B Ratio Time Series & Trend')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('P/B Ratio')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Volatility Analysis
            ax2 = axes[0, 1]
            if len(pb_ratios) > 12:
                # Calculate rolling volatility
                pb_series = pd.Series(pb_ratios)
                rolling_vol = pb_series.rolling(window=12).std()
                ax2.plot(dates, rolling_vol, 'g-', linewidth=2, label='12-Period Rolling Volatility')
                
                # Add volatility regime indicators
                if statistical_result.volatility_analysis:
                    vol_regime = statistical_result.volatility_analysis.current_vol_regime
                    ax2.axhline(y=np.nanmean(rolling_vol), color='orange', linestyle='--', 
                              alpha=0.7, label=f'Mean (Regime: {vol_regime})')
            
            ax2.set_title('Volatility Analysis')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Volatility')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Market Cycle Visualization
            ax3 = axes[1, 0]
            ax3.plot(dates, pb_ratios, 'b-', alpha=0.7, linewidth=1.5)
            
            # Highlight cycle positions if detected
            if statistical_result.cycle_analysis and statistical_result.cycle_analysis.cycles_detected > 0:
                current_position = statistical_result.cycle_analysis.current_cycle_position
                ax3.axhline(y=np.mean(pb_ratios), color='orange', linestyle='--', alpha=0.7, 
                          label=f'Mean (Position: {current_position})')
                
                # Add percentile bands
                p25 = np.percentile(pb_ratios, 25)
                p75 = np.percentile(pb_ratios, 75)
                ax3.axhspan(p25, p75, alpha=0.2, color='green', label='25th-75th Percentile')
            
            ax3.set_title('Market Cycle Analysis')
            ax3.set_xlabel('Date')
            ax3.set_ylabel('P/B Ratio')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: Analysis Summary
            ax4 = axes[1, 1]
            ax4.axis('off')
            
            # Create summary text
            summary_text = []
            if statistical_result.trend_analysis:
                trend = statistical_result.trend_analysis
                summary_text.append(f"Trend: {trend.trend_direction.upper()}")
                summary_text.append(f"Strength: {trend.trend_strength:.3f}")
                summary_text.append(f"Significance: {trend.statistical_significance:.3f}")
            
            summary_text.append("")
            summary_text.append(f"Market Timing: {statistical_result.market_timing_signal}")
            summary_text.append(f"Signal Strength: {statistical_result.signal_strength:.3f}")
            
            summary_text.append("")
            if statistical_result.volatility_analysis:
                vol = statistical_result.volatility_analysis
                summary_text.append(f"Risk Level: {vol.current_vol_regime}")
                summary_text.append(f"Risk Score: {vol.overall_risk_score:.3f}")
            
            summary_text.append("")
            if enhanced_result.success:
                summary_text.append(f"Recommendation: {enhanced_result.investment_recommendation}")
                summary_text.append(f"Confidence: {enhanced_result.recommendation_confidence:.3f}")
            
            # Display summary
            ax4.text(0.05, 0.95, '\n'.join(summary_text), transform=ax4.transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
            ax4.set_title('Analysis Summary')
            
            plt.tight_layout()
            plt.savefig('pb_statistical_analysis_results.png', dpi=300, bbox_inches='tight')
            print(f"   📊 Visualization saved as 'pb_statistical_analysis_results.png'")
            
            # Show plot if in interactive environment
            try:
                plt.show()
            except:
                pass  # Skip if not in interactive environment
            
        except Exception as e:
            print(f"   ❌ Visualization error: {str(e)}")
    
    def run_scenario_comparison(self):
        """Run comparison across different market scenarios."""
        scenarios = ["bull", "bear", "volatile", "mixed"]
        
        print(f"\n{'='*80}")
        print(f"P/B STATISTICAL ANALYSIS - SCENARIO COMPARISON")
        print(f"{'='*80}")
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n🔍 Analyzing {scenario.upper()} market scenario...")
            
            try:
                response = self.generate_demo_data(scenario=scenario)
                historical_result = self.historical_engine.analyze_historical_performance(response, years=5)
                
                if historical_result.success:
                    statistical_result = self.statistical_engine.analyze_pb_statistics(historical_result)
                    
                    if statistical_result.success:
                        results[scenario] = {
                            'trend_direction': statistical_result.trend_analysis.trend_direction,
                            'trend_strength': statistical_result.trend_analysis.trend_strength,
                            'market_timing': statistical_result.market_timing_signal,
                            'signal_strength': statistical_result.signal_strength,
                            'risk_score': statistical_result.volatility_analysis.overall_risk_score,
                            'confidence': statistical_result.statistical_confidence
                        }
                        print(f"   ✅ {scenario} analysis completed")
                    else:
                        print(f"   ❌ {scenario} statistical analysis failed")
                else:
                    print(f"   ❌ {scenario} historical analysis failed")
                    
            except Exception as e:
                print(f"   ❌ {scenario} analysis error: {str(e)}")
        
        # Display comparison results
        if results:
            print(f"\n📊 SCENARIO COMPARISON RESULTS:")
            print(f"{'Scenario':<12} {'Trend':<10} {'Strength':<10} {'Timing':<10} {'Risk':<8} {'Confidence':<10}")
            print(f"{'-'*70}")
            
            for scenario, data in results.items():
                print(f"{scenario.capitalize():<12} "
                      f"{data['trend_direction']:<10} "
                      f"{data['trend_strength']:<10.3f} "
                      f"{data['market_timing']:<10} "
                      f"{data['risk_score']:<8.3f} "
                      f"{data['confidence']:<10.3f}")
        
        print(f"\n✅ Scenario comparison completed!")


def main():
    """Main function to run the statistical analysis demo."""
    print("P/B Statistical Analysis Engine Demo")
    print("====================================")
    
    demo = StatisticalAnalysisDemo()
    
    try:
        # Run individual scenario demos
        scenarios = ["mixed", "bull", "bear", "volatile"]
        
        for scenario in scenarios:
            demo.run_statistical_analysis_demo(scenario)
            print(f"\n{'─'*50}")
        
        # Run scenario comparison
        demo.run_scenario_comparison()
        
        print(f"\n🎉 All demonstrations completed successfully!")
        print(f"\nKey Features Demonstrated:")
        print(f"✅ Advanced trend detection with statistical significance")
        print(f"✅ Market cycle detection and regime analysis")
        print(f"✅ Volatility assessment and risk scoring")
        print(f"✅ Enhanced P/B analysis integration")
        print(f"✅ Comprehensive reporting capabilities")
        if PLOTTING_AVAILABLE:
            print(f"✅ Statistical visualization")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    main()