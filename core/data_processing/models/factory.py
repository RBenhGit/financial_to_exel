"""
Financial Model Factory
=======================

Factory methods for creating financial statement models from various data sources
including Excel files, API responses, and raw dictionaries.

This module provides:
- Source-agnostic model creation
- Data validation and cleaning
- Error handling and fallback mechanisms
- Batch processing capabilities
- Integration with existing data processors
"""

from typing import Dict, Any, List, Optional, Union, Type
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging

from .base import BaseFinancialStatementModel, DataSource, Currency
from .income_statement import IncomeStatementModel
from .balance_sheet import BalanceSheetModel
from .cash_flow import CashFlowStatementModel

logger = logging.getLogger(__name__)


class ModelCreationError(Exception):
    """Custom exception for model creation errors"""
    pass


class FinancialModelFactory:
    """
    Factory class for creating financial statement models from various sources
    """

    @staticmethod
    def _clean_numeric_value(value: Any) -> Optional[Decimal]:
        """
        Clean and convert numeric values to Decimal

        Args:
            value: Raw value from data source

        Returns:
            Cleaned Decimal value or None
        """
        if value is None or value == "" or value == "N/A":
            return None

        if isinstance(value, (int, float)):
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError):
                logger.warning(f"Could not convert numeric value: {value}")
                return None

        if isinstance(value, str):
            # Remove common formatting characters
            cleaned = value.replace(",", "").replace("$", "").replace("(", "-").replace(")", "").strip()

            if cleaned in ["", "-", "N/A", "n/a", "None", "null"]:
                return None

            try:
                return Decimal(cleaned)
            except (InvalidOperation, ValueError):
                logger.warning(f"Could not convert string value to decimal: {value}")
                return None

        if isinstance(value, Decimal):
            return value

        logger.warning(f"Unsupported value type for numeric conversion: {type(value)}")
        return None

    @staticmethod
    def _normalize_field_name(field_name: str, data_source: DataSource) -> str:
        """
        Normalize field names from different sources to standard model field names

        Args:
            field_name: Original field name from source
            data_source: Source of the data

        Returns:
            Normalized field name for model
        """
        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = field_name.lower().replace(" ", "_").replace("-", "_").replace("&", "and")
        normalized = normalized.replace("(", "").replace(")", "").replace("/", "_")

        # Common field name mappings
        field_mappings = {
            # Revenue variants
            "total_revenue": "revenue",
            "net_sales": "revenue",
            "total_revenues": "revenue",
            "revenues": "revenue",

            # Cost variants
            "cost_of_goods_sold": "cost_of_revenue",
            "cogs": "cost_of_revenue",
            "cost_of_sales": "cost_of_revenue",

            # Asset variants
            "total_current_assets": "current_assets",
            "cash_and_cash_equivalents": "cash_and_equivalents",
            "cash_short_term_investments": "cash_and_equivalents",
            "net_receivables": "accounts_receivable",
            "property_plant_and_equipment": "property_plant_equipment",
            "pp_e": "property_plant_equipment",

            # Liability variants
            "total_current_liabilities": "current_liabilities",
            "total_liab": "total_liabilities",
            "total_stockholder_equity": "shareholders_equity",
            "stockholders_equity": "shareholders_equity",
            "total_stockholders_equity": "shareholders_equity",

            # Cash flow variants
            "operating_cash_flow": "operating_cash_flow",
            "cash_flow_from_operations": "operating_cash_flow",
            "cash_from_operating_activities": "operating_cash_flow",
            "net_cash_from_operations": "operating_cash_flow",

            "investing_cash_flow": "investing_cash_flow",
            "cash_flow_from_investing": "investing_cash_flow",
            "cash_from_investing_activities": "investing_cash_flow",
            "net_cash_from_investing": "investing_cash_flow",

            "financing_cash_flow": "financing_cash_flow",
            "cash_flow_from_financing": "financing_cash_flow",
            "cash_from_financing_activities": "financing_cash_flow",
            "net_cash_from_financing": "financing_cash_flow",

            # Other common variants
            "shares_outstanding": "shares_outstanding",
            "weighted_average_shares": "weighted_avg_shares",
            "basic_eps": "earnings_per_share",
            "eps": "earnings_per_share"
        }

        return field_mappings.get(normalized, normalized)

    @classmethod
    def create_income_statement(
        cls,
        data: Dict[str, Any],
        data_source: Optional[DataSource] = None,
        **kwargs
    ) -> IncomeStatementModel:
        """
        Create an IncomeStatementModel from raw data

        Args:
            data: Raw financial data dictionary
            data_source: Source of the data (for field mapping)
            **kwargs: Additional model parameters

        Returns:
            IncomeStatementModel instance

        Raises:
            ModelCreationError: If model creation fails
        """
        try:
            # Normalize data
            normalized_data = cls._normalize_data(data, data_source or DataSource.MANUAL)

            # Add metadata
            if data_source:
                normalized_data['data_source'] = data_source

            # Merge with any additional parameters
            normalized_data.update(kwargs)

            # Create model
            model = IncomeStatementModel(**normalized_data)

            # Calculate derived fields
            model.calculate_gross_profit()
            model.calculate_eps()
            model.calculate_effective_tax_rate()
            model.calculate_ebitda()

            logger.info(f"Successfully created income statement for {model.company_ticker}")
            return model

        except Exception as e:
            logger.error(f"Failed to create income statement model: {str(e)}")
            raise ModelCreationError(f"Income statement creation failed: {str(e)}")

    @classmethod
    def create_balance_sheet(
        cls,
        data: Dict[str, Any],
        data_source: Optional[DataSource] = None,
        **kwargs
    ) -> BalanceSheetModel:
        """
        Create a BalanceSheetModel from raw data

        Args:
            data: Raw financial data dictionary
            data_source: Source of the data (for field mapping)
            **kwargs: Additional model parameters

        Returns:
            BalanceSheetModel instance

        Raises:
            ModelCreationError: If model creation fails
        """
        try:
            # Normalize data
            normalized_data = cls._normalize_data(data, data_source or DataSource.MANUAL)

            # Add metadata
            if data_source:
                normalized_data['data_source'] = data_source

            # Merge with any additional parameters
            normalized_data.update(kwargs)

            # Create model
            model = BalanceSheetModel(**normalized_data)

            # Calculate derived fields
            model.calculate_working_capital()
            model.calculate_net_debt()
            model.calculate_total_debt()
            model.calculate_tangible_book_value()

            logger.info(f"Successfully created balance sheet for {model.company_ticker}")
            return model

        except Exception as e:
            logger.error(f"Failed to create balance sheet model: {str(e)}")
            raise ModelCreationError(f"Balance sheet creation failed: {str(e)}")

    @classmethod
    def create_cash_flow_statement(
        cls,
        data: Dict[str, Any],
        data_source: Optional[DataSource] = None,
        **kwargs
    ) -> CashFlowStatementModel:
        """
        Create a CashFlowStatementModel from raw data

        Args:
            data: Raw financial data dictionary
            data_source: Source of the data (for field mapping)
            **kwargs: Additional model parameters

        Returns:
            CashFlowStatementModel instance

        Raises:
            ModelCreationError: If model creation fails
        """
        try:
            # Normalize data
            normalized_data = cls._normalize_data(data, data_source or DataSource.MANUAL)

            # Add metadata
            if data_source:
                normalized_data['data_source'] = data_source

            # Merge with any additional parameters
            normalized_data.update(kwargs)

            # Create model
            model = CashFlowStatementModel(**normalized_data)

            # Calculate derived fields
            model.calculate_free_cash_flow()
            model.calculate_fcfe()
            model.calculate_levered_fcf()

            logger.info(f"Successfully created cash flow statement for {model.company_ticker}")
            return model

        except Exception as e:
            logger.error(f"Failed to create cash flow statement model: {str(e)}")
            raise ModelCreationError(f"Cash flow statement creation failed: {str(e)}")

    @classmethod
    def _normalize_data(cls, data: Dict[str, Any], data_source: DataSource) -> Dict[str, Any]:
        """
        Normalize raw data to model-compatible format

        Args:
            data: Raw data dictionary
            data_source: Source of the data

        Returns:
            Normalized data dictionary
        """
        normalized = {}

        for key, value in data.items():
            # Normalize field name
            normalized_key = cls._normalize_field_name(key, data_source)

            # Clean numeric values
            if normalized_key in cls._get_numeric_fields():
                normalized_value = cls._clean_numeric_value(value)
                if normalized_value is not None:
                    normalized[normalized_key] = normalized_value
            else:
                # Handle non-numeric fields
                if value is not None and value != "":
                    normalized[normalized_key] = value

        return normalized

    @staticmethod
    def _get_numeric_fields() -> set:
        """Get set of fields that should be treated as numeric"""
        return {
            # Income statement numeric fields
            'revenue', 'total_revenue', 'cost_of_revenue', 'gross_profit',
            'operating_income', 'ebit', 'ebitda', 'net_income', 'earnings_per_share',
            'diluted_eps', 'research_development', 'selling_general_admin',
            'operating_expenses', 'interest_expense', 'tax_expense',
            'depreciation_amortization', 'shares_outstanding', 'weighted_avg_shares',

            # Balance sheet numeric fields
            'total_assets', 'current_assets', 'cash_and_equivalents',
            'accounts_receivable', 'inventory', 'property_plant_equipment',
            'long_term_investments', 'goodwill', 'intangible_assets',
            'total_liabilities', 'current_liabilities', 'accounts_payable',
            'short_term_debt', 'long_term_debt', 'total_debt',
            'shareholders_equity', 'retained_earnings', 'working_capital',

            # Cash flow numeric fields
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
            'net_change_in_cash', 'capital_expenditures', 'free_cash_flow',
            'dividends_paid', 'share_repurchases', 'cash_beginning_period',
            'cash_end_period', 'depreciation_amortization', 'change_in_working_capital'
        }

    @classmethod
    def create_complete_financials(
        cls,
        income_data: Dict[str, Any],
        balance_data: Dict[str, Any],
        cash_flow_data: Dict[str, Any],
        data_source: Optional[DataSource] = None,
        **common_kwargs
    ) -> Dict[str, BaseFinancialStatementModel]:
        """
        Create complete set of financial statements

        Args:
            income_data: Income statement data
            balance_data: Balance sheet data
            cash_flow_data: Cash flow statement data
            data_source: Data source for all statements
            **common_kwargs: Common parameters for all models

        Returns:
            Dictionary containing all three financial statement models

        Raises:
            ModelCreationError: If any model creation fails
        """
        try:
            statements = {}

            # Create income statement
            statements['income_statement'] = cls.create_income_statement(
                income_data, data_source, **common_kwargs
            )

            # Create balance sheet
            statements['balance_sheet'] = cls.create_balance_sheet(
                balance_data, data_source, **common_kwargs
            )

            # Create cash flow statement
            statements['cash_flow'] = cls.create_cash_flow_statement(
                cash_flow_data, data_source, **common_kwargs
            )

            # Cross-validate consistency between statements
            cls._validate_cross_statement_consistency(statements)

            logger.info(f"Successfully created complete financials for {statements['income_statement'].company_ticker}")
            return statements

        except Exception as e:
            logger.error(f"Failed to create complete financials: {str(e)}")
            raise ModelCreationError(f"Complete financials creation failed: {str(e)}")

    @staticmethod
    def _validate_cross_statement_consistency(statements: Dict[str, BaseFinancialStatementModel]):
        """
        Validate consistency across financial statements

        Args:
            statements: Dictionary of financial statement models

        Raises:
            ModelCreationError: If consistency checks fail
        """
        income = statements.get('income_statement')
        balance = statements.get('balance_sheet')
        cash_flow = statements.get('cash_flow')

        warnings = []

        # Check net income consistency between income statement and cash flow
        if (income and cash_flow and
            income.net_income is not None and cash_flow.net_income is not None):

            if abs(income.net_income - cash_flow.net_income) > abs(income.net_income * 0.01):
                warnings.append("Net income mismatch between income statement and cash flow statement")

        # Check cash consistency between balance sheet and cash flow
        if (balance and cash_flow and
            balance.cash_and_equivalents is not None and cash_flow.cash_end_period is not None):

            if abs(balance.cash_and_equivalents - cash_flow.cash_end_period) > abs(balance.cash_and_equivalents * 0.05):
                warnings.append("Cash balance mismatch between balance sheet and cash flow statement")

        if warnings:
            logger.warning(f"Cross-statement consistency warnings: {'; '.join(warnings)}")
            # Add warnings to model notes
            for statement in statements.values():
                if hasattr(statement, 'notes'):
                    existing_notes = statement.notes or ""
                    statement.notes = f"{existing_notes}; Cross-statement warnings: {'; '.join(warnings)}"

    @classmethod
    def create_from_excel_data(
        cls,
        excel_data: Dict[str, Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> Dict[str, BaseFinancialStatementModel]:
        """
        Create models from Excel data structure

        Args:
            excel_data: Dictionary with keys 'income_statement', 'balance_sheet', 'cash_flow'
            company_info: Common company information

        Returns:
            Dictionary of financial statement models
        """
        try:
            return cls.create_complete_financials(
                income_data=excel_data.get('income_statement', {}),
                balance_data=excel_data.get('balance_sheet', {}),
                cash_flow_data=excel_data.get('cash_flow', {}),
                data_source=DataSource.EXCEL,
                **company_info
            )
        except Exception as e:
            raise ModelCreationError(f"Excel data processing failed: {str(e)}")

    @classmethod
    def create_from_api_data(
        cls,
        api_data: Dict[str, Any],
        data_source: DataSource,
        statement_type: str
    ) -> BaseFinancialStatementModel:
        """
        Create model from API response data

        Args:
            api_data: API response data
            data_source: API source (yfinance, fmp, etc.)
            statement_type: Type of statement ('income', 'balance', 'cash_flow')

        Returns:
            Appropriate financial statement model

        Raises:
            ModelCreationError: If model creation fails
        """
        try:
            if statement_type.lower() in ['income', 'income_statement']:
                return cls.create_income_statement(api_data, data_source)
            elif statement_type.lower() in ['balance', 'balance_sheet']:
                return cls.create_balance_sheet(api_data, data_source)
            elif statement_type.lower() in ['cash_flow', 'cash']:
                return cls.create_cash_flow_statement(api_data, data_source)
            else:
                raise ValueError(f"Unknown statement type: {statement_type}")

        except Exception as e:
            raise ModelCreationError(f"API data processing failed: {str(e)}")

    @classmethod
    def batch_create_models(
        cls,
        data_list: List[Dict[str, Any]],
        model_type: Type[BaseFinancialStatementModel],
        data_source: Optional[DataSource] = None
    ) -> List[BaseFinancialStatementModel]:
        """
        Create multiple models in batch

        Args:
            data_list: List of data dictionaries
            model_type: Type of model to create
            data_source: Source of the data

        Returns:
            List of created models
        """
        models = []
        errors = []

        for i, data in enumerate(data_list):
            try:
                if model_type == IncomeStatementModel:
                    model = cls.create_income_statement(data, data_source)
                elif model_type == BalanceSheetModel:
                    model = cls.create_balance_sheet(data, data_source)
                elif model_type == CashFlowStatementModel:
                    model = cls.create_cash_flow_statement(data, data_source)
                else:
                    raise ValueError(f"Unsupported model type: {model_type}")

                models.append(model)

            except Exception as e:
                error_msg = f"Failed to create model {i}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        if errors:
            logger.warning(f"Batch creation completed with {len(errors)} errors out of {len(data_list)} items")

        return models