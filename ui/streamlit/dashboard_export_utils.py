"""
Dashboard Export and Sharing Utilities

Comprehensive export functionality for financial dashboard including:
- PDF dashboard snapshots
- CSV/Excel data exports
- Shareable URLs with embedded filters
- Email sharing capabilities
- Print-friendly formatting
"""

import streamlit as st
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import json
import io
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any
import zipfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import urllib.parse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class DashboardExporter:
    """Comprehensive dashboard export and sharing functionality"""

    def __init__(self):
        """Initialize the dashboard exporter"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.export_formats = {
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json',
            'pdf': 'application/pdf',
            'zip': 'application/zip'
        }

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for PDF reports"""
        self.title_style = ParagraphStyle(
            'DashboardTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#1f77b4'),
        )

        self.section_style = ParagraphStyle(
            'DashboardSection',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50'),
        )

        self.normal_style = ParagraphStyle(
            'DashboardNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leading=14
        )

    def export_dashboard_to_pdf(
        self,
        dashboard_data: Dict[str, Any],
        company_info: Dict[str, str],
        charts: List[go.Figure],
        include_charts: bool = True,
        include_data_tables: bool = True
    ) -> bytes:
        """
        Export dashboard as PDF snapshot

        Args:
            dashboard_data: Dictionary containing dashboard data
            company_info: Company information (name, ticker, etc.)
            charts: List of Plotly figures to include
            include_charts: Whether to include chart visualizations
            include_data_tables: Whether to include data tables

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # Title page
        title = f"Financial Dashboard Report - {company_info.get('name', 'Unknown Company')}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))

        # Company information
        if company_info:
            story.append(Paragraph("Company Information", self.section_style))
            info_data = [
                ['Ticker', company_info.get('ticker', 'N/A')],
                ['Company Name', company_info.get('name', 'N/A')],
                ['Report Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Data Source', company_info.get('source', 'Mixed Sources')]
            ]
            info_table = Table(info_data)
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))

        # Financial Ratios Section
        if 'financial_ratios' in dashboard_data and include_data_tables:
            story.append(Paragraph("Financial Ratios Summary", self.section_style))
            ratios_df = dashboard_data['financial_ratios']
            if not ratios_df.empty:
                # Convert DataFrame to table data
                table_data = [ratios_df.columns.tolist()]
                table_data.extend(ratios_df.values.tolist())

                ratios_table = Table(table_data)
                ratios_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(ratios_table)
                story.append(Spacer(1, 20))

        # Charts Section
        if charts and include_charts:
            story.append(Paragraph("Financial Charts", self.section_style))

            for i, fig in enumerate(charts):
                try:
                    # Convert Plotly figure to image
                    img_bytes = pio.to_image(fig, format="png", width=600, height=400)
                    img_buffer = io.BytesIO(img_bytes)
                    img = Image(ImageReader(img_buffer), width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))

                    # Add page break after every 2 charts
                    if (i + 1) % 2 == 0 and i < len(charts) - 1:
                        story.append(PageBreak())
                except Exception as e:
                    logger.warning(f"Failed to include chart {i}: {e}")
                    story.append(Paragraph(f"Chart {i+1} could not be rendered", self.normal_style))
                    story.append(Spacer(1, 15))

        # Additional Data Tables
        if include_data_tables:
            for section_name, data in dashboard_data.items():
                if section_name != 'financial_ratios' and isinstance(data, pd.DataFrame) and not data.empty:
                    story.append(PageBreak())
                    story.append(Paragraph(f"{section_name.replace('_', ' ').title()}", self.section_style))

                    # Limit table size for PDF
                    display_data = data.head(20) if len(data) > 20 else data
                    table_data = [display_data.columns.tolist()]
                    table_data.extend(display_data.values.tolist())

                    data_table = Table(table_data)
                    data_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(data_table)
                    story.append(Spacer(1, 20))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def export_data_to_excel(
        self,
        dashboard_data: Dict[str, pd.DataFrame],
        filename: Optional[str] = None
    ) -> bytes:
        """
        Export dashboard data to Excel with multiple sheets

        Args:
            dashboard_data: Dictionary of DataFrames to export
            filename: Optional filename

        Returns:
            Excel file bytes
        """
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, df in dashboard_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # Clean sheet name (Excel requirements)
                    clean_sheet_name = sheet_name.replace('_', ' ').title()[:31]
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)

        excel_bytes = output.getvalue()
        output.close()

        return excel_bytes

    def export_data_to_csv_zip(
        self,
        dashboard_data: Dict[str, pd.DataFrame],
        company_name: str = "Company"
    ) -> bytes:
        """
        Export dashboard data as ZIP file containing multiple CSV files

        Args:
            dashboard_data: Dictionary of DataFrames to export
            company_name: Company name for file naming

        Returns:
            ZIP file bytes
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for data_name, df in dashboard_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_content = csv_buffer.getvalue()

                    filename = f"{company_name}_{data_name}.csv"
                    zip_file.writestr(filename, csv_content)

        zip_bytes = zip_buffer.getvalue()
        zip_buffer.close()

        return zip_bytes

    def create_shareable_url(
        self,
        filters: Dict[str, Any],
        base_url: Optional[str] = None
    ) -> str:
        """
        Create shareable URL with embedded filters

        Args:
            filters: Dictionary of filter parameters
            base_url: Base URL (if None, uses current Streamlit URL)

        Returns:
            Shareable URL string
        """
        if base_url is None:
            # Try to get current Streamlit URL
            try:
                base_url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
            except:
                base_url = "http://localhost:8501"

        # Encode filters as URL parameters
        params = {}
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, (list, tuple)):
                    params[key] = ','.join(map(str, value))
                else:
                    params[key] = str(value)

        # Create query string
        query_string = urllib.parse.urlencode(params)

        # Combine base URL with parameters
        shareable_url = f"{base_url}?{query_string}"

        return shareable_url

    def send_email_report(
        self,
        recipient_email: str,
        report_data: bytes,
        report_filename: str,
        sender_email: str,
        sender_password: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        company_name: str = "Company"
    ) -> bool:
        """
        Send email with dashboard report attachment

        Args:
            recipient_email: Recipient email address
            report_data: Report file bytes
            report_filename: Name of report file
            sender_email: Sender email address
            sender_password: Sender email password/app password
            smtp_server: SMTP server address
            smtp_port: SMTP port
            company_name: Company name for email subject

        Returns:
            Success status
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Financial Dashboard Report - {company_name}"

            # Email body
            body = f"""
            Dear Recipient,

            Please find attached the financial dashboard report for {company_name}.

            Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            Best regards,
            Financial Analysis System
            """

            msg.attach(MIMEText(body, 'plain'))

            # Attach report
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(report_data)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {report_filename}'
            )
            msg.attach(attachment)

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def create_print_friendly_view(self, dashboard_data: Dict[str, Any]) -> str:
        """
        Create print-friendly HTML view of dashboard

        Args:
            dashboard_data: Dashboard data dictionary

        Returns:
            HTML string for print-friendly view
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Financial Dashboard - Print View</title>
            <style>
                @media print {
                    .no-print { display: none; }
                    body { font-family: Arial, sans-serif; margin: 0.5in; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    .page-break { page-break-before: always; }
                    h1, h2 { color: #333; }
                    .summary-box { border: 2px solid #333; padding: 10px; margin: 10px 0; }
                }
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .summary-box { border: 2px solid #333; padding: 10px; margin: 10px 0; }
                h1, h2 { color: #333; }
            </style>
        </head>
        <body>
        """

        # Add header
        html_content += f"""
        <h1>Financial Dashboard Report</h1>
        <div class="summary-box">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Company:</strong> {dashboard_data.get('company_name', 'N/A')}</p>
            <p><strong>Ticker:</strong> {dashboard_data.get('ticker', 'N/A')}</p>
        </div>
        """

        # Add data tables
        for section_name, data in dashboard_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                html_content += f"<h2>{section_name.replace('_', ' ').title()}</h2>"
                html_content += data.to_html(classes='data-table', escape=False)
                html_content += '<div class="page-break"></div>'

        html_content += """
        </body>
        </html>
        """

        return html_content


def render_export_sharing_interface():
    """Render the export and sharing interface in Streamlit sidebar"""
    with st.sidebar.expander("📤 Export & Share", expanded=False):
        st.subheader("Dashboard Export")

        exporter = DashboardExporter()

        # Check if we have data to export
        if not hasattr(st.session_state, 'financial_calculator') or not st.session_state.financial_calculator:
            st.warning("⚠️ Load company data first to enable export")
            return

        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            ["PDF Dashboard", "Excel Data", "CSV Bundle", "Print View"],
            help="Choose export format"
        )

        # Additional options
        if export_format == "PDF Dashboard":
            include_charts = st.checkbox("Include Charts", value=True)
            include_tables = st.checkbox("Include Data Tables", value=True)

            if st.button("📄 Generate PDF"):
                try:
                    # Collect dashboard data
                    dashboard_data = collect_dashboard_data()
                    company_info = get_current_company_info()
                    charts = get_current_charts()

                    pdf_bytes = exporter.export_dashboard_to_pdf(
                        dashboard_data=dashboard_data,
                        company_info=company_info,
                        charts=charts if include_charts else [],
                        include_charts=include_charts,
                        include_data_tables=include_tables
                    )

                    filename = f"dashboard_{company_info.get('ticker', 'report')}_{datetime.now().strftime('%Y%m%d')}.pdf"

                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf"
                    )

                    st.success("✅ PDF generated successfully!")

                except Exception as e:
                    st.error(f"❌ PDF generation failed: {e}")

        elif export_format == "Excel Data":
            if st.button("📊 Generate Excel"):
                try:
                    dashboard_data = collect_dashboard_data()
                    company_info = get_current_company_info()

                    excel_bytes = exporter.export_data_to_excel(dashboard_data)

                    filename = f"dashboard_data_{company_info.get('ticker', 'data')}_{datetime.now().strftime('%Y%m%d')}.xlsx"

                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    st.success("✅ Excel file generated!")

                except Exception as e:
                    st.error(f"❌ Excel generation failed: {e}")

        elif export_format == "CSV Bundle":
            if st.button("📦 Generate CSV Bundle"):
                try:
                    dashboard_data = collect_dashboard_data()
                    company_info = get_current_company_info()

                    zip_bytes = exporter.export_data_to_csv_zip(
                        dashboard_data,
                        company_info.get('name', 'Company')
                    )

                    filename = f"dashboard_csv_bundle_{company_info.get('ticker', 'data')}_{datetime.now().strftime('%Y%m%d')}.zip"

                    st.download_button(
                        label="📥 Download ZIP",
                        data=zip_bytes,
                        file_name=filename,
                        mime="application/zip"
                    )

                    st.success("✅ CSV bundle created!")

                except Exception as e:
                    st.error(f"❌ CSV bundle generation failed: {e}")

        elif export_format == "Print View":
            if st.button("🖨️ Generate Print View"):
                try:
                    dashboard_data = collect_dashboard_data()
                    html_content = exporter.create_print_friendly_view(dashboard_data)

                    # Display print view in new tab/window
                    st.components.v1.html(
                        f"""
                        <script>
                        var printWindow = window.open('', '_blank');
                        printWindow.document.write(`{html_content}`);
                        printWindow.document.close();
                        printWindow.focus();
                        </script>
                        """,
                        height=0
                    )

                    st.success("✅ Print view opened in new window!")

                except Exception as e:
                    st.error(f"❌ Print view generation failed: {e}")

        # Shareable URL section
        st.subheader("Share Dashboard")

        if st.button("🔗 Generate Shareable URL"):
            try:
                current_filters = get_current_filters()
                shareable_url = exporter.create_shareable_url(current_filters)

                st.text_area(
                    "Shareable URL:",
                    value=shareable_url,
                    height=100,
                    help="Copy this URL to share current dashboard view"
                )

                st.success("✅ Shareable URL generated!")

            except Exception as e:
                st.error(f"❌ URL generation failed: {e}")

        # Email sharing (optional - requires email configuration)
        with st.expander("📧 Email Report", expanded=False):
            st.warning("⚠️ Requires email configuration")

            recipient_email = st.text_input("Recipient Email")
            sender_email = st.text_input("Your Email")
            sender_password = st.text_input("Email Password", type="password")

            if st.button("📧 Send Email") and recipient_email and sender_email and sender_password:
                try:
                    # Generate PDF for email
                    dashboard_data = collect_dashboard_data()
                    company_info = get_current_company_info()
                    charts = get_current_charts()

                    pdf_bytes = exporter.export_dashboard_to_pdf(
                        dashboard_data=dashboard_data,
                        company_info=company_info,
                        charts=charts
                    )

                    filename = f"dashboard_{company_info.get('ticker', 'report')}_{datetime.now().strftime('%Y%m%d')}.pdf"

                    success = exporter.send_email_report(
                        recipient_email=recipient_email,
                        report_data=pdf_bytes,
                        report_filename=filename,
                        sender_email=sender_email,
                        sender_password=sender_password,
                        company_name=company_info.get('name', 'Company')
                    )

                    if success:
                        st.success("✅ Email sent successfully!")
                    else:
                        st.error("❌ Email sending failed!")

                except Exception as e:
                    st.error(f"❌ Email sending failed: {e}")


def collect_dashboard_data() -> Dict[str, Any]:
    """Collect current dashboard data for export"""
    data = {}

    try:
        # Get financial calculator data
        if hasattr(st.session_state, 'financial_calculator') and st.session_state.financial_calculator:
            calc = st.session_state.financial_calculator

            # Financial ratios
            if hasattr(calc, 'financial_ratios_df') and calc.financial_ratios_df is not None:
                data['financial_ratios'] = calc.financial_ratios_df

            # FCF data
            if hasattr(calc, 'fcf_data') and calc.fcf_data:
                data['fcf_analysis'] = pd.DataFrame(calc.fcf_data)

            # DCF results
            if hasattr(st.session_state, 'dcf_results') and st.session_state.dcf_results:
                dcf_df = pd.DataFrame([st.session_state.dcf_results])
                data['dcf_valuation'] = dcf_df

        # Company info
        data['company_name'] = getattr(st.session_state, 'company_name', 'Unknown')
        data['ticker'] = getattr(st.session_state, 'ticker', 'N/A')

    except Exception as e:
        logger.warning(f"Error collecting dashboard data: {e}")

    return data


def get_current_company_info() -> Dict[str, str]:
    """Get current company information"""
    return {
        'name': getattr(st.session_state, 'company_name', 'Unknown Company'),
        'ticker': getattr(st.session_state, 'ticker', 'N/A'),
        'source': 'Mixed Sources'
    }


def get_current_charts() -> List[go.Figure]:
    """Get current dashboard charts"""
    charts = []

    try:
        # Try to get charts from session state
        if hasattr(st.session_state, 'dashboard_charts') and st.session_state.dashboard_charts:
            charts.extend(st.session_state.dashboard_charts)

    except Exception as e:
        logger.warning(f"Error collecting charts: {e}")

    return charts


def get_current_filters() -> Dict[str, Any]:
    """Get current dashboard filters for URL sharing"""
    filters = {}

    try:
        # Company selection
        if hasattr(st.session_state, 'ticker') and st.session_state.ticker:
            filters['ticker'] = st.session_state.ticker

        # Data source selection
        if hasattr(st.session_state, 'data_source') and st.session_state.data_source:
            filters['data_source'] = st.session_state.data_source

        # Analysis type
        if hasattr(st.session_state, 'analysis_type') and st.session_state.analysis_type:
            filters['analysis_type'] = st.session_state.analysis_type

    except Exception as e:
        logger.warning(f"Error collecting filters: {e}")

    return filters