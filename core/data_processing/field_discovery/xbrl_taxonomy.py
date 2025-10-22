"""
XBRL Taxonomy Mapper
====================

Maps financial fields to XBRL (eXtensible Business Reporting Language) taxonomy
for standardization against SEC reporting requirements and international standards.

XBRL is the global standard for exchanging business financial information.
This module provides mappings to US GAAP and IFRS taxonomies.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TaxonomyStandard(Enum):
    """Financial reporting taxonomy standards"""
    US_GAAP = "us-gaap"
    IFRS = "ifrs"
    SEC = "sec"


@dataclass
class XBRLConcept:
    """Represents an XBRL taxonomy concept"""
    concept_name: str
    taxonomy: TaxonomyStandard
    label: str
    definition: str
    data_type: str
    period_type: str  # instant or duration
    statement_category: str
    is_monetary: bool
    is_abstract: bool = False


class XBRLTaxonomyMapper:
    """
    Maps financial fields to XBRL taxonomy concepts.

    Provides standardization against SEC filing requirements and
    international financial reporting standards (IFRS).
    """

    def __init__(self, default_taxonomy: TaxonomyStandard = TaxonomyStandard.US_GAAP):
        """
        Initialize the XBRL taxonomy mapper.

        Args:
            default_taxonomy: Default taxonomy standard to use
        """
        self.default_taxonomy = default_taxonomy

        # Initialize taxonomy mappings
        self._initialize_us_gaap_taxonomy()
        self._initialize_ifrs_taxonomy()

        logger.info(f"XBRLTaxonomyMapper initialized with {self.default_taxonomy.value} taxonomy")

    def _initialize_us_gaap_taxonomy(self):
        """Initialize US GAAP taxonomy mappings"""
        self.us_gaap_concepts = {
            # Income Statement
            'revenue': XBRLConcept(
                concept_name='Revenues',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Revenue',
                definition='Total revenue from goods sold and services rendered during the reporting period',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),
            'cost_of_revenue': XBRLConcept(
                concept_name='CostOfRevenue',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Cost of Revenue',
                definition='The aggregate cost of goods produced and sold and services rendered',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),
            'gross_profit': XBRLConcept(
                concept_name='GrossProfit',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Gross Profit',
                definition='Revenue less cost of revenue',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),
            'operating_income': XBRLConcept(
                concept_name='OperatingIncomeLoss',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Operating Income (Loss)',
                definition='Operating income before income from equity method investments',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),
            'net_income': XBRLConcept(
                concept_name='NetIncomeLoss',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Net Income (Loss)',
                definition='The portion of profit or loss attributable to the parent',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),

            # Balance Sheet - Assets
            'cash_and_cash_equivalents': XBRLConcept(
                concept_name='CashAndCashEquivalentsAtCarryingValue',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Cash and Cash Equivalents',
                definition='Cash and highly liquid investments with maturity of 3 months or less',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'accounts_receivable': XBRLConcept(
                concept_name='AccountsReceivableNetCurrent',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Accounts Receivable, Net',
                definition='Trade accounts and notes receivable, net of allowances',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'inventory': XBRLConcept(
                concept_name='InventoryNet',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Inventory, Net',
                definition='Carrying amount of inventories',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'total_current_assets': XBRLConcept(
                concept_name='AssetsCurrent',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Assets, Current',
                definition='Sum of carrying amounts of current assets',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'property_plant_equipment_net': XBRLConcept(
                concept_name='PropertyPlantAndEquipmentNet',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Property, Plant and Equipment, Net',
                definition='Tangible assets used in normal conduct of business',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'goodwill': XBRLConcept(
                concept_name='Goodwill',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Goodwill',
                definition='Amount after accumulated impairment loss of an asset representing future economic benefits',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'total_assets': XBRLConcept(
                concept_name='Assets',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Assets',
                definition='Sum of carrying amounts of all assets',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),

            # Balance Sheet - Liabilities & Equity
            'accounts_payable': XBRLConcept(
                concept_name='AccountsPayableCurrent',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Accounts Payable, Current',
                definition='Carrying value of liabilities for purchase of goods and services',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'short_term_debt': XBRLConcept(
                concept_name='ShortTermBorrowings',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Short-term Debt',
                definition='Carrying amount of short-term borrowings',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'total_current_liabilities': XBRLConcept(
                concept_name='LiabilitiesCurrent',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Liabilities, Current',
                definition='Total current liabilities',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'long_term_debt': XBRLConcept(
                concept_name='LongTermDebtNoncurrent',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Long-term Debt, Noncurrent',
                definition='Carrying amount of long-term debt excluding current portion',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'total_liabilities': XBRLConcept(
                concept_name='Liabilities',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Liabilities',
                definition='Sum of carrying amounts of all liabilities',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),
            'total_stockholders_equity': XBRLConcept(
                concept_name='StockholdersEquity',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Stockholders\' Equity',
                definition='Total of all stockholders\' equity components',
                data_type='monetary',
                period_type='instant',
                statement_category='balance_sheet',
                is_monetary=True
            ),

            # Cash Flow Statement
            'operating_cash_flow': XBRLConcept(
                concept_name='NetCashProvidedByUsedInOperatingActivities',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Net Cash Provided by (Used in) Operating Activities',
                definition='Cash inflow (outflow) from operating activities',
                data_type='monetary',
                period_type='duration',
                statement_category='cash_flow',
                is_monetary=True
            ),
            'capital_expenditures': XBRLConcept(
                concept_name='PaymentsToAcquirePropertyPlantAndEquipment',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Payments to Acquire Property, Plant, and Equipment',
                definition='Cash outflow for capital expenditures',
                data_type='monetary',
                period_type='duration',
                statement_category='cash_flow',
                is_monetary=True
            ),
            'investing_cash_flow': XBRLConcept(
                concept_name='NetCashProvidedByUsedInInvestingActivities',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Net Cash Provided by (Used in) Investing Activities',
                definition='Cash inflow (outflow) from investing activities',
                data_type='monetary',
                period_type='duration',
                statement_category='cash_flow',
                is_monetary=True
            ),
            'financing_cash_flow': XBRLConcept(
                concept_name='NetCashProvidedByUsedInFinancingActivities',
                taxonomy=TaxonomyStandard.US_GAAP,
                label='Net Cash Provided by (Used in) Financing Activities',
                definition='Cash inflow (outflow) from financing activities',
                data_type='monetary',
                period_type='duration',
                statement_category='cash_flow',
                is_monetary=True
            ),
        }

    def _initialize_ifrs_taxonomy(self):
        """Initialize IFRS taxonomy mappings"""
        # IFRS uses similar concepts but with different naming conventions
        self.ifrs_concepts = {
            'revenue': XBRLConcept(
                concept_name='Revenue',
                taxonomy=TaxonomyStandard.IFRS,
                label='Revenue',
                definition='Income arising in course of ordinary activities',
                data_type='monetary',
                period_type='duration',
                statement_category='income_statement',
                is_monetary=True
            ),
            # Add more IFRS concepts as needed
        }

    def get_xbrl_concept(
        self,
        standard_field_name: str,
        taxonomy: Optional[TaxonomyStandard] = None
    ) -> Optional[XBRLConcept]:
        """
        Get XBRL concept for a standard field name.

        Args:
            standard_field_name: Standard field name
            taxonomy: Optional taxonomy standard (defaults to instance default)

        Returns:
            XBRLConcept if found, None otherwise
        """
        taxonomy = taxonomy or self.default_taxonomy

        if taxonomy == TaxonomyStandard.US_GAAP:
            return self.us_gaap_concepts.get(standard_field_name)
        elif taxonomy == TaxonomyStandard.IFRS:
            return self.ifrs_concepts.get(standard_field_name)

        return None

    def validate_against_taxonomy(
        self,
        field_name: str,
        taxonomy: Optional[TaxonomyStandard] = None
    ) -> bool:
        """
        Check if a field name exists in the taxonomy.

        Args:
            field_name: Field name to validate
            taxonomy: Optional taxonomy standard

        Returns:
            True if field exists in taxonomy
        """
        concept = self.get_xbrl_concept(field_name, taxonomy)
        return concept is not None

    def get_all_concepts(
        self,
        taxonomy: Optional[TaxonomyStandard] = None
    ) -> Dict[str, XBRLConcept]:
        """
        Get all concepts for a taxonomy.

        Args:
            taxonomy: Optional taxonomy standard

        Returns:
            Dictionary of field names to XBRLConcept objects
        """
        taxonomy = taxonomy or self.default_taxonomy

        if taxonomy == TaxonomyStandard.US_GAAP:
            return self.us_gaap_concepts.copy()
        elif taxonomy == TaxonomyStandard.IFRS:
            return self.ifrs_concepts.copy()

        return {}

    def suggest_xbrl_mapping(
        self,
        field_name: str,
        taxonomy: Optional[TaxonomyStandard] = None
    ) -> List[XBRLConcept]:
        """
        Suggest XBRL concepts that might match a field name.

        Args:
            field_name: Field name to match
            taxonomy: Optional taxonomy standard

        Returns:
            List of potential XBRLConcept matches
        """
        taxonomy = taxonomy or self.default_taxonomy
        concepts = self.get_all_concepts(taxonomy)

        suggestions = []
        normalized_field = field_name.lower().replace('_', ' ')

        for concept_field, concept in concepts.items():
            # Check if field name contains concept keywords
            concept_keywords = concept_field.lower().replace('_', ' ')
            if any(word in normalized_field for word in concept_keywords.split()):
                suggestions.append(concept)

        return suggestions
