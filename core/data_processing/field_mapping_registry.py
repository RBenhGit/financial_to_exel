"""
Centralized Field Mapping Registry
==================================

Comprehensive centralized system for mapping source-specific field names to standardized
GeneralizedVariableDict field names. Supports multiple data sources (yfinance, FMP,
Excel, etc.) with case-insensitive lookups and fuzzy matching for Excel fields.

This module provides:
- Centralized alias mapping for all data sources
- Bidirectional lookups (source -> standard, standard -> source)
- Case-insensitive matching
- Fuzzy matching for Excel field names
- Mapping validation and conflict detection
- Thread-safe operations

Usage Example:
--------------
>>> from field_mapping_registry import FieldMappingRegistry
>>>
>>> registry = FieldMappingRegistry()
>>>
>>> # Get standard field name from source-specific name
>>> standard = registry.get_standard_field_name('yfinance', 'totalRevenue')
>>> print(standard)  # 'revenue'
>>>
>>> # Get source-specific name from standard name
>>> source_field = registry.get_source_field_name('yfinance', 'revenue')
>>> print(source_field)  # 'totalRevenue'
>>>
>>> # Case-insensitive lookup
>>> standard = registry.get_standard_field_name('excel', 'TOTAL REVENUE', case_sensitive=False)
>>> print(standard)  # 'revenue'
"""

