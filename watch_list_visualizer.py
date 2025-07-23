"""
Watch List Visualization Module

This module provides interactive visualization capabilities for watch lists,
including upside/downside bar charts and performance analysis plots.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WatchListVisualizer:
    """
    Creates interactive visualizations for watch list data
    """
    
    def __init__(self):
        """Initialize visualizer with default styling"""
        self.color_scheme = {
            'undervalued': '#2E8B57',      # Sea Green
            'overvalued': '#DC143C',       # Crimson
            'fairly_valued': '#4682B4',    # Steel Blue
            'background': '#F8F9FA',       # Light Gray
            'grid': '#E9ECEF',            # Light Grid
            'text': '#212529'             # Dark Text
        }
        
        self.performance_thresholds = {
            'strong_buy': 20,      # >20% upside
            'buy': 10,             # 10-20% upside
            'hold': -10,           # -10% to 10%
            'sell': -20,           # -20% to -10%
            'strong_sell': -20     # <-20% downside
        }
    
    def create_upside_downside_chart(self, watch_list_data: Dict, 
                                   title: str = "Watch List Performance") -> go.Figure:
        """
        Create interactive upside/downside bar chart with performance indicators
        
        Args:
            watch_list_data (dict): Watch list data from WatchListManager
            title (str): Chart title
            
        Returns:
            plotly.graph_objects.Figure: Interactive chart
        """
        try:
            stocks = watch_list_data.get('stocks', [])
            
            if not stocks:
                # Return empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="No stocks found in watch list",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16)
                )
                fig.update_layout(title=title)
                return fig
            
            # Prepare data
            tickers = []
            upside_values = []
            colors = []
            hover_texts = []
            
            for stock in stocks:
                ticker = stock.get('ticker', 'UNKNOWN')
                upside = stock.get('upside_downside_pct', 0)
                current_price = stock.get('current_price', 0)
                fair_value = stock.get('fair_value', 0)
                company_name = stock.get('company_name', '')
                analysis_date = stock.get('analysis_date', '')
                
                tickers.append(ticker)
                upside_values.append(upside)
                
                # Color based on performance
                if upside >= self.performance_thresholds['strong_buy']:
                    colors.append(self.color_scheme['undervalued'])
                elif upside >= self.performance_thresholds['buy']:
                    colors.append('#90EE90')  # Light Green
                elif upside >= self.performance_thresholds['hold']:
                    colors.append(self.color_scheme['fairly_valued'])
                elif upside >= self.performance_thresholds['sell']:
                    colors.append('#FFA07A')  # Light Salmon
                else:
                    colors.append(self.color_scheme['overvalued'])
                
                # Create hover text
                hover_text = (
                    f"<b>{ticker}</b><br>"
                    f"Company: {company_name}<br>"
                    f"Current Price: ${current_price:.2f}<br>"
                    f"Fair Value: ${fair_value:.2f}<br>"
                    f"Upside/Downside: {upside:.1f}%<br>"
                    f"Analysis Date: {analysis_date[:10] if analysis_date else 'N/A'}"
                )
                hover_texts.append(hover_text)
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=tickers,
                    y=upside_values,
                    marker_color=colors,
                    hovertemplate=hover_texts,
                    name="Upside/Downside %"
                )
            ])
            
            # Add horizontal reference lines
            fig.add_hline(
                y=20, line_dash="dash", line_color="green", 
                annotation_text="Strong Buy (>20%)", annotation_position="top right"
            )
            fig.add_hline(
                y=10, line_dash="dot", line_color="lightgreen", 
                annotation_text="Buy (>10%)", annotation_position="top right"
            )
            fig.add_hline(
                y=0, line_dash="solid", line_color="gray", line_width=2,
                annotation_text="Fair Value", annotation_position="top right"
            )
            fig.add_hline(
                y=-10, line_dash="dot", line_color="lightsalmon", 
                annotation_text="Sell (<-10%)", annotation_position="bottom right"
            )
            fig.add_hline(
                y=-20, line_dash="dash", line_color="red", 
                annotation_text="Strong Sell (<-20%)", annotation_position="bottom right"
            )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20}
                },
                xaxis_title="Stock Ticker",
                yaxis_title="Upside/Downside (%)",
                plot_bgcolor=self.color_scheme['background'],
                paper_bgcolor='white',
                showlegend=False,
                height=600,
                hovermode='closest'
            )
            
            # Update axes
            fig.update_xaxes(
                tickangle=45,
                gridcolor=self.color_scheme['grid']
            )
            fig.update_yaxes(
                gridcolor=self.color_scheme['grid'],
                zeroline=True,
                zerolinecolor='gray',
                zerolinewidth=2
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating upside/downside chart: {e}")
            # Return empty figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(title=title)
            return fig
    
    def create_performance_distribution_chart(self, watch_list_data: Dict) -> go.Figure:
        """
        Create performance distribution histogram
        
        Args:
            watch_list_data (dict): Watch list data
            
        Returns:
            plotly.graph_objects.Figure: Distribution chart
        """
        try:
            stocks = watch_list_data.get('stocks', [])
            upside_values = [stock.get('upside_downside_pct', 0) for stock in stocks]
            
            if not upside_values:
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for distribution",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig
            
            # Create histogram
            fig = go.Figure(data=[
                go.Histogram(
                    x=upside_values,
                    nbinsx=20,
                    marker_color=self.color_scheme['fairly_valued'],
                    opacity=0.7,
                    name="Stock Count"
                )
            ])
            
            # Add vertical reference lines
            fig.add_vline(x=0, line_dash="solid", line_color="gray", line_width=2)
            fig.add_vline(x=10, line_dash="dot", line_color="green")
            fig.add_vline(x=-10, line_dash="dot", line_color="red")
            
            fig.update_layout(
                title="Performance Distribution",
                xaxis_title="Upside/Downside (%)",
                yaxis_title="Number of Stocks",
                plot_bgcolor=self.color_scheme['background'],
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating distribution chart: {e}")
            return go.Figure()
    
    def create_performance_summary_metrics(self, watch_list_data: Dict) -> Dict:
        """
        Calculate performance summary metrics for display
        
        Args:
            watch_list_data (dict): Watch list data
            
        Returns:
            dict: Summary metrics
        """
        try:
            stocks = watch_list_data.get('stocks', [])
            upside_values = [stock.get('upside_downside_pct', 0) for stock in stocks 
                           if stock.get('upside_downside_pct') is not None]
            
            if not upside_values:
                return {
                    'total_stocks': 0,
                    'avg_upside': 0,
                    'median_upside': 0,
                    'max_upside': 0,
                    'min_upside': 0,
                    'undervalued_count': 0,
                    'overvalued_count': 0,
                    'fairly_valued_count': 0,
                    'strong_buy_count': 0,
                    'buy_count': 0,
                    'hold_count': 0,
                    'sell_count': 0,
                    'strong_sell_count': 0
                }
            
            # Calculate basic statistics
            avg_upside = np.mean(upside_values)
            median_upside = np.median(upside_values)
            max_upside = np.max(upside_values)
            min_upside = np.min(upside_values)
            
            # Count categories
            undervalued_count = len([v for v in upside_values if v > 0])
            overvalued_count = len([v for v in upside_values if v < 0])
            fairly_valued_count = len([v for v in upside_values if abs(v) <= 5])
            
            # Count performance categories
            strong_buy_count = len([v for v in upside_values if v >= 20])
            buy_count = len([v for v in upside_values if 10 <= v < 20])
            hold_count = len([v for v in upside_values if -10 <= v < 10])
            sell_count = len([v for v in upside_values if -20 <= v < -10])
            strong_sell_count = len([v for v in upside_values if v < -20])
            
            return {
                'total_stocks': len(stocks),
                'avg_upside': avg_upside,
                'median_upside': median_upside,
                'max_upside': max_upside,
                'min_upside': min_upside,
                'undervalued_count': undervalued_count,
                'overvalued_count': overvalued_count,
                'fairly_valued_count': fairly_valued_count,
                'strong_buy_count': strong_buy_count,
                'buy_count': buy_count,
                'hold_count': hold_count,
                'sell_count': sell_count,
                'strong_sell_count': strong_sell_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary metrics: {e}")
            return {}
    
    def create_time_series_chart(self, watch_list_data: Dict, ticker: str = None) -> go.Figure:
        """
        Create time series chart showing analysis history for a stock or watch list
        
        Args:
            watch_list_data (dict): Watch list data
            ticker (str): Specific ticker to show (optional)
            
        Returns:
            plotly.graph_objects.Figure: Time series chart
        """
        try:
            stocks = watch_list_data.get('stocks', [])
            
            if ticker:
                # Filter for specific ticker
                stocks = [s for s in stocks if s.get('ticker', '').upper() == ticker.upper()]
            
            if not stocks:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"No data found for {ticker if ticker else 'watch list'}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig
            
            # Group by ticker and sort by date
            ticker_data = {}
            for stock in stocks:
                ticker_sym = stock.get('ticker', 'UNKNOWN')
                if ticker_sym not in ticker_data:
                    ticker_data[ticker_sym] = []
                ticker_data[ticker_sym].append(stock)
            
            # Sort each ticker's data by date
            for ticker_sym in ticker_data:
                ticker_data[ticker_sym].sort(key=lambda x: x.get('analysis_date', ''))
            
            # Create traces for each ticker
            fig = go.Figure()
            
            for ticker_sym, ticker_stocks in ticker_data.items():
                dates = [stock.get('analysis_date', '')[:10] for stock in ticker_stocks]
                upside_values = [stock.get('upside_downside_pct', 0) for stock in ticker_stocks]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=upside_values,
                    mode='lines+markers',
                    name=ticker_sym,
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
            
            # Add reference lines
            fig.add_hline(y=0, line_dash="solid", line_color="gray")
            fig.add_hline(y=10, line_dash="dot", line_color="green", opacity=0.5)
            fig.add_hline(y=-10, line_dash="dot", line_color="red", opacity=0.5)
            
            fig.update_layout(
                title=f"Analysis History - {ticker if ticker else 'All Stocks'}",
                xaxis_title="Analysis Date",
                yaxis_title="Upside/Downside (%)",
                plot_bgcolor=self.color_scheme['background'],
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series chart: {e}")
            return go.Figure()
    
    def create_sector_comparison_chart(self, multiple_watch_lists: List[Dict]) -> go.Figure:
        """
        Create comparison chart across multiple watch lists (e.g., sectors)
        
        Args:
            multiple_watch_lists (list): List of watch list data dictionaries
            
        Returns:
            plotly.graph_objects.Figure: Comparison chart
        """
        try:
            if not multiple_watch_lists:
                fig = go.Figure()
                fig.add_annotation(
                    text="No watch lists provided for comparison",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig
            
            watch_list_names = []
            avg_upside_values = []
            median_upside_values = []
            
            for watch_list in multiple_watch_lists:
                name = watch_list.get('name', 'Unknown')
                stocks = watch_list.get('stocks', [])
                upside_values = [s.get('upside_downside_pct', 0) for s in stocks 
                               if s.get('upside_downside_pct') is not None]
                
                if upside_values:
                    avg_upside = np.mean(upside_values)
                    median_upside = np.median(upside_values)
                else:
                    avg_upside = 0
                    median_upside = 0
                
                watch_list_names.append(name)
                avg_upside_values.append(avg_upside)
                median_upside_values.append(median_upside)
            
            # Create grouped bar chart
            fig = go.Figure(data=[
                go.Bar(name='Average', x=watch_list_names, y=avg_upside_values,
                      marker_color=self.color_scheme['fairly_valued']),
                go.Bar(name='Median', x=watch_list_names, y=median_upside_values,
                      marker_color=self.color_scheme['undervalued'])
            ])
            
            # Add reference line
            fig.add_hline(y=0, line_dash="solid", line_color="gray")
            
            fig.update_layout(
                title="Watch List Performance Comparison",
                xaxis_title="Watch Lists",
                yaxis_title="Upside/Downside (%)",
                barmode='group',
                plot_bgcolor=self.color_scheme['background']
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            return go.Figure()

# Global instance for easy access
watch_list_visualizer = WatchListVisualizer()