"""
PDF Report Generator Module

This module handles the generation of comprehensive PDF reports including FCF and DCF analysis.
"""

import os
import io
import tempfile
from datetime import datetime
import pandas as pd
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import logging

logger = logging.getLogger(__name__)


class FCFReportGenerator:
    """
    Generates comprehensive PDF reports for FCF and DCF analysis
    """

    def __init__(self):
        """Initialize report generator"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#1f77b4'),
        )

        # Section header style
        self.section_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50'),
        )

        # Subsection style
        self.subsection_style = ParagraphStyle(
            'SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=15,
            textColor=colors.HexColor('#34495e'),
        )

        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal', parent=self.styles['Normal'], fontSize=10, spaceAfter=12, leading=14
        )

    def generate_report(
        self,
        company_name,
        fcf_results,
        dcf_results,
        dcf_assumptions,
        fcf_plots,
        dcf_plots,
        growth_analysis_df,
        fcf_data_df,
        dcf_projections_df,
        current_price=None,
        ticker=None,
        sensitivity_params=None,
        user_decisions=None,
    ):
        """
        Generate comprehensive PDF report

        Args:
            company_name (str): Company name
            fcf_results (dict): FCF calculation results
            dcf_results (dict): DCF calculation results
            dcf_assumptions (dict): DCF assumptions used
            fcf_plots (dict): FCF analysis plots
            dcf_plots (dict): DCF analysis plots
            growth_analysis_df (pd.DataFrame): Growth rate analysis table
            fcf_data_df (pd.DataFrame): FCF data table
            dcf_projections_df (pd.DataFrame): DCF projections table
            current_price (float): Current market price
            ticker (str): Stock ticker
            sensitivity_params (dict): Sensitivity analysis parameters
            user_decisions (dict): User decisions and rationale

        Returns:
            bytes: PDF report as bytes
        """
        try:
            # Create temporary file for PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=72, bottomMargin=72)
            story = []

            # Report title and metadata
            story.extend(self._create_title_section(company_name, ticker, current_price))

            # Executive Summary
            story.extend(
                self._create_executive_summary(
                    fcf_results, dcf_results, current_price, dcf_assumptions
                )
            )

            # FCF Analysis Section (only if FCF data is available)
            if fcf_results and any(fcf_results.values()):
                story.append(PageBreak())
                story.extend(
                    self._create_fcf_section(
                        fcf_results, fcf_plots, growth_analysis_df, fcf_data_df
                    )
                )

            # DCF Analysis Section (only if DCF results are available)
            if dcf_results and dcf_results.get('enterprise_value', 0):
                story.append(PageBreak())
                story.extend(
                    self._create_dcf_section(
                        dcf_results, dcf_assumptions, dcf_plots, dcf_projections_df, current_price
                    )
                )

            # User Assumptions and Decisions Section (only if assumptions are available)
            if dcf_assumptions:
                story.append(PageBreak())
                story.extend(
                    self._create_assumptions_section(
                        dcf_assumptions, sensitivity_params, user_decisions
                    )
                )

            # Appendix (only if assumptions are available)
            if dcf_assumptions:
                story.append(PageBreak())
                story.extend(self._create_appendix(dcf_assumptions))

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise

    def _create_title_section(self, company_name, ticker, current_price):
        """Create title section of the report"""
        story = []

        # Main title with company name/ticker prominently displayed
        if ticker:
            title_text = f"{company_name} - {ticker}<br/>Free Cash Flow & DCF Analysis Report"
        else:
            title_text = f"{company_name}<br/>Free Cash Flow & DCF Analysis Report"

        story.append(Paragraph(title_text, self.title_style))

        # Report metadata with prominent price display
        current_date = datetime.now().strftime("%B %d, %Y")
        metadata_text = f"<b>Analysis Date:</b> {current_date}"

        if current_price:
            metadata_text += f"<br/><b>Current Share Price:</b> ${current_price:.2f}"

        story.append(Paragraph(metadata_text, self.normal_style))
        story.append(Spacer(1, 20))

        return story

    def _create_executive_summary(
        self, fcf_results, dcf_results, current_price, dcf_assumptions=None
    ):
        """Create executive summary section"""
        story = []

        story.append(Paragraph("Executive Summary", self.section_style))

        # Key Investment Metrics Summary
        if dcf_results and dcf_assumptions:
            story.append(Paragraph("Key Investment Metrics", self.subsection_style))

            # Create summary metrics table
            metrics_data = [['Metric', 'Value', 'Assumption/Source']]

            # Fair value and recommendation
            fair_value = dcf_results.get('value_per_share', 0)
            if fair_value > 0 and current_price:
                upside = ((fair_value - current_price) / current_price) * 100
                recommendation = "BUY" if upside > 10 else "HOLD" if upside > -10 else "SELL"
                metrics_data.append(
                    ['Investment Recommendation', recommendation, f'{upside:+.1f}% upside/downside']
                )
                metrics_data.append(['Fair Value per Share', f'${fair_value:.2f}', 'DCF Analysis'])
                metrics_data.append(
                    ['Current Market Price', f'${current_price:.2f}', 'Market Data']
                )

            # Key assumptions
            if 'fcf_type' in dcf_assumptions:
                metrics_data.append(
                    ['FCF Methodology', dcf_assumptions['fcf_type'], 'User Selection']
                )

            if 'growth_rate_yr1_5' in dcf_assumptions:
                growth = dcf_assumptions['growth_rate_yr1_5'] * 100
                metrics_data.append(
                    ['Growth Rate (Yrs 1-5)', f'{growth:.1f}%', 'Historical Analysis + User Input']
                )

            if 'discount_rate' in dcf_assumptions:
                discount = dcf_assumptions['discount_rate'] * 100
                metrics_data.append(['Discount Rate (WACC)', f'{discount:.1f}%', 'User Assumption'])

            metrics_table = Table(metrics_data, colWidths=[2.0 * inch, 1.3 * inch, 2.7 * inch])
            metrics_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]
                )
            )

            story.append(metrics_table)
            story.append(Spacer(1, 15))

        # Valuation Comparison (most important section)
        elif dcf_results and current_price:
            story.append(Paragraph("Investment Recommendation", self.subsection_style))
            valuation_comparison = self._get_valuation_comparison(dcf_results, current_price)
            story.append(Paragraph(valuation_comparison, self.normal_style))
            story.append(Spacer(1, 15))

        # FCF Summary (only if FCF data is available)
        if fcf_results and any(fcf_results.values()):
            fcf_summary = self._get_fcf_summary(fcf_results)
            story.append(
                Paragraph(f"<b>Free Cash Flow Analysis:</b><br/>{fcf_summary}", self.normal_style)
            )
        else:
            story.append(
                Paragraph(
                    f"<b>Free Cash Flow Analysis:</b><br/>No FCF analysis was performed due to insufficient financial data.",
                    self.normal_style,
                )
            )

        # DCF Summary (only if DCF results are available)
        if dcf_results and dcf_results.get('enterprise_value', 0):
            dcf_summary = self._get_dcf_summary(dcf_results, current_price)
            story.append(Paragraph(f"<b>DCF Valuation:</b><br/>{dcf_summary}", self.normal_style))
        else:
            story.append(
                Paragraph(
                    f"<b>DCF Valuation:</b><br/>No DCF valuation was performed. This analysis requires user-specified assumptions for discount rates and growth projections.",
                    self.normal_style,
                )
            )

        story.append(Spacer(1, 20))

        return story

    def _get_valuation_comparison(self, dcf_results, current_price):
        """Generate valuation comparison with investment recommendation"""
        if not dcf_results or not current_price:
            return "No valuation comparison available."

        fair_value = dcf_results.get('value_per_share', 0)

        if fair_value <= 0:
            return "Unable to calculate fair value for comparison."

        upside = ((fair_value - current_price) / current_price) * 100

        # Create recommendation based on upside/downside
        if upside > 20:
            recommendation = "<b><font color='green'>STRONG BUY</font></b>"
            reasoning = "significantly undervalued"
        elif upside >= 10:
            recommendation = "<b><font color='green'>BUY</font></b>"
            reasoning = "undervalued"
        elif upside > -10:
            recommendation = "<b><font color='orange'>HOLD</font></b>"
            reasoning = "fairly valued"
        elif upside > -20:
            recommendation = "<b><font color='red'>SELL</font></b>"
            reasoning = "overvalued"
        else:
            recommendation = "<b><font color='red'>STRONG SELL</font></b>"
            reasoning = "significantly overvalued"

        comparison_text = f"""
        <b>Current Share Price:</b> ${current_price:.2f}<br/>
        <b>DCF Fair Value:</b> ${fair_value:.2f}<br/>
        <b>Upside/Downside:</b> {upside:+.1f}%<br/>
        <b>Investment Recommendation:</b> {recommendation}<br/>
        <i>The stock appears {reasoning} based on DCF analysis.</i>
        """

        return comparison_text.strip()

    def _get_fcf_summary(self, fcf_results):
        """Generate FCF summary text"""
        if not fcf_results or not any(fcf_results.values()):
            return "No FCF data available for analysis."

        summary_parts = []

        for fcf_type, values in fcf_results.items():
            if values and len(values) >= 2:
                latest = values[-1]
                previous = values[-2]
                change = ((latest - previous) / abs(previous)) * 100 if previous != 0 else 0

                summary_parts.append(f"{fcf_type}: ${latest:.1f}M (YoY: {change:+.1f}%)")

        return (
            "<br/>".join(summary_parts) if summary_parts else "Insufficient data for FCF analysis."
        )

    def _get_dcf_summary(self, dcf_results, current_price):
        """Generate DCF summary text"""
        if not dcf_results:
            return "No DCF analysis available."

        fair_value = dcf_results.get('value_per_share', 0)
        enterprise_value = dcf_results.get('enterprise_value', 0)

        summary = f"Fair Value per Share: ${fair_value:.2f}<br/>Enterprise Value: ${enterprise_value:.1f}M"

        if current_price and fair_value > 0:
            upside = ((fair_value - current_price) / current_price) * 100
            summary += f"<br/>Upside/Downside vs Current Price: {upside:+.1f}%"

        return summary

    def _create_fcf_section(self, fcf_results, fcf_plots, growth_analysis_df, fcf_data_df):
        """Create FCF analysis section"""
        story = []

        story.append(Paragraph("Free Cash Flow Analysis", self.section_style))

        # Check if any FCF data is available
        if not fcf_results or not any(fcf_results.values()):
            story.append(Paragraph("FCF Analysis Not Available", self.subsection_style))
            story.append(
                Paragraph(
                    "No FCF analysis was performed for this report. This may be due to insufficient financial data or missing key metrics required for FCF calculations.",
                    self.normal_style,
                )
            )
            story.append(Spacer(1, 20))
            return story

        # FCF Comparison Chart
        if 'fcf_comparison' in fcf_plots and fcf_plots['fcf_comparison']:
            story.append(Paragraph("FCF Comparison", self.subsection_style))
            chart_image = self._convert_plotly_to_image(fcf_plots['fcf_comparison'])
            if chart_image:
                story.append(chart_image)
            story.append(Spacer(1, 20))

        # Growth Rate Analysis
        if growth_analysis_df is not None and not growth_analysis_df.empty:
            story.append(Paragraph("Growth Rate Analysis", self.subsection_style))
            growth_table = self._dataframe_to_table(growth_analysis_df, "Growth Rate Analysis")
            if growth_table:
                story.append(growth_table)
            story.append(Spacer(1, 20))

        # FCF Data Table
        if fcf_data_df is not None and not fcf_data_df.empty:
            story.append(Paragraph("FCF Historical Data", self.subsection_style))
            fcf_table = self._dataframe_to_table(fcf_data_df, "FCF Data")
            if fcf_table:
                story.append(fcf_table)
            story.append(Spacer(1, 20))

        # Slope Analysis Chart
        if 'slope_analysis' in fcf_plots and fcf_plots['slope_analysis']:
            story.append(Paragraph("FCF Growth Trend Analysis", self.subsection_style))
            slope_image = self._convert_plotly_to_image(fcf_plots['slope_analysis'])
            if slope_image:
                story.append(slope_image)
            story.append(Spacer(1, 20))

        return story

    def _create_dcf_section(
        self, dcf_results, dcf_assumptions, dcf_plots, dcf_projections_df, current_price=None
    ):
        """Create DCF analysis section"""
        story = []

        story.append(Paragraph("DCF Valuation Analysis", self.section_style))

        # Check if DCF analysis is available
        if not dcf_results or not dcf_results.get('enterprise_value', 0):
            story.append(Paragraph("DCF Analysis Not Available", self.subsection_style))
            story.append(
                Paragraph(
                    "No DCF valuation was performed for this report. DCF analysis requires historical FCF data and user-specified assumptions for discount rates and growth projections.",
                    self.normal_style,
                )
            )
            story.append(Spacer(1, 20))
            return story

        # DCF Summary
        if dcf_results:
            story.append(Paragraph("Valuation Summary", self.subsection_style))
            summary_data = [
                ['Metric', 'Value'],
                ['Enterprise Value', f"${dcf_results.get('enterprise_value', 0):.1f}M"],
                ['Fair Value per Share', f"${dcf_results.get('value_per_share', 0):.2f}"],
                ['Terminal Value', f"${dcf_results.get('terminal_value', 0):.1f}M"],
                ['Present Value of FCF', f"${dcf_results.get('pv_fcf_total', 0):.1f}M"],
            ]

            summary_table = Table(summary_data)
            summary_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Price Comparison Table (if current price is available)
            if current_price:
                story.append(Paragraph("Fair Value vs Market Price", self.subsection_style))
                fair_value = dcf_results.get('value_per_share', 0)
                upside = (
                    ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0
                )

                # Color code the upside/downside
                if upside > 10:
                    upside_color = colors.green
                elif upside > -10:
                    upside_color = colors.orange
                else:
                    upside_color = colors.red

                comparison_data = [
                    ['Metric', 'Value'],
                    ['Current Market Price', f"${current_price:.2f}"],
                    ['DCF Fair Value', f"${fair_value:.2f}"],
                    ['Upside/(Downside)', f"{upside:+.1f}%"],
                ]

                comparison_table = Table(comparison_data)
                comparison_table.setStyle(
                    TableStyle(
                        [
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('BACKGROUND', (0, 3), (-1, 3), upside_color),  # Color the upside row
                            ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
                            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )

                story.append(comparison_table)
                story.append(Spacer(1, 20))

        # DCF Waterfall Chart
        if 'waterfall' in dcf_plots and dcf_plots['waterfall']:
            story.append(Paragraph("DCF Valuation Breakdown", self.subsection_style))
            waterfall_image = self._convert_plotly_to_image(dcf_plots['waterfall'])
            if waterfall_image:
                story.append(waterfall_image)
            story.append(Spacer(1, 20))

        # Sensitivity Analysis
        if 'sensitivity' in dcf_plots and dcf_plots['sensitivity']:
            story.append(Paragraph("Sensitivity Analysis", self.subsection_style))
            sensitivity_image = self._convert_plotly_to_image(dcf_plots['sensitivity'])
            if sensitivity_image:
                story.append(sensitivity_image)
            story.append(Spacer(1, 20))
        else:
            # Add note if sensitivity analysis wasn't performed
            story.append(Paragraph("Sensitivity Analysis", self.subsection_style))
            story.append(
                Paragraph(
                    "Sensitivity analysis was not performed for this report. This analysis tests how changes in key assumptions (discount rate and growth rates) affect the valuation outcome.",
                    self.normal_style,
                )
            )
            story.append(Spacer(1, 20))

        # DCF Projections Table
        if dcf_projections_df is not None and not dcf_projections_df.empty:
            story.append(Paragraph("DCF Projections", self.subsection_style))
            projections_table = self._dataframe_to_table(dcf_projections_df, "DCF Projections")
            if projections_table:
                story.append(projections_table)
            story.append(Spacer(1, 20))

        return story

    def _create_assumptions_section(self, dcf_assumptions, sensitivity_params, user_decisions):
        """Create comprehensive user assumptions and decisions section"""
        story = []

        story.append(Paragraph("User Assumptions & Investment Decisions", self.section_style))

        # DCF Model Assumptions
        story.append(Paragraph("DCF Model Assumptions", self.subsection_style))

        if dcf_assumptions:
            # Create comprehensive assumptions table with explanations
            assumptions_data = [['Parameter', 'Value', 'Rationale/Source']]

            # Growth Rate Assumptions
            if 'growth_rate_yr1_5' in dcf_assumptions:
                growth_1_5 = dcf_assumptions['growth_rate_yr1_5'] * 100
                assumptions_data.append(
                    [
                        'Growth Rate (Years 1-5)',
                        f"{growth_1_5:.1f}%",
                        'Based on 5-year historical average with user adjustment',
                    ]
                )

            if 'growth_rate_yr5_10' in dcf_assumptions:
                growth_5_10 = dcf_assumptions['growth_rate_yr5_10'] * 100
                assumptions_data.append(
                    [
                        'Growth Rate (Years 6-10)',
                        f"{growth_5_10:.1f}%",
                        'Conservative long-term growth assumption',
                    ]
                )

            if 'terminal_growth_rate' in dcf_assumptions:
                terminal = dcf_assumptions['terminal_growth_rate'] * 100
                assumptions_data.append(
                    ['Terminal Growth Rate', f"{terminal:.1f}%", 'Long-term GDP growth assumption']
                )

            # Discount Rate
            if 'discount_rate' in dcf_assumptions:
                discount = dcf_assumptions['discount_rate'] * 100
                assumptions_data.append(
                    [
                        'Discount Rate (WACC)',
                        f"{discount:.1f}%",
                        'Weighted Average Cost of Capital estimate',
                    ]
                )

            # FCF Type Selection
            if 'fcf_type' in dcf_assumptions:
                fcf_type = dcf_assumptions['fcf_type']
                type_explanation = {
                    'FCFF': 'Free Cash Flow to Firm - represents total firm value',
                    'FCFE': 'Free Cash Flow to Equity - represents equity value directly',
                    'LFCF': 'Levered Free Cash Flow - simplified cash flow calculation',
                }.get(fcf_type, 'Selected FCF methodology')

                assumptions_data.append(['FCF Methodology', fcf_type, type_explanation])

            # Projection Period
            if 'projection_years' in dcf_assumptions:
                proj_years = dcf_assumptions['projection_years']
                assumptions_data.append(
                    [
                        'Projection Period',
                        f"{proj_years} years",
                        'DCF projection horizon selected by user',
                    ]
                )

            # Create assumptions table
            assumptions_table = Table(
                assumptions_data, colWidths=[2.2 * inch, 1.2 * inch, 2.6 * inch]
            )
            assumptions_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]
                )
            )

            story.append(assumptions_table)
            story.append(Spacer(1, 20))

        # Sensitivity Analysis Parameters
        if sensitivity_params:
            story.append(Paragraph("Sensitivity Analysis Configuration", self.subsection_style))

            sens_data = [['Parameter', 'Range', 'Purpose']]

            if (
                'discount_rate_min' in sensitivity_params
                and 'discount_rate_max' in sensitivity_params
            ):
                dr_min = sensitivity_params['discount_rate_min'] * 100
                dr_max = sensitivity_params['discount_rate_max'] * 100
                sens_data.append(
                    [
                        'Discount Rate Range',
                        f"{dr_min:.1f}% - {dr_max:.1f}%",
                        'Test valuation sensitivity to cost of capital assumptions',
                    ]
                )

            if 'growth_rate_min' in sensitivity_params and 'growth_rate_max' in sensitivity_params:
                gr_min = sensitivity_params['growth_rate_min'] * 100
                gr_max = sensitivity_params['growth_rate_max'] * 100
                sens_data.append(
                    [
                        'Growth Rate Range',
                        f"{gr_min:.1f}% - {gr_max:.1f}%",
                        'Test valuation sensitivity to growth assumptions',
                    ]
                )

            sens_table = Table(sens_data, colWidths=[2.0 * inch, 1.5 * inch, 2.5 * inch])
            sens_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]
                )
            )

            story.append(sens_table)
            story.append(Spacer(1, 20))

        # User Investment Decisions and Rationale
        if user_decisions:
            story.append(Paragraph("Investment Decision Rationale", self.subsection_style))

            # Investment thesis
            if 'investment_thesis' in user_decisions:
                thesis_text = f"<b>Investment Thesis:</b><br/>{user_decisions['investment_thesis']}"
                story.append(Paragraph(thesis_text, self.normal_style))
                story.append(Spacer(1, 12))

            # Key assumptions rationale
            if 'assumptions_rationale' in user_decisions:
                rationale_text = f"<b>Key Assumptions Rationale:</b><br/>{user_decisions['assumptions_rationale']}"
                story.append(Paragraph(rationale_text, self.normal_style))
                story.append(Spacer(1, 12))

            # Risk factors considered
            if 'risk_factors' in user_decisions:
                risk_text = f"<b>Risk Factors Considered:</b><br/>{user_decisions['risk_factors']}"
                story.append(Paragraph(risk_text, self.normal_style))
                story.append(Spacer(1, 12))

        # Model Validation Notes
        story.append(Paragraph("Model Validation", self.subsection_style))
        validation_text = """
        <b>Historical Performance Check:</b><br/>
        • Growth assumptions compared against 1, 3, 5, and 10-year historical averages<br/>
        • FCF methodology selected based on company characteristics and data availability<br/>
        • Discount rate benchmarked against industry and market conditions<br/><br/>
        
        <b>Reasonableness Tests:</b><br/>
        • Terminal growth rate not exceeding long-term GDP growth<br/>
        • Discount rate reflecting appropriate risk premium<br/>
        • Growth rates declining over time to sustainable levels<br/>
        """

        story.append(Paragraph(validation_text, self.normal_style))

        return story

    def _create_appendix(self, dcf_assumptions):
        """Create appendix with assumptions and methodology"""
        story = []

        story.append(Paragraph("Appendix: DCF Assumptions & Methodology", self.section_style))

        # DCF Assumptions
        if dcf_assumptions:
            story.append(Paragraph("DCF Assumptions Used", self.subsection_style))

            assumptions_data = [['Parameter', 'Value']]
            for key, value in dcf_assumptions.items():
                if isinstance(value, float):
                    if 'rate' in key.lower() or 'growth' in key.lower():
                        formatted_value = f"{value:.1%}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)

                # Format key for display
                display_key = key.replace('_', ' ').title()
                assumptions_data.append([display_key, formatted_value])

            assumptions_table = Table(assumptions_data)
            assumptions_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(assumptions_table)
            story.append(Spacer(1, 20))

        # Methodology
        story.append(Paragraph("Methodology", self.subsection_style))
        methodology_text = """
        <b>FCF Calculation Methods:</b><br/>
        • FCFF (Free Cash Flow to Firm): EBIT(1-Tax Rate) + D&A - Working Capital Change - CapEx<br/>
        • FCFE (Free Cash Flow to Equity): Net Income + D&A - Working Capital Change - CapEx + Net Borrowing<br/>
        • LFCF (Levered Free Cash Flow): Operating Cash Flow - CapEx<br/><br/>
        
        <b>DCF Valuation:</b><br/>
        • Projects future free cash flows based on historical growth trends<br/>
        • Calculates terminal value using Gordon Growth Model<br/>
        • Discounts all cash flows to present value using weighted average cost of capital<br/>
        • Adjusts enterprise value for net debt to derive equity value per share<br/><br/>
        
        <b>Sensitivity Analysis:</b><br/>
        • Tests valuation sensitivity to changes in growth rate and discount rate assumptions<br/>
        • Provides upside/downside scenarios relative to current market price<br/>
        """

        story.append(Paragraph(methodology_text, self.normal_style))

        return story

    def _convert_plotly_to_image(self, fig, width=6.5 * inch, height=4.5 * inch):
        """Convert Plotly figure to ReportLab Image with improved quality"""
        try:
            if fig is None:
                logger.warning("Received None figure for conversion")
                return None

            # Enhance figure for PDF conversion
            fig.update_layout(
                font=dict(family="Arial", size=10),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=60, t=60, b=60),
            )

            # Convert plotly figure to image bytes with high quality
            img_bytes = pio.to_image(fig, format="png", width=1000, height=700, scale=2)

            # Create ReportLab Image from bytes
            img_buffer = io.BytesIO(img_bytes)
            img = Image(img_buffer, width=width, height=height)

            return img

        except Exception as e:
            logger.error(f"Error converting plot to image: {e}")
            return None

    def _dataframe_to_table(self, df, title=""):
        """Convert pandas DataFrame to ReportLab Table"""
        try:
            if df is None or df.empty:
                logger.warning(f"Empty or None DataFrame for table: {title}")
                return None

            # Validate DataFrame shape
            logger.info(f"Creating table '{title}' with shape: {df.shape}")

            # Convert DataFrame to list of lists
            data = [df.columns.tolist()]  # Header row
            data.extend(df.values.tolist())  # Data rows

            # Create table
            table = Table(data)

            # Apply styling
            table.setStyle(
                TableStyle(
                    [
                        # Header styling
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        # Data styling
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            return table

        except Exception as e:
            logger.error(f"Error converting DataFrame to table: {e}")
            return None
