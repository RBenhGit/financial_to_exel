"""
ML Forecasting UI Components
=============================

Streamlit UI components for machine learning-based financial forecasting.
Provides interfaces for model training, validation, and prediction visualization.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Import ML framework components
from core.analysis.ml.models.model_manager import MLModelManager
from core.analysis.ml.forecasting.financial_forecaster import FinancialForecaster
from core.analysis.ml.validation.model_validator import ModelValidator
from core.analysis.engines.financial_calculations import FinancialCalculator

logger = logging.getLogger(__name__)

def render_ml_forecasting_tab(selected_symbol: str, financial_calculator: FinancialCalculator):
    """
    Render the ML Forecasting tab in the Streamlit app

    Parameters:
    -----------
    selected_symbol : str
        Selected stock ticker symbol
    financial_calculator : FinancialCalculator
        Financial calculator instance with loaded data
    """
    st.header("🤖 Machine Learning Forecasting")

    if not selected_symbol:
        st.warning("Please select a company symbol to begin ML forecasting.")
        return

    # Initialize ML components
    ml_manager = MLModelManager(financial_calculator)
    forecaster = FinancialForecaster(financial_calculator, ml_manager)
    validator = ModelValidator()

    # Create tabs for different ML functionalities
    ml_tab1, ml_tab2, ml_tab3, ml_tab4 = st.tabs([
        "📈 Forecasting",
        "🔧 Model Training",
        "📊 Model Performance",
        "⚙️ Settings"
    ])

    with ml_tab1:
        render_forecasting_interface(forecaster, selected_symbol)

    with ml_tab2:
        render_model_training_interface(ml_manager, financial_calculator, selected_symbol)

    with ml_tab3:
        render_model_performance_interface(ml_manager, validator)

    with ml_tab4:
        render_ml_settings_interface()

def render_forecasting_interface(forecaster: FinancialForecaster, ticker: str):
    """Render the forecasting interface"""
    st.subheader("📈 Financial Forecasting")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        forecast_type = st.selectbox(
            "Forecast Type",
            ["Free Cash Flow", "Revenue", "Comprehensive Valuation"],
            help="Select the type of financial forecast to generate"
        )

    with col2:
        forecast_periods = st.number_input(
            "Forecast Periods",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of periods to forecast"
        )

    with col3:
        confidence_level = st.select_slider(
            "Confidence Level",
            options=[0.90, 0.95, 0.99],
            value=0.95,
            format_func=lambda x: f"{x:.0%}",
            help="Confidence level for prediction intervals"
        )

    if st.button("Generate Forecast", type="primary"):
        with st.spinner(f"Generating {forecast_type.lower()} forecast for {ticker}..."):
            try:
                if forecast_type == "Free Cash Flow":
                    forecast_result = forecaster.forecast_fcf(
                        ticker, forecast_periods, confidence_level
                    )
                    if forecast_result:
                        display_fcf_forecast_results(forecast_result)
                    else:
                        st.error("Failed to generate FCF forecast. Please check data availability.")

                elif forecast_type == "Revenue":
                    forecast_result = forecaster.forecast_revenue(
                        ticker, forecast_periods, confidence_level
                    )
                    if forecast_result:
                        display_revenue_forecast_results(forecast_result)
                    else:
                        st.error("Failed to generate revenue forecast. Please check data availability.")

                elif forecast_type == "Comprehensive Valuation":
                    valuation_forecast = forecaster.forecast_valuation(ticker, forecast_periods)
                    if valuation_forecast:
                        display_comprehensive_valuation_forecast(valuation_forecast)
                    else:
                        st.error("Failed to generate comprehensive valuation forecast.")

            except Exception as e:
                logger.error(f"Error generating forecast: {e}")
                st.error(f"Error generating forecast: {str(e)}")

def display_fcf_forecast_results(forecast_result):
    """Display FCF forecast results with interactive visualizations"""
    st.subheader("💰 Free Cash Flow Forecast Results")

    # Create forecast visualization
    fig = create_forecast_chart(
        forecast_result.forecast_periods,
        forecast_result.forecast_values,
        forecast_result.confidence_intervals,
        "Free Cash Flow",
        "FCF ($)",
        "FCF Forecast"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display forecast table
    forecast_df = pd.DataFrame({
        'Period': forecast_result.forecast_periods,
        'FCF Forecast ($)': [f"${val:,.0f}" for val in forecast_result.forecast_values],
        'Lower Bound ($)': [f"${ci[0]:,.0f}" for ci in forecast_result.confidence_intervals],
        'Upper Bound ($)': [f"${ci[1]:,.0f}" for ci in forecast_result.confidence_intervals]
    })

    st.dataframe(forecast_df, use_container_width=True)

    # Model information and assumptions
    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**Model Used:** {forecast_result.model_used}")
        if forecast_result.accuracy_metrics:
            st.metric(
                "Model R² Score",
                f"{forecast_result.accuracy_metrics.get('r2_score', 0):.3f}"
            )

    with col2:
        if forecast_result.assumptions:
            with st.expander("📋 Forecast Assumptions"):
                for key, value in forecast_result.assumptions.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    # Risk factors
    if forecast_result.risk_factors:
        with st.expander("⚠️ Risk Factors"):
            for risk in forecast_result.risk_factors:
                st.write(f"• {risk}")

def display_revenue_forecast_results(forecast_result):
    """Display revenue forecast results"""
    st.subheader("📊 Revenue Forecast Results")

    # Create forecast visualization
    fig = create_forecast_chart(
        forecast_result.forecast_periods,
        forecast_result.forecast_values,
        forecast_result.confidence_intervals,
        "Revenue",
        "Revenue ($)",
        "Revenue Forecast"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Calculate growth rates
    growth_rates = []
    for i in range(1, len(forecast_result.forecast_values)):
        growth = (forecast_result.forecast_values[i] / forecast_result.forecast_values[i-1] - 1) * 100
        growth_rates.append(growth)

    # Display forecast table with growth rates
    forecast_data = {
        'Period': forecast_result.forecast_periods,
        'Revenue Forecast ($)': [f"${val:,.0f}" for val in forecast_result.forecast_values],
        'YoY Growth (%)': ['N/A'] + [f"{gr:.1f}%" for gr in growth_rates],
        'Lower Bound ($)': [f"${ci[0]:,.0f}" for ci in forecast_result.confidence_intervals],
        'Upper Bound ($)': [f"${ci[1]:,.0f}" for ci in forecast_result.confidence_intervals]
    }

    forecast_df = pd.DataFrame(forecast_data)
    st.dataframe(forecast_df, use_container_width=True)

def display_comprehensive_valuation_forecast(valuation_forecast):
    """Display comprehensive valuation forecast results"""
    st.subheader("🏢 Comprehensive Valuation Forecast")

    col1, col2 = st.columns(2)

    with col1:
        if valuation_forecast.fcf_forecast:
            st.metric(
                "FCF Model Reliability",
                f"{valuation_forecast.forecast_reliability:.1%}"
            )

    with col2:
        if valuation_forecast.combined_valuation_range:
            low, high = valuation_forecast.combined_valuation_range
            st.metric(
                "Valuation Range",
                f"${low:,.0f} - ${high:,.0f}"
            )

    # Create tabs for different forecast components
    if any([valuation_forecast.fcf_forecast, valuation_forecast.revenue_forecast,
            valuation_forecast.dcf_forecast]):

        forecast_tabs = st.tabs(["FCF", "Revenue", "DCF Valuation"])

        with forecast_tabs[0]:
            if valuation_forecast.fcf_forecast:
                display_fcf_forecast_results(valuation_forecast.fcf_forecast)
            else:
                st.info("FCF forecast not available")

        with forecast_tabs[1]:
            if valuation_forecast.revenue_forecast:
                display_revenue_forecast_results(valuation_forecast.revenue_forecast)
            else:
                st.info("Revenue forecast not available")

        with forecast_tabs[2]:
            if valuation_forecast.dcf_forecast:
                st.subheader("🎯 DCF Valuation Forecast")
                if valuation_forecast.dcf_forecast.forecast_values:
                    st.metric(
                        "DCF Valuation",
                        f"${valuation_forecast.dcf_forecast.forecast_values[0]:,.0f}"
                    )

                    # Display assumptions
                    if valuation_forecast.dcf_forecast.assumptions:
                        with st.expander("DCF Assumptions"):
                            for key, value in valuation_forecast.dcf_forecast.assumptions.items():
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:
                st.info("DCF valuation forecast not available")

def create_forecast_chart(periods, values, confidence_intervals, metric_name, y_label, title):
    """Create an interactive forecast chart with confidence intervals"""
    fig = go.Figure()

    # Add confidence interval as filled area
    upper_bounds = [ci[1] for ci in confidence_intervals]
    lower_bounds = [ci[0] for ci in confidence_intervals]

    # Create x values for the confidence interval
    x_values = list(range(len(periods)))

    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=x_values + x_values[::-1],
        y=upper_bounds + lower_bounds[::-1],
        fill='toself',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='Confidence Interval'
    ))

    # Add forecast line
    fig.add_trace(go.Scatter(
        x=x_values,
        y=values,
        mode='lines+markers',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        name=f'{metric_name} Forecast',
        hovertemplate=f'<b>Period:</b> %{{customdata}}<br>' +
                     f'<b>{metric_name}:</b> $%{{y:,.0f}}<extra></extra>',
        customdata=periods
    ))

    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=20)
        ),
        xaxis=dict(
            title="Forecast Period",
            tickvals=x_values,
            ticktext=periods,
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            tickformat='$,.0f'
        ),
        hovermode='x unified',
        showlegend=True,
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def render_model_training_interface(ml_manager: MLModelManager,
                                  financial_calculator: FinancialCalculator,
                                  ticker: str):
    """Render the model training interface"""
    st.subheader("🔧 Model Training & Management")

    # Model training section
    st.write("### Train New Model")

    col1, col2 = st.columns(2)

    with col1:
        target_variable = st.selectbox(
            "Target Variable",
            ["fcf", "revenue", "net_income", "operating_cash_flow"],
            help="Select the financial metric to predict"
        )

        model_type = st.selectbox(
            "Model Type",
            ["random_forest", "linear", "gradient_boost"],
            help="Select the machine learning algorithm"
        )

    with col2:
        test_size = st.slider(
            "Test Size",
            min_value=0.1,
            max_value=0.4,
            value=0.2,
            step=0.05,
            help="Proportion of data for testing"
        )

        cv_folds = st.number_input(
            "Cross-Validation Folds",
            min_value=3,
            max_value=10,
            value=5,
            help="Number of cross-validation folds"
        )

    if st.button("Train Model", type="primary"):
        with st.spinner(f"Training {model_type} model for {target_variable}..."):
            try:
                # Prepare training data
                training_data = prepare_training_data(financial_calculator, ticker)

                if training_data.empty:
                    st.error("No training data available. Please ensure financial data is loaded.")
                    return

                # Define feature columns based on available data
                feature_columns = [col for col in training_data.columns
                                 if col != target_variable and col not in ['date', 'period']]

                if not feature_columns:
                    st.error("No feature columns available for training.")
                    return

                # Train the model
                model_id = ml_manager.train_financial_predictor(
                    target_variable=target_variable,
                    feature_columns=feature_columns,
                    data=training_data,
                    ticker=ticker,
                    model_type=model_type,
                    test_size=test_size,
                    cv_folds=cv_folds
                )

                if model_id:
                    st.success(f"Model trained successfully! Model ID: {model_id}")

                    # Display model performance
                    performance = ml_manager.get_model_performance(model_id)
                    display_model_performance_summary(performance)
                else:
                    st.error("Model training failed. Please check the logs for details.")

            except Exception as e:
                logger.error(f"Error training model: {e}")
                st.error(f"Error training model: {str(e)}")

def render_model_performance_interface(ml_manager: MLModelManager, validator: ModelValidator):
    """Render the model performance interface"""
    st.subheader("📊 Model Performance & Validation")

    # List existing models
    models = ml_manager.list_models()

    if not models:
        st.info("No trained models available. Train a model first in the Model Training tab.")
        return

    # Model selection
    model_options = [f"{m['model_id']} - {m['target_variable']}" for m in models]
    selected_model = st.selectbox("Select Model", model_options)

    if selected_model:
        model_id = selected_model.split(" - ")[0]
        model_info = next(m for m in models if m['model_id'] == model_id)

        # Display model information
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Target Variable", model_info['target_variable'])

        with col2:
            st.metric("Model Type", model_info['model_type'])

        with col3:
            training_date = pd.to_datetime(model_info['training_date']).strftime('%Y-%m-%d')
            st.metric("Training Date", training_date)

        # Performance metrics
        if model_info.get('performance_metrics'):
            st.write("### Performance Metrics")
            metrics = model_info['performance_metrics']

            metric_cols = st.columns(len(metrics))
            for i, (metric, value) in enumerate(metrics.items()):
                with metric_cols[i]:
                    st.metric(metric.upper(), f"{value:.4f}")

        # Bias test results
        if model_info.get('bias_test_results'):
            with st.expander("🔍 Bias Test Results"):
                bias_results = model_info['bias_test_results']
                for key, value in bias_results.items():
                    if isinstance(value, dict):
                        st.write(f"**{key.replace('_', ' ').title()}:**")
                        for sub_key, sub_value in value.items():
                            st.write(f"  - {sub_key}: {sub_value}")
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")

def render_ml_settings_interface():
    """Render the ML settings interface"""
    st.subheader("⚙️ ML Settings & Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Model Storage")
        st.info("Models are automatically saved to `data/models/`")

        st.write("### Auto-Retraining")
        auto_retrain = st.checkbox(
            "Enable automatic model retraining",
            value=False,
            help="Automatically retrain models when new data is available"
        )

        if auto_retrain:
            retrain_frequency = st.selectbox(
                "Retraining Frequency",
                ["Weekly", "Monthly", "Quarterly"],
                help="How often to retrain models"
            )

    with col2:
        st.write("### Performance Thresholds")

        min_r2_score = st.slider(
            "Minimum R² Score",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
            help="Minimum acceptable R² score for model validation"
        )

        max_bias = st.slider(
            "Maximum Bias",
            min_value=0.0,
            max_value=0.5,
            value=0.1,
            step=0.01,
            help="Maximum acceptable bias in model predictions"
        )

    if st.button("Save Settings"):
        # Save settings to session state or configuration file
        st.session_state.ml_settings = {
            'auto_retrain': auto_retrain,
            'retrain_frequency': retrain_frequency if auto_retrain else None,
            'min_r2_score': min_r2_score,
            'max_bias': max_bias
        }
        st.success("Settings saved successfully!")

def prepare_training_data(financial_calculator: FinancialCalculator, ticker: str) -> pd.DataFrame:
    """Prepare training data from financial calculator"""
    try:
        # Calculate FCF and get financial metrics
        fcf_results = financial_calculator.calculate_all_fcf_types()
        metrics = financial_calculator.get_financial_metrics()

        # Create basic training data structure
        data_dict = {}

        # Add FCF data
        if fcf_results:
            for fcf_type, values in fcf_results.items():
                if isinstance(values, list) and values:
                    data_dict[fcf_type.lower()] = values

        # Add basic financial metrics if available
        if metrics:
            # Add scalar metrics as repeated values (simplified approach)
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and not pd.isna(value):
                    # Repeat the value for the length of FCF data
                    if data_dict:
                        data_length = len(next(iter(data_dict.values())))
                        data_dict[key] = [value] * data_length

        # Create DataFrame
        if data_dict:
            # Ensure all series have the same length
            min_length = min(len(values) for values in data_dict.values() if isinstance(values, list))
            aligned_data = {key: values[:min_length] if isinstance(values, list) else values
                          for key, values in data_dict.items()}

            df = pd.DataFrame(aligned_data)

            # Add engineered features
            if 'fcfe' in df.columns:
                df['fcf'] = df['fcfe']  # Use FCFE as primary FCF
                df['fcf_growth'] = df['fcf'].pct_change()

            # Clean the data
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)

            return df

        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error preparing training data: {e}")
        return pd.DataFrame()

def display_model_performance_summary(performance: Dict[str, Any]):
    """Display a summary of model performance"""
    st.write("### Model Performance Summary")

    col1, col2, col3 = st.columns(3)

    metrics = performance.get('performance_metrics', {})

    with col1:
        if 'r2' in metrics:
            st.metric("R² Score", f"{metrics['r2']:.4f}")
        elif 'r2_score' in metrics:
            st.metric("R² Score", f"{metrics['r2_score']:.4f}")

    with col2:
        if 'mse' in metrics:
            st.metric("MSE", f"{metrics['mse']:.2e}")

    with col3:
        if 'cv_mean' in metrics:
            st.metric("CV Mean", f"{metrics['cv_mean']:.4f}")

    # Feature importance if available
    if performance.get('features'):
        with st.expander("📊 Feature Information"):
            st.write("**Features used in model:**")
            for i, feature in enumerate(performance['features'], 1):
                st.write(f"{i}. {feature}")