import logging
import threading
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FieldMappingRegistry:
    """
    Centralized registry for field name mappings across all data sources.

    Thread-safe singleton implementation with comprehensive alias mapping
    for yfinance, FMP, Excel, Alpha Vantage, and Polygon data sources.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the field mapping registry"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._access_lock = threading.RLock()

        # Initialize all mapping dictionaries
        self._source_to_standard = self._build_all_mappings()
        self._standard_to_source = self._build_reverse_mappings()

        logger.info("FieldMappingRegistry initialized with comprehensive mappings")

    def _build_all_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build comprehensive source-to-standard mappings for all data sources"""
        return {
            'yfinance': self._get_yfinance_mappings(),
            'fmp': self._get_fmp_mappings(),
            'excel': self._get_excel_mappings(),
            'alpha_vantage': self._get_alpha_vantage_mappings(),
            'polygon': self._get_polygon_mappings(),
        }

    def _get_yfinance_mappings(self) -> Dict[str, str]:
        """Get comprehensive yfinance field name mappings"""
        return {
            # Required fields
            'symbol': 'ticker',
            'shortName': 'company_name',
            'longName': 'company_name',
            'currency': 'currency',
            'financialCurrency': 'currency',

            # Income Statement
            'totalRevenue': 'revenue',
            'TotalRevenue': 'revenue',
            'Revenue': 'revenue',
            'costOfRevenue': 'cost_of_revenue',
            'CostOfRevenue': 'cost_of_revenue',
            'grossProfit': 'gross_profit',
            'GrossProfit': 'gross_profit',
            'operatingExpense': 'operating_expenses',
            'OperatingExpense': 'operating_expenses',
            'researchDevelopment': 'research_and_development',
            'ResearchDevelopment': 'research_and_development',
            'sellingGeneralAdministrative': 'selling_general_administrative',
            'SellingGeneralAdministrative': 'selling_general_administrative',
            'operatingIncome': 'operating_income',
            'OperatingIncome': 'operating_income',
            'interestExpense': 'interest_expense',
            'InterestExpense': 'interest_expense',
            'otherIncomeExpenseNet': 'other_income_expense',
            'incomeBeforeTax': 'income_before_tax',
            'IncomeBeforeTax': 'income_before_tax',
            'incomeTaxExpense': 'income_tax_expense',
            'IncomeTaxExpense': 'income_tax_expense',
            'netIncome': 'net_income',
            'NetIncome': 'net_income',
            'NetIncomeCommonStockholders': 'net_income',
            'basicEPS': 'eps_basic',
            'dilutedEPS': 'eps_diluted',
            'trailingEps': 'eps_diluted',
            'forwardEps': 'forward_pe',
            'ebitda': 'ebitda',
            'EBITDA': 'ebitda',
            'ebit': 'ebit',
            'EBIT': 'ebit',

            # Balance Sheet
            'cashAndCashEquivalents': 'cash_and_cash_equivalents',
            'CashAndCashEquivalents': 'cash_and_cash_equivalents',
            'cash': 'cash_and_cash_equivalents',
            'shortTermInvestments': 'short_term_investments',
            'accountsReceivable': 'accounts_receivable',
            'AccountsReceivable': 'accounts_receivable',
            'inventory': 'inventory',
            'Inventory': 'inventory',
            'otherCurrentAssets': 'other_current_assets',
            'totalCurrentAssets': 'total_current_assets',
            'TotalCurrentAssets': 'total_current_assets',
            'propertyPlantEquipment': 'property_plant_equipment_net',
            'PropertyPlantEquipment': 'property_plant_equipment_net',
            'goodwill': 'goodwill',
            'Goodwill': 'goodwill',
            'intangibleAssets': 'intangible_assets',
            'IntangibleAssets': 'intangible_assets',
            'longTermInvestments': 'long_term_investments',
            'otherAssets': 'other_non_current_assets',
            'totalAssets': 'total_assets',
            'TotalAssets': 'total_assets',
            'accountsPayable': 'accounts_payable',
            'AccountsPayable': 'accounts_payable',
            'shortTermDebt': 'short_term_debt',
            'currentDebt': 'short_term_debt',
            'currentLongTermDebt': 'current_portion_long_term_debt',
            'deferredRevenue': 'deferred_revenue_current',
            'totalCurrentLiabilities': 'total_current_liabilities',
            'TotalCurrentLiabilities': 'total_current_liabilities',
            'longTermDebt': 'long_term_debt',
            'LongTermDebt': 'long_term_debt',
            'deferredTaxLiabilities': 'deferred_tax_liabilities',
            'otherLiabilities': 'other_non_current_liabilities',
            'totalLiabilities': 'total_liabilities',
            'TotalLiabilities': 'total_liabilities',
            'totalLiabilitiesNetMinorityInterest': 'total_liabilities',
            'commonStock': 'common_stock',
            'retainedEarnings': 'retained_earnings',
            'RetainedEarnings': 'retained_earnings',
            'totalStockholderEquity': 'total_stockholders_equity',
            'TotalStockholderEquity': 'total_stockholders_equity',
            'stockholdersEquity': 'total_stockholders_equity',

            # Cash Flow Statement
            'operatingCashFlow': 'operating_cash_flow',
            'totalCashFromOperatingActivities': 'operating_cash_flow',
            'depreciation': 'depreciation_and_amortization',
            'depreciationAndAmortization': 'depreciation_and_amortization',
            'stockBasedCompensation': 'stock_based_compensation',
            'changeInWorkingCapital': 'change_in_working_capital',
            'changeToAccountReceivables': 'change_in_accounts_receivable',
            'changeToInventory': 'change_in_inventory',
            'changeToAccountPayables': 'change_in_accounts_payable',
            'capitalExpenditures': 'capital_expenditures',
            'capitalExpenditure': 'capital_expenditures',
            'investments': 'purchases_of_investments',
            'investingCashFlow': 'investing_cash_flow',
            'totalCashflowsFromInvestingActivities': 'investing_cash_flow',
            'repaymentOfDebt': 'debt_repayment',
            'issuanceOfDebt': 'debt_issuance',
            'issuanceOfStock': 'common_stock_issued',
            'repurchaseOfStock': 'common_stock_repurchased',
            'dividendsPaid': 'dividends_paid',
            'financingCashFlow': 'financing_cash_flow',
            'totalCashFromFinancingActivities': 'financing_cash_flow',
            'freeCashFlow': 'free_cash_flow',
            'freeCashflow': 'free_cash_flow',

            # Market Data
            'currentPrice': 'stock_price',
            'regularMarketPrice': 'stock_price',
            'marketCap': 'market_cap',
            'enterpriseValue': 'enterprise_value',
            'sharesOutstanding': 'shares_outstanding',
            'beta': 'beta',
            'dividendYield': 'dividend_yield',
            'dividendRate': 'dividend_per_share',
            'trailingPE': 'pe_ratio',
            'forwardPE': 'forward_pe',
            'pegRatio': 'peg_ratio',
            'priceToSalesTrailing12Months': 'price_to_sales',
            'priceToBook': 'price_to_book',
            'enterpriseToRevenue': 'ev_to_revenue',
            'enterpriseToEbitda': 'ev_to_ebitda',

            # Company Info
            'sector': 'sector',
            'industry': 'industry',
            'country': 'country',
            'exchange': 'exchange',
            'fullTimeEmployees': 'employees',
            'longBusinessSummary': 'description',
            'website': 'website',
        }

    def _get_fmp_mappings(self) -> Dict[str, str]:
        """Get comprehensive FMP (Financial Modeling Prep) field name mappings"""
        return {
            # Required fields
            'symbol': 'ticker',
            'companyName': 'company_name',
            'currency': 'currency',
            'reportedCurrency': 'currency',

            # Income Statement
            'revenue': 'revenue',
            'costOfRevenue': 'cost_of_revenue',
            'grossProfit': 'gross_profit',
            'grossProfitRatio': 'gross_margin',
            'researchAndDevelopmentExpenses': 'research_and_development',
            'generalAndAdministrativeExpenses': 'selling_general_administrative',
            'sellingAndMarketingExpenses': 'selling_general_administrative',
            'sellingGeneralAndAdministrativeExpenses': 'selling_general_administrative',
            'otherExpenses': 'operating_expenses',
            'operatingExpenses': 'operating_expenses',
            'costAndExpenses': 'operating_expenses',
            'interestExpense': 'interest_expense',
            'interestIncome': 'interest_income',
            'depreciationAndAmortization': 'depreciation_and_amortization',
            'ebitda': 'ebitda',
            'ebitdaratio': 'operating_margin',
            'operatingIncome': 'operating_income',
            'operatingIncomeRatio': 'operating_margin',
            'totalOtherIncomeExpensesNet': 'other_income_expense',
            'incomeBeforeTax': 'income_before_tax',
            'incomeBeforeTaxRatio': 'net_margin',
            'incomeTaxExpense': 'income_tax_expense',
            'netIncome': 'net_income',
            'netIncomeRatio': 'net_margin',
            'eps': 'eps_basic',
            'epsdiluted': 'eps_diluted',
            'weightedAverageShsOut': 'weighted_average_shares_basic',
            'weightedAverageShsOutDil': 'weighted_average_shares_diluted',

            # Balance Sheet
            'cashAndCashEquivalents': 'cash_and_cash_equivalents',
            'shortTermInvestments': 'short_term_investments',
            'cashAndShortTermInvestments': 'cash_and_cash_equivalents',
            'netReceivables': 'accounts_receivable',
            'inventory': 'inventory',
            'otherCurrentAssets': 'other_current_assets',
            'totalCurrentAssets': 'total_current_assets',
            'propertyPlantEquipmentNet': 'property_plant_equipment_net',
            'goodwill': 'goodwill',
            'intangibleAssets': 'intangible_assets',
            'goodwillAndIntangibleAssets': 'intangible_assets',
            'longTermInvestments': 'long_term_investments',
            'taxAssets': 'other_non_current_assets',
            'otherNonCurrentAssets': 'other_non_current_assets',
            'totalNonCurrentAssets': 'total_non_current_assets',
            'otherAssets': 'other_non_current_assets',
            'totalAssets': 'total_assets',
            'accountPayables': 'accounts_payable',
            'shortTermDebt': 'short_term_debt',
            'taxPayables': 'accrued_liabilities',
            'deferredRevenue': 'deferred_revenue_current',
            'otherCurrentLiabilities': 'other_current_liabilities',
            'totalCurrentLiabilities': 'total_current_liabilities',
            'longTermDebt': 'long_term_debt',
            'deferredRevenueNonCurrent': 'deferred_revenue_non_current',
            'deferredTaxLiabilitiesNonCurrent': 'deferred_tax_liabilities',
            'otherNonCurrentLiabilities': 'other_non_current_liabilities',
            'totalNonCurrentLiabilities': 'total_non_current_liabilities',
            'otherLiabilities': 'other_non_current_liabilities',
            'capitalLeaseObligations': 'other_non_current_liabilities',
            'totalLiabilities': 'total_liabilities',
            'preferredStock': 'common_stock',
            'commonStock': 'common_stock',
            'retainedEarnings': 'retained_earnings',
            'accumulatedOtherComprehensiveIncomeLoss': 'accumulated_other_comprehensive_income',
            'othertotalStockholdersEquity': 'total_stockholders_equity',
            'totalStockholdersEquity': 'total_stockholders_equity',
            'totalEquity': 'total_stockholders_equity',
            'totalLiabilitiesAndStockholdersEquity': 'total_liabilities_and_equity',
            'minorityInterest': 'total_stockholders_equity',
            'totalLiabilitiesAndTotalEquity': 'total_liabilities_and_equity',
            'totalInvestments': 'long_term_investments',
            'totalDebt': 'long_term_debt',
            'netDebt': 'long_term_debt',

            # Cash Flow Statement
            'netCashFlowIncome': 'net_income_cash_flow',
            'depreciationAndAmortization': 'depreciation_and_amortization',
            'deferredIncomeTax': 'deferred_tax_liabilities',
            'stockBasedCompensation': 'stock_based_compensation',
            'changeInWorkingCapital': 'change_in_working_capital',
            'accountsReceivables': 'change_in_accounts_receivable',
            'changeInventory': 'change_in_inventory',
            'accountsPayables': 'change_in_accounts_payable',
            'otherWorkingCapital': 'change_in_working_capital',
            'otherNonCashItems': 'other_operating_activities',
            'netCashProvidedByOperatingActivities': 'operating_cash_flow',
            'investmentsInPropertyPlantAndEquipment': 'capital_expenditures',
            'acquisitionsNet': 'acquisitions',
            'purchasesOfInvestments': 'purchases_of_investments',
            'salesMaturitiesOfInvestments': 'sales_of_investments',
            'otherInvestingActivites': 'other_investing_activities',
            'netCashUsedForInvestingActivites': 'investing_cash_flow',
            'debtRepayment': 'debt_repayment',
            'commonStockIssued': 'common_stock_issued',
            'commonStockRepurchased': 'common_stock_repurchased',
            'dividendsPaid': 'dividends_paid',
            'otherFinancingActivites': 'other_financing_activities',
            'netCashUsedProvidedByFinancingActivities': 'financing_cash_flow',
            'effectOfForexChangesOnCash': 'net_change_in_cash',
            'netChangeInCash': 'net_change_in_cash',
            'cashAtEndOfPeriod': 'cash_and_cash_equivalents',
            'cashAtBeginningOfPeriod': 'cash_and_cash_equivalents',
            'operatingCashFlow': 'operating_cash_flow',
            'capitalExpenditure': 'capital_expenditures',
            'freeCashFlow': 'free_cash_flow',

            # Market Data & Ratios
            'marketCap': 'market_cap',
            'enterpriseValue': 'enterprise_value',
            'peRatio': 'pe_ratio',
            'priceToBookRatio': 'price_to_book',
            'priceToSalesRatio': 'price_to_sales',
            'pocfratio': 'price_to_cash_flow',
            'pfcfRatio': 'price_to_free_cash_flow',
            'pegRatio': 'peg_ratio',
            'evToSales': 'ev_to_sales',
            'enterpriseValueOverEBITDA': 'ev_to_ebitda',
            'evToOperatingCashFlow': 'ev_to_operating_cash_flow',
            'evToFreeCashFlow': 'ev_to_free_cash_flow',
            'earningsYield': 'earnings_yield',
            'freeCashFlowYield': 'free_cash_flow_yield',
            'debtToEquity': 'debt_to_equity',
            'debtToAssets': 'debt_to_assets',
            'netDebtToEBITDA': 'debt_to_equity',
            'currentRatio': 'current_ratio',
            'quickRatio': 'quick_ratio',
            'cashRatio': 'cash_ratio',
            'daysOfSalesOutstanding': 'days_sales_outstanding',
            'daysOfInventoryOutstanding': 'days_inventory_outstanding',
            'operatingCycle': 'cash_conversion_cycle',
            'daysOfPayablesOutstanding': 'days_payables_outstanding',
            'cashConversionCycle': 'cash_conversion_cycle',
            'grossProfitMargin': 'gross_margin',
            'operatingProfitMargin': 'operating_margin',
            'pretaxProfitMargin': 'net_margin',
            'netProfitMargin': 'net_margin',
            'effectiveTaxRate': 'tax_rate',
            'returnOnAssets': 'return_on_assets',
            'returnOnEquity': 'return_on_equity',
            'returnOnCapitalEmployed': 'return_on_invested_capital',
            'assetTurnover': 'asset_turnover',
            'inventoryTurnover': 'inventory_turnover',
            'receivablesTurnover': 'receivables_turnover',
            'payablesTurnover': 'payables_turnover',
            'dividendYield': 'dividend_yield',
            'dividendPerShare': 'dividend_per_share',
            'dividendPayout': 'dividend_payout_ratio',
            'payoutRatio': 'dividend_payout_ratio',
        }

    def _get_excel_mappings(self) -> Dict[str, str]:
        """Get comprehensive Excel field name mappings (common variations)"""
        return {
            # Required fields
            'Ticker': 'ticker',
            'Symbol': 'ticker',
            'Stock Symbol': 'ticker',
            'Company': 'company_name',
            'Company Name': 'company_name',
            'Name': 'company_name',
            'Currency': 'currency',
            'Fiscal Year End': 'fiscal_year_end',
            'FYE': 'fiscal_year_end',

            # Income Statement
            'Revenue': 'revenue',
            'Total Revenue': 'revenue',
            'Sales': 'revenue',
            'Total Sales': 'revenue',
            'Net Sales': 'revenue',
            'Cost of Revenue': 'cost_of_revenue',
            'COGS': 'cost_of_revenue',
            'Cost of Goods Sold': 'cost_of_revenue',
            'Cost of Sales': 'cost_of_revenue',
            'Gross Profit': 'gross_profit',
            'Gross Income': 'gross_profit',
            'Operating Expenses': 'operating_expenses',
            'OPEX': 'operating_expenses',
            'R&D': 'research_and_development',
            'Research and Development': 'research_and_development',
            'SG&A': 'selling_general_administrative',
            'Selling General and Administrative': 'selling_general_administrative',
            'Operating Income': 'operating_income',
            'Operating Profit': 'operating_income',
            'EBIT': 'ebit',
            'Earnings Before Interest and Taxes': 'ebit',
            'EBITDA': 'ebitda',
            'Interest Expense': 'interest_expense',
            'Interest Income': 'interest_income',
            'Other Income': 'other_income_expense',
            'Other Expense': 'other_income_expense',
            'Pretax Income': 'income_before_tax',
            'Income Before Tax': 'income_before_tax',
            'EBT': 'income_before_tax',
            'Tax Expense': 'income_tax_expense',
            'Income Tax': 'income_tax_expense',
            'Taxes': 'income_tax_expense',
            'Net Income': 'net_income',
            'Net Profit': 'net_income',
            'Net Earnings': 'net_income',
            'Profit': 'net_income',
            'EPS': 'eps_basic',
            'Earnings Per Share': 'eps_basic',
            'Basic EPS': 'eps_basic',
            'Diluted EPS': 'eps_diluted',

            # Balance Sheet
            'Cash': 'cash_and_cash_equivalents',
            'Cash and Equivalents': 'cash_and_cash_equivalents',
            'Cash and Cash Equivalents': 'cash_and_cash_equivalents',
            'Short Term Investments': 'short_term_investments',
            'Marketable Securities': 'short_term_investments',
            'Accounts Receivable': 'accounts_receivable',
            'A/R': 'accounts_receivable',
            'Receivables': 'accounts_receivable',
            'Inventory': 'inventory',
            'Inventories': 'inventory',
            'Current Assets': 'total_current_assets',
            'Total Current Assets': 'total_current_assets',
            'PP&E': 'property_plant_equipment_net',
            'Property Plant and Equipment': 'property_plant_equipment_net',
            'Fixed Assets': 'property_plant_equipment_net',
            'Goodwill': 'goodwill',
            'Intangible Assets': 'intangible_assets',
            'Intangibles': 'intangible_assets',
            'Long Term Investments': 'long_term_investments',
            'Non-Current Assets': 'total_non_current_assets',
            'Total Non-Current Assets': 'total_non_current_assets',
            'Total Assets': 'total_assets',
            'Assets': 'total_assets',
            'Accounts Payable': 'accounts_payable',
            'A/P': 'accounts_payable',
            'Payables': 'accounts_payable',
            'Short Term Debt': 'short_term_debt',
            'Current Debt': 'short_term_debt',
            'Current Liabilities': 'total_current_liabilities',
            'Total Current Liabilities': 'total_current_liabilities',
            'Long Term Debt': 'long_term_debt',
            'LT Debt': 'long_term_debt',
            'Non-Current Liabilities': 'total_non_current_liabilities',
            'Total Non-Current Liabilities': 'total_non_current_liabilities',
            'Total Liabilities': 'total_liabilities',
            'Liabilities': 'total_liabilities',
            'Common Stock': 'common_stock',
            'Retained Earnings': 'retained_earnings',
            'Shareholders Equity': 'total_stockholders_equity',
            'Stockholders Equity': 'total_stockholders_equity',
            'Total Equity': 'total_stockholders_equity',
            'Equity': 'total_stockholders_equity',

            # Cash Flow Statement
            'Operating Cash Flow': 'operating_cash_flow',
            'Cash from Operations': 'operating_cash_flow',
            'OCF': 'operating_cash_flow',
            'Depreciation': 'depreciation_and_amortization',
            'D&A': 'depreciation_and_amortization',
            'Depreciation and Amortization': 'depreciation_and_amortization',
            'Stock Based Compensation': 'stock_based_compensation',
            'SBC': 'stock_based_compensation',
            'Change in Working Capital': 'change_in_working_capital',
            'Working Capital Change': 'change_in_working_capital',
            'Capital Expenditures': 'capital_expenditures',
            'Capex': 'capital_expenditures',
            'CAPEX': 'capital_expenditures',
            'CapEx': 'capital_expenditures',
            'Investing Cash Flow': 'investing_cash_flow',
            'Cash from Investing': 'investing_cash_flow',
            'Financing Cash Flow': 'financing_cash_flow',
            'Cash from Financing': 'financing_cash_flow',
            'Dividends Paid': 'dividends_paid',
            'Dividends': 'dividends_paid',
            'Free Cash Flow': 'free_cash_flow',
            'FCF': 'free_cash_flow',

            # Market Data & Ratios
            'Stock Price': 'stock_price',
            'Price': 'stock_price',
            'Share Price': 'stock_price',
            'Market Cap': 'market_cap',
            'Market Capitalization': 'market_cap',
            'Enterprise Value': 'enterprise_value',
            'EV': 'enterprise_value',
            'Shares Outstanding': 'shares_outstanding',
            'Shares': 'shares_outstanding',
            'P/E': 'pe_ratio',
            'PE Ratio': 'pe_ratio',
            'Price to Earnings': 'pe_ratio',
            'P/B': 'price_to_book',
            'Price to Book': 'price_to_book',
            'PB Ratio': 'price_to_book',
            'P/S': 'price_to_sales',
            'Price to Sales': 'price_to_sales',
            'Dividend Yield': 'dividend_yield',
            'Div Yield': 'dividend_yield',
            'Beta': 'beta',
            'ROE': 'return_on_equity',
            'Return on Equity': 'return_on_equity',
            'ROA': 'return_on_assets',
            'Return on Assets': 'return_on_assets',
            'ROIC': 'return_on_invested_capital',
            'Return on Invested Capital': 'return_on_invested_capital',
            'Gross Margin': 'gross_margin',
            'Operating Margin': 'operating_margin',
            'Net Margin': 'net_margin',
            'Profit Margin': 'net_margin',
            'Current Ratio': 'current_ratio',
            'Quick Ratio': 'quick_ratio',
            'Debt to Equity': 'debt_to_equity',
            'D/E': 'debt_to_equity',
            'Debt/Equity': 'debt_to_equity',

            # Company Info
            'Sector': 'sector',
            'Industry': 'industry',
            'Country': 'country',
            'Exchange': 'exchange',
            'Employees': 'employees',
        }

    def _get_alpha_vantage_mappings(self) -> Dict[str, str]:
        """Get Alpha Vantage field name mappings"""
        return {
            'symbol': 'ticker',
            'name': 'company_name',
            'currency': 'currency',
            'totalRevenue': 'revenue',
            'costOfRevenue': 'cost_of_revenue',
            'grossProfit': 'gross_profit',
            'operatingExpenses': 'operating_expenses',
            'operatingIncome': 'operating_income',
            'netIncome': 'net_income',
            'ebitda': 'ebitda',
            'totalAssets': 'total_assets',
            'totalLiabilities': 'total_liabilities',
            'totalEquity': 'total_stockholders_equity',
            'cashAndCashEquivalents': 'cash_and_cash_equivalents',
            'operatingCashflow': 'operating_cash_flow',
            'capitalExpenditures': 'capital_expenditures',
        }

    def _get_polygon_mappings(self) -> Dict[str, str]:
        """Get Polygon.io field name mappings"""
        return {
            'ticker': 'ticker',
            'name': 'company_name',
            'market_cap': 'market_cap',
            'revenues': 'revenue',
            'net_income': 'net_income',
            'total_assets': 'total_assets',
            'total_liabilities': 'total_liabilities',
            'equity': 'total_stockholders_equity',
        }

    def _build_reverse_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build reverse mappings (standard -> source)"""
        reverse = {}
        for source, mappings in self._source_to_standard.items():
            reverse[source] = {std: src for src, std in mappings.items()}
        return reverse

    def get_standard_field_name(
        self,
        source: str,
        field_name: str,
        case_sensitive: bool = True,
        fuzzy_match: bool = False,
        fuzzy_threshold: float = 0.8
    ) -> Optional[str]:
        """
        Get standard field name from source-specific field name.

        Args:
            source: Data source ('yfinance', 'fmp', 'excel', etc.)
            field_name: Source-specific field name
            case_sensitive: Whether to use case-sensitive matching
            fuzzy_match: Whether to use fuzzy matching (useful for Excel)
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0)

        Returns:
            Standard field name if found, None otherwise
        """
        with self._access_lock:
            source = source.lower()

            if source not in self._source_to_standard:
                logger.warning(f"Unknown data source: {source}")
                return None

            mappings = self._source_to_standard[source]

            # Exact match (case-sensitive)
            if case_sensitive and field_name in mappings:
                return mappings[field_name]

            # Case-insensitive match
            if not case_sensitive:
                for src_field, std_field in mappings.items():
                    if src_field.lower() == field_name.lower():
                        return std_field

            # Fuzzy match (for Excel and user input)
            if fuzzy_match:
                return self._fuzzy_match_field(field_name, mappings, fuzzy_threshold)

            return None

    def get_source_field_name(
        self,
        source: str,
        standard_field_name: str
    ) -> Optional[str]:
        """
        Get source-specific field name from standard field name (reverse lookup).

        Args:
            source: Data source ('yfinance', 'fmp', 'excel', etc.)
            standard_field_name: Standard field name

        Returns:
            Source-specific field name if found, None otherwise
        """
        with self._access_lock:
            source = source.lower()

            if source not in self._standard_to_source:
                logger.warning(f"Unknown data source: {source}")
                return None

            return self._standard_to_source[source].get(standard_field_name)

    def _fuzzy_match_field(
        self,
        field_name: str,
        mappings: Dict[str, str],
        threshold: float = 0.8
    ) -> Optional[str]:
        """
        Fuzzy match field name against available mappings.

        Args:
            field_name: Field name to match
            mappings: Available mappings to match against
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Standard field name of best match, or None if no good match
        """
        best_match = None
        best_score = 0.0

        field_lower = field_name.lower().strip()

        for source_field, standard_field in mappings.items():
            source_lower = source_field.lower().strip()

            # Calculate similarity ratio
            ratio = SequenceMatcher(None, field_lower, source_lower).ratio()

            if ratio > best_score:
                best_score = ratio
                best_match = standard_field

        if best_score >= threshold:
            logger.debug(f"Fuzzy matched '{field_name}' to standard field (score: {best_score:.2f})")
            return best_match

        return None

    def get_all_source_fields(self, source: str) -> List[str]:
        """
        Get all source-specific field names for a data source.

        Args:
            source: Data source name

        Returns:
            List of source-specific field names
        """
        with self._access_lock:
            source = source.lower()
            if source not in self._source_to_standard:
                return []
            return list(self._source_to_standard[source].keys())

    def get_all_standard_fields(self, source: str) -> List[str]:
        """
        Get all standard field names available for a data source.

        Args:
            source: Data source name

        Returns:
            List of standard field names
        """
        with self._access_lock:
            source = source.lower()
            if source not in self._source_to_standard:
                return []
            return list(set(self._source_to_standard[source].values()))

    def validate_mappings(self) -> Tuple[bool, List[str]]:
        """
        Validate all mappings for conflicts and issues.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        with self._access_lock:
            # Check for duplicate source field mappings within each source
            for source, mappings in self._source_to_standard.items():
                # Check for conflicts (same source field mapping to different standard fields)
                seen = {}
                for src_field, std_field in mappings.items():
                    src_lower = src_field.lower()
                    if src_lower in seen and seen[src_lower] != std_field:
                        issues.append(
                            f"{source}: '{src_field}' maps to both '{seen[src_lower]}' "
                            f"and '{std_field}'"
                        )
                    seen[src_lower] = std_field

            # Validate reverse mappings match forward mappings
            for source in self._source_to_standard.keys():
                forward_std_fields = set(self._source_to_standard[source].values())
                reverse_std_fields = set(self._standard_to_source[source].keys())

                if forward_std_fields != reverse_std_fields:
                    issues.append(
                        f"{source}: Mismatch between forward and reverse mappings"
                    )

        return len(issues) == 0, issues

    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the field mappings"""
        with self._access_lock:
            stats = {}
            for source, mappings in self._source_to_standard.items():
                unique_standards = len(set(mappings.values()))
                stats[source] = {
                    'total_mappings': len(mappings),
                    'unique_standard_fields': unique_standards,
                    'coverage_ratio': f"{unique_standards}/{len(mappings)}"
                }
            return stats


# Singleton accessor function
def get_field_mapping_registry() -> FieldMappingRegistry:
    """Get the singleton FieldMappingRegistry instance"""
    return FieldMappingRegistry()
