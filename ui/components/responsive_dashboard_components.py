"""
Responsive Dashboard Components for Financial Analysis Application

Provides pre-built, responsive UI components specifically designed for
financial data display with mobile-first responsive design patterns.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Union
import logging

from .responsive_framework import responsive_layout, accessibility

logger = logging.getLogger(__name__)

class ResponsiveFinancialComponents:
    """Pre-built responsive components for financial data display."""

    def __init__(self):
        self.layout_manager = responsive_layout

    def financial_summary_card(
        self,
        company_name: str,
        ticker: str,
        current_price: float,
        currency: str = "USD",
        market_cap: Optional[float] = None,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Render a responsive company summary card.

        Args:
            company_name: Company name
            ticker: Stock ticker
            current_price: Current stock price
            currency: Currency symbol
            market_cap: Market capitalization
            additional_metrics: Additional metrics to display
        """
        with st.container():
            st.markdown("### 🏢 Company Overview")

            # Primary info row
            col1, col2 = self.layout_manager.responsive_columns([2, 1])

            with col1:
                st.markdown(f"**{company_name}** ({ticker})")
                if market_cap:
                    market_cap_display = f"{market_cap/1e9:.1f}B" if market_cap > 1e9 else f"{market_cap/1e6:.1f}M"
                    st.caption(f"Market Cap: {currency} {market_cap_display}")

            with col2:
                self.layout_manager.accessible_metric(
                    label="Current Price",
                    value=f"{currency} {current_price:.2f}",
                    help=f"Latest stock price for {ticker}"
                )

            # Additional metrics in responsive grid
            if additional_metrics:
                metrics_list = []
                for label, value in additional_metrics.items():
                    metrics_list.append({
                        'label': label,
                        'value': str(value),
                        'help': f"{label} for {company_name}"
                    })

                if metrics_list:
                    self.layout_manager.responsive_metric_grid(metrics_list, max_cols=3)

    def fcf_analysis_dashboard(
        self,
        fcf_results: Dict[str, Any],
        show_detailed: bool = True
    ) -> None:
        """
        Render responsive FCF analysis dashboard.

        Args:
            fcf_results: FCF calculation results
            show_detailed: Whether to show detailed breakdown
        """
        if not fcf_results:
            st.warning("No FCF data available")
            return

        st.markdown("### 💰 Free Cash Flow Analysis")

        # Extract FCF types and latest values
        fcf_metrics = []
        for fcf_type, values in fcf_results.items():
            if isinstance(values, dict) and 'values' in values:
                latest_value = values['values'][-1] if values['values'] else 0
                fcf_metrics.append({
                    'label': fcf_type.replace('_', ' ').title(),
                    'value': f"${latest_value:.1f}M",
                    'help': f"Latest {fcf_type} calculation"
                })

        # Display metrics in responsive grid
        self.layout_manager.responsive_metric_grid(fcf_metrics, max_cols=3)

        if show_detailed:
            # Detailed breakdown in collapsible sections
            with st.expander("📊 Detailed FCF Breakdown", expanded=False):
                self._render_fcf_detailed_breakdown(fcf_results)

    def valuation_comparison_panel(
        self,
        dcf_result: Optional[Dict] = None,
        ddm_result: Optional[Dict] = None,
        pb_result: Optional[Dict] = None,
        current_price: Optional[float] = None
    ) -> None:
        """
        Render responsive valuation comparison panel.

        Args:
            dcf_result: DCF valuation results
            ddm_result: DDM valuation results
            pb_result: P/B valuation results
            current_price: Current stock price
        """
        st.markdown("### 🎯 Valuation Comparison")

        valuations = []

        if dcf_result and 'fair_value' in dcf_result:
            valuations.append({
                'method': 'DCF',
                'fair_value': dcf_result['fair_value'],
                'upside': self._calculate_upside(current_price, dcf_result['fair_value']) if current_price else None
            })

        if ddm_result and 'fair_value' in ddm_result:
            valuations.append({
                'method': 'DDM',
                'fair_value': ddm_result['fair_value'],
                'upside': self._calculate_upside(current_price, ddm_result['fair_value']) if current_price else None
            })

        if pb_result and 'fair_value' in pb_result:
            valuations.append({
                'method': 'P/B',
                'fair_value': pb_result['fair_value'],
                'upside': self._calculate_upside(current_price, pb_result['fair_value']) if current_price else None
            })

        if not valuations:
            st.info("Run valuations to see comparison")
            return

        # Create responsive comparison table
        self._render_valuation_table(valuations, current_price)

    def responsive_chart_container(
        self,
        chart_data: Any,
        title: str,
        height: int = 400,
        use_container_width: bool = True
    ) -> None:
        """
        Render chart in responsive container.

        Args:
            chart_data: Chart object (plotly, altair, etc.)
            title: Chart title
            height: Chart height
            use_container_width: Whether to use full container width
        """
        with st.container():
            st.markdown(f"#### {title}")
            with st.container():
                st.markdown('<div class="responsive-chart">', unsafe_allow_html=True)

                # Configure chart for responsiveness
                if hasattr(chart_data, 'update_layout'):  # Plotly chart
                    chart_data.update_layout(
                        height=height,
                        autosize=True,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )

                st.plotly_chart(
                    chart_data,
                    use_container_width=use_container_width,
                    height=height
                )
                st.markdown('</div>', unsafe_allow_html=True)

    def mobile_optimized_data_table(
        self,
        df: pd.DataFrame,
        title: str,
        max_rows: int = 10,
        hide_columns_mobile: Optional[List[str]] = None
    ) -> None:
        """
        Render mobile-optimized data table.

        Args:
            df: DataFrame to display
            title: Table title
            max_rows: Maximum rows to display
            hide_columns_mobile: Columns to hide on mobile
        """
        st.markdown(f"#### {title}")

        if df.empty:
            st.info("No data available")
            return

        # Limit rows for performance
        display_df = df.head(max_rows) if len(df) > max_rows else df

        # Add responsive styling
        with st.container():
            st.markdown('<div class="responsive-table">', unsafe_allow_html=True)

            # For mobile, show simplified view
            if hide_columns_mobile:
                # This would require client-side detection in a real implementation
                # For now, show all columns
                pass

            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(400, len(display_df) * 35 + 50)  # Dynamic height
            )

            if len(df) > max_rows:
                st.caption(f"Showing {max_rows} of {len(df)} rows")

            st.markdown('</div>', unsafe_allow_html=True)

    def sidebar_responsive_controls(
        self,
        controls_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Render responsive sidebar controls that adapt to screen size.

        Args:
            controls_config: Configuration for controls

        Returns:
            Dictionary of control values
        """
        results = {}

        # Group controls in collapsible sections for mobile
        for section, config in controls_config.items():
            with st.sidebar.expander(config.get('title', section), expanded=config.get('expanded', True)):

                for control_id, control_config in config.get('controls', {}).items():
                    control_type = control_config.get('type', 'text_input')

                    if control_type == 'selectbox':
                        results[control_id] = st.selectbox(
                            control_config.get('label', control_id),
                            options=control_config.get('options', []),
                            key=f"sidebar_{control_id}",
                            help=control_config.get('help')
                        )
                    elif control_type == 'slider':
                        results[control_id] = st.slider(
                            control_config.get('label', control_id),
                            min_value=control_config.get('min', 0),
                            max_value=control_config.get('max', 100),
                            value=control_config.get('default', 50),
                            key=f"sidebar_{control_id}",
                            help=control_config.get('help')
                        )
                    elif control_type == 'text_input':
                        results[control_id] = st.text_input(
                            control_config.get('label', control_id),
                            value=control_config.get('default', ''),
                            key=f"sidebar_{control_id}",
                            help=control_config.get('help')
                        )

        return results

    def _render_fcf_detailed_breakdown(self, fcf_results: Dict[str, Any]) -> None:
        """Render detailed FCF breakdown."""
        for fcf_type, data in fcf_results.items():
            if isinstance(data, dict) and 'values' in data:
                st.markdown(f"**{fcf_type.replace('_', ' ').title()}**")

                values = data['values']
                if values:
                    # Create mini chart
                    if len(values) > 1:
                        chart_data = pd.DataFrame({
                            'Period': range(len(values)),
                            'FCF': values
                        })

                        fig = px.line(
                            chart_data,
                            x='Period',
                            y='FCF',
                            title=f"{fcf_type} Trend"
                        )
                        fig.update_layout(height=200)
                        st.plotly_chart(fig, use_container_width=True)

                    # Show latest value
                    st.metric(
                        label="Latest Value",
                        value=f"${values[-1]:.1f}M"
                    )

    def _render_valuation_table(self, valuations: List[Dict], current_price: Optional[float]) -> None:
        """Render valuation comparison table."""
        # Create DataFrame for display
        df_data = []
        for val in valuations:
            row = {
                'Method': val['method'],
                'Fair Value': f"${val['fair_value']:.2f}",
            }
            if val['upside'] is not None:
                row['Upside/Downside'] = f"{val['upside']:+.1f}%"
            df_data.append(row)

        if current_price:
            df_data.append({
                'Method': 'Current Price',
                'Fair Value': f"${current_price:.2f}",
                'Upside/Downside': '—'
            })

        df = pd.DataFrame(df_data)

        # Display in responsive table
        self.mobile_optimized_data_table(
            df,
            "Valuation Summary",
            max_rows=len(df)
        )

    def _calculate_upside(self, current_price: float, fair_value: float) -> float:
        """Calculate upside percentage."""
        if current_price and fair_value:
            return ((fair_value - current_price) / current_price) * 100
        return 0.0

# Global instance
responsive_components = ResponsiveFinancialComponents()