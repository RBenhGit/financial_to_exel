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
            'undervalued': '#2E8B57',  # Sea Green
            'overvalued': '#DC143C',  # Crimson
            'fairly_valued': '#4682B4',  # Steel Blue
            'background': '#F8F9FA',  # Light Gray
            'grid': '#E9ECEF',  # Light Grid
            'text': '#212529',  # Dark Text
        }

        self.performance_thresholds = {
            'strong_buy': 20,  # >20% upside
            'buy': 10,  # 10-20% upside
            'hold': -10,  # -10% to 10%
            'sell': -20,  # -20% to -10%
            'strong_sell': -20,  # <-20% downside
        }

    def create_enhanced_upside_downside_chart(
        self, watch_list_data: Dict, title: str = "Watch List Performance", show_enhanced_features: bool = True
    ) -> go.Figure:
        """
        Create enhanced interactive upside/downside bar chart with dual-view capabilities
        Enhanced for Task #84 with color-coded performance indicators and comprehensive tooltips

        Args:
            watch_list_data (dict): Watch list data from WatchListManager
            title (str): Chart title
            show_enhanced_features (bool): Show enhanced features like performance indicators

        Returns:
            plotly.graph_objects.Figure: Enhanced interactive chart
        """
        try:
            stocks = watch_list_data.get('stocks', [])

            if not stocks:
                # Return empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="No stocks found in watch list",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16),
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

                # Create enhanced hover text with comprehensive data
                analysis_age = self._calculate_analysis_age(analysis_date) if analysis_date else "N/A"
                risk_level = self._get_risk_level(upside)
                performance_category = self._get_performance_category(upside)
                
                hover_text = (
                    f"<b>📊 {ticker} - {performance_category}</b><br>"
                    f"🏢 Company: {company_name}<br>"
                    f"💵 Current Price: ${current_price:.2f}<br>"
                    f"🎯 Fair Value: ${fair_value:.2f}<br>"
                    f"📈 Upside/Downside: {upside:.1f}%<br>"
                    f"📅 Analysis Date: {analysis_date[:10] if analysis_date else 'N/A'}<br>"
                    f"⏰ Analysis Age: {analysis_age}<br>"
                    f"⚖️ Risk Level: {risk_level}<br>"
                    f"🎯 Target Price: ${fair_value:.2f}<br>"
                    f"💰 Potential Gain: ${(fair_value - current_price):.2f} per share" if current_price > 0 else ""
                )
                hover_texts.append(hover_text)

            # Create bar chart
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=tickers,
                        y=upside_values,
                        marker_color=colors,
                        hovertemplate=hover_texts,
                        name="Upside/Downside %",
                    )
                ]
            )

            # Enhanced horizontal reference lines with improved styling
            if show_enhanced_features:
                reference_lines_data = [
                    {'y': 20, 'color': '#2E8B57', 'dash': 'dash', 'text': '🚀 Strong Buy (+20%)', 'width': 2.5},
                    {'y': 10, 'color': '#90EE90', 'dash': 'dot', 'text': '📈 Buy (+10%)', 'width': 2},
                    {'y': 0, 'color': '#4682B4', 'dash': 'solid', 'text': '⚖️ Fair Value Zone', 'width': 3},
                    {'y': -10, 'color': '#FFA07A', 'dash': 'dot', 'text': '📉 Sell (-10%)', 'width': 2},
                    {'y': -20, 'color': '#DC143C', 'dash': 'dash', 'text': '🔻 Strong Sell (-20%)', 'width': 2.5}
                ]
                
                for line_data in reference_lines_data:
                    fig.add_hline(
                        y=line_data['y'],
                        line_dash=line_data['dash'],
                        line_color=line_data['color'],
                        line_width=line_data['width'],
                        opacity=0.8,
                        annotation_text=line_data['text'],
                        annotation_position="top right" if line_data['y'] > 0 else "bottom right",
                        annotation=dict(
                            font=dict(size=11, color=line_data['color']),
                            bgcolor="rgba(255, 255, 255, 0.8)",
                            bordercolor=line_data['color'],
                            borderwidth=1
                        )
                    )
                    
                # Add performance zones as shapes
                fig.add_shape(
                    type="rect",
                    x0=-0.5, x1=len(tickers)-0.5,
                    y0=20, y1=100,
                    fillcolor="green",
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )
                fig.add_shape(
                    type="rect", 
                    x0=-0.5, x1=len(tickers)-0.5,
                    y0=10, y1=20,
                    fillcolor="lightgreen",
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )
                fig.add_shape(
                    type="rect",
                    x0=-0.5, x1=len(tickers)-0.5,
                    y0=-10, y1=10,
                    fillcolor="blue",
                    opacity=0.05,
                    layer="below",
                    line_width=0
                )
                fig.add_shape(
                    type="rect",
                    x0=-0.5, x1=len(tickers)-0.5,
                    y0=-20, y1=-10,
                    fillcolor="salmon",
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )
                fig.add_shape(
                    type="rect",
                    x0=-0.5, x1=len(tickers)-0.5,
                    y0=-100, y1=-20,
                    fillcolor="red",
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )

            # Enhanced layout with improved styling
            enhanced_title = f"Target Analysis: {title}" if show_enhanced_features else title
            
            fig.update_layout(
                title={
                    'text': enhanced_title, 
                    'x': 0.5, 
                    'xanchor': 'center', 
                    'font': {'size': 22, 'color': '#2F4F4F'}
                },
                xaxis_title="Stock Ticker",
                yaxis_title="Upside/Downside (%)",
                plot_bgcolor=self.color_scheme['background'],
                paper_bgcolor='white',
                showlegend=False,
                height=650,
                hovermode='closest',
                margin=dict(l=60, r=60, t=120, b=80),
                font=dict(family="Arial, sans-serif", size=12),
                annotations=[
                    dict(
                        x=0.5, y=-0.15,
                        xref='paper', yref='paper',
                        text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        showarrow=False,
                        font=dict(size=10, color="gray")
                    )
                ] if show_enhanced_features else None
            )

            # Enhanced axes styling
            fig.update_xaxes(
                tickangle=45, 
                gridcolor=self.color_scheme['grid'],
                showgrid=True,
                linecolor='#D3D3D3',
                linewidth=1
            )
            fig.update_yaxes(
                gridcolor=self.color_scheme['grid'],
                showgrid=True,
                zeroline=True,
                zerolinecolor='#4682B4',
                zerolinewidth=3,
                linecolor='#D3D3D3',
                linewidth=1,
                tickformat=".1f"
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating upside/downside chart: {e}")
            # Return empty figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="red"),
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
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                return fig

            # Create histogram
            fig = go.Figure(
                data=[
                    go.Histogram(
                        x=upside_values,
                        nbinsx=20,
                        marker_color=self.color_scheme['fairly_valued'],
                        opacity=0.7,
                        name="Stock Count",
                    )
                ]
            )

            # Add vertical reference lines
            fig.add_vline(x=0, line_dash="solid", line_color="gray", line_width=2)
            fig.add_vline(x=10, line_dash="dot", line_color="green")
            fig.add_vline(x=-10, line_dash="dot", line_color="red")

            fig.update_layout(
                title="Performance Distribution",
                xaxis_title="Upside/Downside (%)",
                yaxis_title="Number of Stocks",
                plot_bgcolor=self.color_scheme['background'],
                showlegend=False,
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
            upside_values = [
                stock.get('upside_downside_pct', 0)
                for stock in stocks
                if stock.get('upside_downside_pct') is not None
            ]

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
                    'strong_sell_count': 0,
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
                'strong_sell_count': strong_sell_count,
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
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
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

                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=upside_values,
                        mode='lines+markers',
                        name=ticker_sym,
                        line=dict(width=2),
                        marker=dict(size=8),
                    )
                )

            # Add reference lines
            fig.add_hline(y=0, line_dash="solid", line_color="gray")
            fig.add_hline(y=10, line_dash="dot", line_color="green", opacity=0.5)
            fig.add_hline(y=-10, line_dash="dot", line_color="red", opacity=0.5)

            fig.update_layout(
                title=f"Analysis History - {ticker if ticker else 'All Stocks'}",
                xaxis_title="Analysis Date",
                yaxis_title="Upside/Downside (%)",
                plot_bgcolor=self.color_scheme['background'],
                hovermode='x unified',
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
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                return fig

            watch_list_names = []
            avg_upside_values = []
            median_upside_values = []

            for watch_list in multiple_watch_lists:
                name = watch_list.get('name', 'Unknown')
                stocks = watch_list.get('stocks', [])
                upside_values = [
                    s.get('upside_downside_pct', 0)
                    for s in stocks
                    if s.get('upside_downside_pct') is not None
                ]

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
            fig = go.Figure(
                data=[
                    go.Bar(
                        name='Average',
                        x=watch_list_names,
                        y=avg_upside_values,
                        marker_color=self.color_scheme['fairly_valued'],
                    ),
                    go.Bar(
                        name='Median',
                        x=watch_list_names,
                        y=median_upside_values,
                        marker_color=self.color_scheme['undervalued'],
                    ),
                ]
            )

            # Add reference line
            fig.add_hline(y=0, line_dash="solid", line_color="gray")

            fig.update_layout(
                title="Watch List Performance Comparison",
                xaxis_title="Watch Lists",
                yaxis_title="Upside/Downside (%)",
                barmode='group',
                plot_bgcolor=self.color_scheme['background'],
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            return go.Figure()

    def create_dual_view_comparison_chart(self, comparison_data: Dict, view_mode: str = 'side_by_side') -> go.Figure:
        """
        Create enhanced dual-view charts showing historical vs current upside/downside
        Enhanced for Task #84 with improved visualizations and dual perspectives
        
        Args:
            comparison_data (dict): Data from get_current_vs_historical_upside_downside()
            view_mode (str): 'side_by_side', 'overlay', or 'stacked' visualization mode
            
        Returns:
            plotly.graph_objects.Figure: Enhanced dual-view comparison chart
        """
        try:
            comparisons = comparison_data.get('comparisons', [])
            
            if not comparisons:
                fig = go.Figure()
                fig.add_annotation(
                    text="No comparison data available",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16),
                )
                return fig

            # Prepare data for side-by-side comparison
            tickers = []
            historical_upsides = []
            current_upsides = []
            upside_changes = []
            colors_historical = []
            colors_current = []
            hover_texts_historical = []
            hover_texts_current = []

            for comp in comparisons:
                ticker = comp['ticker']
                historical = comp['historical']
                current = comp['current']
                changes = comp['changes']
                
                tickers.append(ticker)
                historical_upsides.append(historical['upside_pct'])
                current_upsides.append(current['upside_pct'])
                upside_changes.append(changes['upside_change_pct'])
                
                # Color coding based on performance categories
                colors_historical.append(self._get_performance_color(historical['upside_pct']))
                colors_current.append(self._get_performance_color(current['upside_pct']))
                
                # Create hover text
                days_since = comp.get('days_since_analysis', 'N/A')
                hover_text_hist = (
                    f"<b>📊 {ticker} - Historical Analysis</b><br>"
                    f"🏢 Company: {comp['company_name']}<br>"
                    f"📅 Analysis Date: {historical.get('analysis_date', 'N/A')[:10]}<br>"
                    f"💰 Price at Analysis: ${historical['price']:.2f}<br>"
                    f"🎯 Fair Value: ${historical['fair_value']:.2f}<br>"
                    f"📈 Upside: {historical['upside_pct']:.1f}%<br>"
                    f"🔍 Status: {historical['valuation_status']}<br>"
                    f"⚖️ Risk Level: {self._get_risk_level(historical['upside_pct'])}"
                )
                
                hover_text_curr = (
                    f"<b>📈 {ticker} - Current Market View</b><br>"
                    f"🏢 Company: {comp['company_name']}<br>"
                    f"⏰ Days Since Analysis: {days_since}<br>"
                    f"💵 Current Price: ${current['price']:.2f}<br>"
                    f"🎯 Fair Value: ${current['fair_value']:.2f}<br>"
                    f"📊 Current Upside: {current['upside_pct']:.1f}%<br>"
                    f"🔍 Status: {current['valuation_status']}<br>"
                    f"📈 Change: {changes['upside_change_pct']:+.1f}%<br>"
                    f"⚖️ Risk Level: {self._get_risk_level(current['upside_pct'])}<br>"
                    f"💡 Insight: {comp['investment_insight']}"
                )
                
                hover_texts_historical.append(hover_text_hist)
                hover_texts_current.append(hover_text_curr)

            # Create subplot based on view mode
            if view_mode == 'side_by_side':
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('📊 Historical Analysis', '📈 Current Market View'),
                    shared_yaxes=True,
                    horizontal_spacing=0.08,
                    specs=[[{"secondary_y": False}, {"secondary_y": False}]]
                )
            elif view_mode == 'stacked':
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('📊 Historical Analysis', '📈 Current Market View'),
                    shared_xaxes=True,
                    vertical_spacing=0.12
                )
            else:  # overlay mode
                fig = go.Figure()

            # Add traces based on view mode
            if view_mode == 'overlay':
                # Overlay mode - both on same chart with transparency
                fig.add_trace(
                    go.Bar(
                        x=[f"{t} (H)" for t in tickers],
                        y=historical_upsides,
                        name="📊 Historical",
                        marker=dict(
                            color=colors_historical,
                            opacity=0.7,
                            line=dict(color='darkblue', width=1)
                        ),
                        hovertemplate=hover_texts_historical,
                        width=0.35,
                        offset=-0.2
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=[f"{t} (C)" for t in tickers],
                        y=current_upsides,
                        name="📈 Current",
                        marker=dict(
                            color=colors_current,
                            opacity=0.7,
                            line=dict(color='darkgreen', width=1)
                        ),
                        hovertemplate=hover_texts_current,
                        width=0.35,
                        offset=0.2
                    )
                )
            elif view_mode == 'stacked':
                # Stacked mode - historical on top, current on bottom
                fig.add_trace(
                    go.Bar(
                        x=tickers,
                        y=historical_upsides,
                        name="📊 Historical Upside",
                        marker_color=colors_historical,
                        hovertemplate=hover_texts_historical,
                        showlegend=True
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Bar(
                        x=tickers,
                        y=current_upsides,
                        name="📈 Current Upside",
                        marker_color=colors_current,
                        hovertemplate=hover_texts_current,
                        showlegend=True
                    ),
                    row=2, col=1
                )
            else:  # side_by_side (default)
                fig.add_trace(
                    go.Bar(
                        x=tickers,
                        y=historical_upsides,
                        name="📊 Historical Upside",
                        marker_color=colors_historical,
                        hovertemplate=hover_texts_historical,
                        showlegend=False
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Bar(
                        x=tickers,
                        y=current_upsides,
                        name="📈 Current Upside",
                        marker_color=colors_current,
                        hovertemplate=hover_texts_current,
                        showlegend=False
                    ),
                    row=1, col=2
                )

            # Enhanced reference lines with improved styling
            reference_lines = [
                {'y': 20, 'color': '#2E8B57', 'dash': 'dash', 'text': '🚀 Strong Buy (+20%)', 'width': 2},
                {'y': 10, 'color': '#90EE90', 'dash': 'dot', 'text': '📈 Buy (+10%)', 'width': 1.5},
                {'y': 0, 'color': '#4682B4', 'dash': 'solid', 'text': '⚖️ Fair Value', 'width': 3},
                {'y': -10, 'color': '#FFA07A', 'dash': 'dot', 'text': '📉 Sell (-10%)', 'width': 1.5},
                {'y': -20, 'color': '#DC143C', 'dash': 'dash', 'text': '🔻 Strong Sell (-20%)', 'width': 2}
            ]
            
            # Add reference lines based on view mode
            if view_mode == 'overlay':
                for line in reference_lines:
                    fig.add_hline(
                        y=line['y'],
                        line_dash=line['dash'],
                        line_color=line['color'],
                        line_width=line['width'],
                        opacity=0.6,
                        annotation_text=line['text'],
                        annotation_position="top right" if line['y'] > 0 else "bottom right"
                    )
            elif view_mode == 'stacked':
                for line in reference_lines:
                    for row in [1, 2]:
                        fig.add_hline(
                            y=line['y'],
                            line_dash=line['dash'],
                            line_color=line['color'],
                            line_width=line['width'],
                            opacity=0.6,
                            row=row, col=1
                        )
            else:  # side_by_side
                for line in reference_lines:
                    for col in [1, 2]:
                        fig.add_hline(
                            y=line['y'],
                            line_dash=line['dash'],
                            line_color=line['color'],
                            line_width=line['width'],
                            opacity=0.6,
                            row=1, col=col
                        )

            # Enhanced layout with improved styling
            title_text = f"🎯 Dual-View Analysis: {comparison_data.get('watch_list_name', 'Watch List')}"
            if view_mode == 'overlay':
                title_text += " (Overlay View)"
            elif view_mode == 'stacked':
                title_text += " (Stacked View)"
            else:
                title_text += " (Side-by-Side View)"
                
            fig.update_layout(
                title={
                    'text': title_text,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': '#2F4F4F'}
                },
                plot_bgcolor=self.color_scheme['background'],
                paper_bgcolor='white',
                height=800 if view_mode == 'stacked' else 700,
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ) if view_mode in ['overlay', 'stacked'] else None,
                margin=dict(l=50, r=50, t=100, b=80),
                font=dict(family="Arial, sans-serif", size=12)
            )

            # Enhanced axes styling based on view mode
            if view_mode == 'overlay':
                fig.update_xaxes(
                    tickangle=45, 
                    title_text="📊 Stock Analysis",
                    gridcolor=self.color_scheme['grid'],
                    showgrid=True
                )
                fig.update_yaxes(
                    title_text="📈 Upside/Downside (%)",
                    gridcolor=self.color_scheme['grid'],
                    zeroline=True,
                    zerolinecolor='#4682B4',
                    zerolinewidth=3,
                    showgrid=True
                )
            elif view_mode == 'stacked':
                fig.update_xaxes(tickangle=45, title_text="Stock Ticker", row=1, col=1)
                fig.update_xaxes(tickangle=45, title_text="Stock Ticker", row=2, col=1)
                fig.update_yaxes(
                    title_text="Historical Upside/Downside (%)",
                    gridcolor=self.color_scheme['grid'],
                    zeroline=True,
                    zerolinecolor='#4682B4',
                    zerolinewidth=3,
                    row=1, col=1
                )
                fig.update_yaxes(
                    title_text="Current Upside/Downside (%)",
                    gridcolor=self.color_scheme['grid'],
                    zeroline=True,
                    zerolinecolor='#4682B4',
                    zerolinewidth=3,
                    row=2, col=1
                )
            else:  # side_by_side
                fig.update_xaxes(tickangle=45, title_text="Stock Ticker", row=1, col=1)
                fig.update_xaxes(tickangle=45, title_text="Stock Ticker", row=1, col=2)
                fig.update_yaxes(
                    title_text="📊 Historical Upside/Downside (%)",
                    gridcolor=self.color_scheme['grid'],
                    zeroline=True,
                    zerolinecolor='#4682B4',
                    zerolinewidth=3,
                    row=1, col=1
                )
                fig.update_yaxes(
                    title_text="📈 Current Upside/Downside (%)",
                    gridcolor=self.color_scheme['grid'],
                    zeroline=True,
                    zerolinecolor='#4682B4',
                    zerolinewidth=3,
                    row=1, col=2
                )
            
            return fig

        except Exception as e:
            logger.error(f"Error creating dual-view comparison chart: {e}")
            # Return empty figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"🚫 Error creating dual-view chart: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="red"),
            )
            fig.update_layout(title="Chart Generation Error")
            return fig

    def create_upside_change_waterfall_chart(self, comparison_data: Dict) -> go.Figure:
        """
        Create waterfall chart showing how upside potential has changed for each stock
        
        Args:
            comparison_data (dict): Data from get_current_vs_historical_upside_downside()
            
        Returns:
            plotly.graph_objects.Figure: Waterfall chart showing upside changes
        """
        try:
            comparisons = comparison_data.get('comparisons', [])
            
            if not comparisons:
                fig = go.Figure()
                fig.add_annotation(
                    text="No comparison data available for waterfall chart",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                return fig

            # Sort by upside change (largest improvements first)
            comparisons_sorted = sorted(comparisons, key=lambda x: x['changes']['upside_change_pct'], reverse=True)

            # Prepare data
            tickers = [comp['ticker'] for comp in comparisons_sorted]
            upside_changes = [comp['changes']['upside_change_pct'] for comp in comparisons_sorted]
            
            # Color based on positive/negative change
            colors = ['green' if change > 0 else 'red' if change < 0 else 'gray' for change in upside_changes]
            
            # Create hover text
            hover_texts = []
            for comp in comparisons_sorted:
                historical_upside = comp['historical']['upside_pct']
                current_upside = comp['current']['upside_pct']
                change = comp['changes']['upside_change_pct']
                
                hover_text = (
                    f"<b>{comp['ticker']}</b><br>"
                    f"Company: {comp['company_name']}<br>"
                    f"Historical Upside: {historical_upside:.1f}%<br>"
                    f"Current Upside: {current_upside:.1f}%<br>"
                    f"Change: {change:+.1f}%<br>"
                    f"Status: {comp['changes']['opportunity_status']}<br>"
                    f"Insight: {comp['investment_insight']}"
                )
                hover_texts.append(hover_text)

            # Create waterfall chart
            fig = go.Figure(go.Waterfall(
                name="Upside Change",
                orientation="v",
                measure=["relative"] * len(tickers),
                x=tickers,
                text=[f"{change:+.1f}%" for change in upside_changes],
                y=upside_changes,
                hovertemplate=hover_texts,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": self.color_scheme['undervalued']}},
                decreasing={"marker": {"color": self.color_scheme['overvalued']}},
                totals={"marker": {"color": self.color_scheme['fairly_valued']}}
            ))

            # Add reference line at zero
            fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=2)

            fig.update_layout(
                title={
                    'text': f"Upside Potential Changes - {comparison_data.get('watch_list_name', 'Watch List')}",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="Stock Ticker",
                yaxis_title="Upside Change (%)",
                plot_bgcolor=self.color_scheme['background'],
                height=600,
                showlegend=False
            )
            
            fig.update_xaxes(tickangle=45)

            return fig

        except Exception as e:
            logger.error(f"Error creating upside change waterfall chart: {e}")
            return go.Figure()

    def _get_performance_color(self, upside_pct: float) -> str:
        """
        Get color based on upside performance thresholds
        
        Args:
            upside_pct (float): Upside percentage
            
        Returns:
            str: Color for the performance level
        """
        if upside_pct >= self.performance_thresholds['strong_buy']:
            return self.color_scheme['undervalued']  # Dark green
        elif upside_pct >= self.performance_thresholds['buy']:
            return '#90EE90'  # Light green
        elif upside_pct >= self.performance_thresholds['hold']:
            return self.color_scheme['fairly_valued']  # Blue
        elif upside_pct >= self.performance_thresholds['sell']:
            return '#FFA07A'  # Light salmon
        else:
            return self.color_scheme['overvalued']  # Red
    
    def _get_risk_level(self, upside_pct: float) -> str:
        """
        Get risk level description based on upside percentage
        
        Args:
            upside_pct (float): Upside percentage
            
        Returns:
            str: Risk level description
        """
        if upside_pct >= 20:
            return "🟢 Low Risk - Strong Value"
        elif upside_pct >= 10:
            return "🟡 Moderate Risk - Good Value"
        elif upside_pct >= -10:
            return "🟠 Balanced Risk - Fair Value"
        elif upside_pct >= -20:
            return "🔴 High Risk - Overvalued"
        else:
            return "🚨 Very High Risk - Significantly Overvalued"
    
    def _get_performance_category(self, upside_pct: float) -> str:
        """
        Get performance category description based on upside percentage
        
        Args:
            upside_pct (float): Upside percentage
            
        Returns:
            str: Performance category description
        """
        if upside_pct >= 20:
            return "Strong Buy Opportunity"
        elif upside_pct >= 10:
            return "Buy Opportunity"
        elif upside_pct >= -10:
            return "Fair Value Range"
        elif upside_pct >= -20:
            return "Overvalued Territory"
        else:
            return "Significantly Overvalued"
    
    def _calculate_analysis_age(self, analysis_date: str) -> str:
        """
        Calculate how old the analysis is
        
        Args:
            analysis_date (str): Analysis date string
            
        Returns:
            str: Human readable age description
        """
        try:
            if not analysis_date:
                return "Unknown"
                
            # Parse date (handle various formats)
            if 'T' in analysis_date:
                analysis_dt = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            else:
                analysis_dt = datetime.strptime(analysis_date[:10], '%Y-%m-%d')
                
            now = datetime.now()
            if analysis_dt.tzinfo:
                now = now.replace(tzinfo=analysis_dt.tzinfo)
                
            delta = now - analysis_dt
            days = delta.days
            
            if days == 0:
                return "Today"
            elif days == 1:
                return "1 day ago"
            elif days < 7:
                return f"{days} days ago"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif days < 365:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
                
        except Exception as e:
            logger.warning(f"Error calculating analysis age for date {analysis_date}: {e}")
            return "Unknown"
    
    def create_upside_downside_chart(
        self, watch_list_data: Dict, title: str = "Watch List Performance"
    ) -> go.Figure:
        """
        Create interactive upside/downside bar chart with performance indicators
        Backwards compatible method that calls the enhanced version
        
        Args:
            watch_list_data (dict): Watch list data from WatchListManager
            title (str): Chart title
            
        Returns:
            plotly.graph_objects.Figure: Interactive chart
        """
        return self.create_enhanced_upside_downside_chart(watch_list_data, title, show_enhanced_features=False)

    def create_opportunity_status_pie_chart(self, comparison_data: Dict) -> go.Figure:
        """
        Create pie chart showing distribution of opportunity status changes
        
        Args:
            comparison_data (dict): Data from get_current_vs_historical_upside_downside()
            
        Returns:
            plotly.graph_objects.Figure: Pie chart of opportunity statuses
        """
        try:
            summary = comparison_data.get('summary', {})
            opportunity_counts = summary.get('opportunity_distribution', {})
            
            if not opportunity_counts:
                fig = go.Figure()
                fig.add_annotation(
                    text="No opportunity data available",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                return fig

            labels = list(opportunity_counts.keys())
            values = list(opportunity_counts.values())
            
            # Define colors for different opportunity statuses
            status_colors = {
                'Opportunity Improved': '#2E8B57',
                'Slight Improvement': '#90EE90',
                'Opportunity Unchanged': '#4682B4',
                'Slight Deterioration': '#FFA07A',
                'Opportunity Deteriorated': '#DC143C',
                'Fair Value Increased': '#32CD32',
                'Price Outpaced Value': '#B22222'
            }
            
            colors = [status_colors.get(label, '#808080') for label in labels]

            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent+value',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])

            fig.update_layout(
                title={
                    'text': f"Investment Opportunity Changes - {comparison_data.get('watch_list_name', 'Watch List')}",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                height=500,
                font=dict(size=12)
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating opportunity status pie chart: {e}")
            return go.Figure()


# Global instance for easy access
watch_list_visualizer = WatchListVisualizer()
