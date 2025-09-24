"""
ESG Variable Definitions
========================

ESG (Environmental, Social, Governance) specific variable definitions for integration
with the financial analysis platform. This module extends the FinancialVariableRegistry
with ESG-specific metrics and data structures.

Key ESG Categories:
- Environmental: Carbon emissions, energy efficiency, waste management, water usage
- Social: Employee satisfaction, diversity, community impact, safety metrics
- Governance: Board composition, executive compensation, compliance, transparency

ESG Score Providers:
- MSCI ESG Research
- Sustainalytics
- ESG Enterprise
- Bloomberg ESG
- Yahoo Finance (limited ESG data)
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from core.data_processing.financial_variable_registry import (
    VariableCategory, DataType, Units, ValidationRule, VariableDefinition
)


class ESGCategory(Enum):
    """ESG-specific variable categories"""
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    ESG_SCORES = "esg_scores"
    ESG_RATINGS = "esg_ratings"
    SUSTAINABILITY = "sustainability"


class ESGDataType(Enum):
    """ESG-specific data types"""
    ESG_SCORE = "esg_score"          # 0-100 scale typically
    ESG_RATING = "esg_rating"        # Letter grades (AAA, AA, A, etc.)
    CARBON_INTENSITY = "carbon_intensity"  # CO2e per unit
    EMPLOYEE_COUNT = "employee_count"
    BOARD_COMPOSITION = "board_composition"  # Percentages
    COMPLIANCE_STATUS = "compliance_status"  # Boolean/categorical


class ESGUnits(Enum):
    """ESG-specific units"""
    # Environmental units
    TONNES_CO2E = "tonnes_co2e"
    TONNES_CO2E_PER_MILLION_REVENUE = "tonnes_co2e_per_million_revenue"
    MWH = "megawatt_hours"
    CUBIC_METERS = "cubic_meters"

    # Social units
    EMPLOYEE_COUNT = "employee_count"
    ACCIDENT_RATE = "accidents_per_100_employees"

    # Governance units
    BOARD_PERCENTAGE = "board_percentage"

    # Scoring units
    ESG_SCORE_100 = "esg_score_100"    # 0-100 scale
    ESG_SCORE_10 = "esg_score_10"      # 0-10 scale
    ESG_RATING_LETTER = "esg_rating_letter"  # AAA, AA, A, BBB, etc.


@dataclass
class ESGVariableDefinition(VariableDefinition):
    """Extended variable definition for ESG metrics"""
    esg_category: ESGCategory = ESGCategory.ESG_SCORES  # Default category
    esg_pillar: str = "ESG"  # "E", "S", "G", or "ESG"
    data_provider: Optional[str] = None  # MSCI, Sustainalytics, etc.
    methodology: Optional[str] = None    # Scoring methodology description
    update_frequency: Optional[str] = None  # Daily, Monthly, Quarterly, Annually


def get_esg_variable_definitions() -> Dict[str, ESGVariableDefinition]:
    """
    Get comprehensive ESG variable definitions for integration with the registry

    Returns:
        Dictionary of ESG variable definitions keyed by variable name
    """
    esg_variables = {}

    # Environmental Variables
    environmental_vars = [
        ESGVariableDefinition(
            name="carbon_emissions_total",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,  # Will use ESGUnits.TONNES_CO2E when integrated
            description="Total carbon emissions (Scope 1 + 2 + 3)",
            aliases={
                "msci": "carbon_emissions_total",
                "sustainalytics": "total_carbon_emissions",
                "esg_enterprise": "carbon_footprint_total",
                "bloomberg": "ENVIRONMENTAL_CARBON_TOTAL"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Carbon emissions cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="carbon_intensity",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Carbon emissions per unit of revenue (tonnes CO2e/$M revenue)",
            aliases={
                "msci": "carbon_intensity_revenue",
                "sustainalytics": "carbon_intensity_sales",
                "esg_enterprise": "carbon_intensity_ratio",
                "bloomberg": "ENVIRONMENTAL_CARBON_INTENSITY"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Carbon intensity cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="energy_consumption",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Total energy consumption in MWh",
            aliases={
                "msci": "energy_consumption_total",
                "sustainalytics": "total_energy_consumption",
                "esg_enterprise": "energy_usage_total",
                "bloomberg": "ENVIRONMENTAL_ENERGY_TOTAL"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Energy consumption cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="renewable_energy_percentage",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of energy consumption from renewable sources",
            aliases={
                "msci": "renewable_energy_pct",
                "sustainalytics": "renewable_energy_ratio",
                "esg_enterprise": "renewable_percentage",
                "bloomberg": "ENVIRONMENTAL_RENEWABLE_PCT"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Renewable energy percentage must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="water_consumption",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Total water consumption in cubic meters",
            aliases={
                "msci": "water_consumption_total",
                "sustainalytics": "total_water_usage",
                "esg_enterprise": "water_consumption",
                "bloomberg": "ENVIRONMENTAL_WATER_TOTAL"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Water consumption cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="waste_generated",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Total waste generated in tonnes",
            aliases={
                "msci": "waste_generated_total",
                "sustainalytics": "total_waste_generated",
                "esg_enterprise": "waste_production",
                "bloomberg": "ENVIRONMENTAL_WASTE_TOTAL"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Waste generated cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="waste_recycling_rate",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ENVIRONMENTAL,
            esg_pillar="E",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of waste that is recycled or reused",
            aliases={
                "msci": "waste_recycling_pct",
                "sustainalytics": "recycling_rate",
                "esg_enterprise": "waste_recycling_percentage",
                "bloomberg": "ENVIRONMENTAL_RECYCLING_PCT"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Waste recycling rate must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        )
    ]

    # Social Variables
    social_vars = [
        ESGVariableDefinition(
            name="employee_count_total",
            category=VariableCategory.METADATA,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.INTEGER,
            units=Units.NONE,
            description="Total number of employees",
            aliases={
                "msci": "total_employees",
                "sustainalytics": "employee_count",
                "esg_enterprise": "total_workforce",
                "bloomberg": "SOCIAL_EMPLOYEE_COUNT",
                "yfinance": "fullTimeEmployees"
            },
            validation_rules=[
                ValidationRule("positive", error_message="Employee count must be positive")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="employee_turnover_rate",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Annual employee turnover rate",
            aliases={
                "msci": "employee_turnover_pct",
                "sustainalytics": "turnover_rate",
                "esg_enterprise": "employee_turnover_percentage",
                "bloomberg": "SOCIAL_TURNOVER_RATE"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Turnover rate cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="gender_diversity_board",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of women on board of directors",
            aliases={
                "msci": "board_gender_diversity_pct",
                "sustainalytics": "women_board_percentage",
                "esg_enterprise": "board_female_percentage",
                "bloomberg": "SOCIAL_BOARD_GENDER_DIVERSITY"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Gender diversity percentage must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="gender_diversity_workforce",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of women in total workforce",
            aliases={
                "msci": "workforce_gender_diversity_pct",
                "sustainalytics": "women_workforce_percentage",
                "esg_enterprise": "workforce_female_percentage",
                "bloomberg": "SOCIAL_WORKFORCE_GENDER_DIVERSITY"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Workforce gender diversity must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="workplace_safety_incidents",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Workplace safety incidents per 100 employees",
            aliases={
                "msci": "safety_incident_rate",
                "sustainalytics": "workplace_accidents_rate",
                "esg_enterprise": "safety_incidents_per_employee",
                "bloomberg": "SOCIAL_SAFETY_INCIDENTS"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Safety incidents cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="training_hours_per_employee",
            category=VariableCategory.DERIVED,
            esg_category=ESGCategory.SOCIAL,
            esg_pillar="S",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Average training hours per employee per year",
            aliases={
                "msci": "training_hours_avg",
                "sustainalytics": "employee_training_hours",
                "esg_enterprise": "training_per_employee",
                "bloomberg": "SOCIAL_TRAINING_HOURS"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Training hours cannot be negative")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        )
    ]

    # Governance Variables
    governance_vars = [
        ESGVariableDefinition(
            name="board_independence",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.GOVERNANCE,
            esg_pillar="G",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of independent board directors",
            aliases={
                "msci": "board_independence_pct",
                "sustainalytics": "independent_directors_percentage",
                "esg_enterprise": "board_independence_ratio",
                "bloomberg": "GOVERNANCE_BOARD_INDEPENDENCE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Board independence must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="board_size",
            category=VariableCategory.METADATA,
            esg_category=ESGCategory.GOVERNANCE,
            esg_pillar="G",
            data_type=DataType.INTEGER,
            units=Units.NONE,
            description="Total number of board directors",
            aliases={
                "msci": "board_size_total",
                "sustainalytics": "total_board_members",
                "esg_enterprise": "board_directors_count",
                "bloomberg": "GOVERNANCE_BOARD_SIZE"
            },
            validation_rules=[
                ValidationRule("positive", error_message="Board size must be positive"),
                ValidationRule("range", {"min": 3, "max": 30},
                             error_message="Board size typically ranges from 3 to 30 directors")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="audit_committee_independence",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.GOVERNANCE,
            esg_pillar="G",
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            description="Percentage of audit committee members who are independent",
            aliases={
                "msci": "audit_committee_independence_pct",
                "sustainalytics": "audit_independence_percentage",
                "esg_enterprise": "audit_committee_independence",
                "bloomberg": "GOVERNANCE_AUDIT_INDEPENDENCE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 1.0},
                             error_message="Audit committee independence must be between 0% and 100%")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="executive_compensation_ratio",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.GOVERNANCE,
            esg_pillar="G",
            data_type=DataType.FLOAT,
            units=Units.MULTIPLE,
            description="Ratio of CEO compensation to median employee compensation",
            aliases={
                "msci": "ceo_pay_ratio",
                "sustainalytics": "executive_pay_ratio",
                "esg_enterprise": "compensation_ratio",
                "bloomberg": "GOVERNANCE_CEO_PAY_RATIO"
            },
            validation_rules=[
                ValidationRule("positive", error_message="Compensation ratio must be positive")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        ),

        ESGVariableDefinition(
            name="shareholder_rights_score",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.GOVERNANCE,
            esg_pillar="G",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Score reflecting strength of shareholder rights (0-100)",
            aliases={
                "msci": "shareholder_rights_score",
                "sustainalytics": "shareholder_protection_score",
                "esg_enterprise": "shareholder_rights_rating",
                "bloomberg": "GOVERNANCE_SHAREHOLDER_RIGHTS"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 100.0},
                             error_message="Shareholder rights score must be between 0 and 100")
            ],
            data_provider="Multiple",
            update_frequency="Annually"
        )
    ]

    # ESG Composite Scores
    esg_score_vars = [
        ESGVariableDefinition(
            name="esg_score_total",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ESG_SCORES,
            esg_pillar="ESG",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Overall ESG score (0-100 scale)",
            aliases={
                "msci": "esg_score",
                "sustainalytics": "esg_risk_score",
                "esg_enterprise": "esg_rating_score",
                "bloomberg": "ESG_DISCLOSURE_SCORE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 100.0},
                             error_message="ESG score must be between 0 and 100")
            ],
            data_provider="Multiple",
            update_frequency="Quarterly"
        ),

        ESGVariableDefinition(
            name="environmental_score",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ESG_SCORES,
            esg_pillar="E",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Environmental pillar score (0-100 scale)",
            aliases={
                "msci": "environmental_score",
                "sustainalytics": "environmental_risk_score",
                "esg_enterprise": "environmental_rating",
                "bloomberg": "ENVIRONMENTAL_DISCLOSURE_SCORE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 100.0},
                             error_message="Environmental score must be between 0 and 100")
            ],
            data_provider="Multiple",
            update_frequency="Quarterly"
        ),

        ESGVariableDefinition(
            name="social_score",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ESG_SCORES,
            esg_pillar="S",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Social pillar score (0-100 scale)",
            aliases={
                "msci": "social_score",
                "sustainalytics": "social_risk_score",
                "esg_enterprise": "social_rating",
                "bloomberg": "SOCIAL_DISCLOSURE_SCORE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 100.0},
                             error_message="Social score must be between 0 and 100")
            ],
            data_provider="Multiple",
            update_frequency="Quarterly"
        ),

        ESGVariableDefinition(
            name="governance_score",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ESG_SCORES,
            esg_pillar="G",
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Governance pillar score (0-100 scale)",
            aliases={
                "msci": "governance_score",
                "sustainalytics": "governance_risk_score",
                "esg_enterprise": "governance_rating",
                "bloomberg": "GOVERNANCE_DISCLOSURE_SCORE"
            },
            validation_rules=[
                ValidationRule("range", {"min": 0.0, "max": 100.0},
                             error_message="Governance score must be between 0 and 100")
            ],
            data_provider="Multiple",
            update_frequency="Quarterly"
        ),

        ESGVariableDefinition(
            name="esg_rating_letter",
            category=VariableCategory.RATIOS,
            esg_category=ESGCategory.ESG_RATINGS,
            esg_pillar="ESG",
            data_type=DataType.STRING,
            units=Units.TEXT,
            description="Overall ESG letter rating (AAA, AA, A, BBB, BB, B, CCC)",
            aliases={
                "msci": "esg_rating",
                "sustainalytics": "esg_risk_rating",
                "esg_enterprise": "esg_grade",
                "bloomberg": "ESG_RATING_COMPOSITE"
            },
            validation_rules=[
                ValidationRule("regex",
                             {"pattern": "^(AAA|AA|A|BBB|BB|B|CCC)$"},
                             error_message="ESG rating must be one of: AAA, AA, A, BBB, BB, B, CCC")
            ],
            data_provider="Multiple",
            update_frequency="Quarterly"
        )
    ]

    # Combine all variables
    all_vars = environmental_vars + social_vars + governance_vars + esg_score_vars

    # Convert to dictionary
    for var in all_vars:
        esg_variables[var.name] = var

    return esg_variables


def register_esg_variables_with_registry():
    """
    Register all ESG variables with the FinancialVariableRegistry singleton

    This function should be called during application initialization to ensure
    ESG variables are available throughout the system.
    """
    from core.data_processing.financial_variable_registry import FinancialVariableRegistry

    registry = FinancialVariableRegistry()
    esg_vars = get_esg_variable_definitions()

    logger = logging.getLogger(__name__)

    registered_count = 0
    for var_name, var_def in esg_vars.items():
        try:
            # Convert ESGVariableDefinition to VariableDefinition for registry
            standard_var_def = VariableDefinition(
                name=var_def.name,
                category=var_def.category,
                data_type=var_def.data_type,
                units=var_def.units,
                description=var_def.description,
                aliases=var_def.aliases,
                validation_rules=var_def.validation_rules,
                required=getattr(var_def, 'required', False),
                default_value=getattr(var_def, 'default_value', None)
            )

            registry.register_variable(standard_var_def)
            registered_count += 1

        except Exception as e:
            logger.warning(f"Failed to register ESG variable '{var_name}': {e}")

    logger.info(f"Successfully registered {registered_count} ESG variables with FinancialVariableRegistry")
    return registered_count