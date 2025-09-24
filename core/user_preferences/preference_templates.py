"""
Preference Templates and Presets

Provides predefined preference templates for different user types and investment strategies.
Templates can be used to quickly configure user preferences based on common patterns.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .user_profile import (
    UserPreferences, FinancialPreferences, DisplayPreferences,
    NotificationPreferences, DataSourcePreferences, WatchListPreferences,
    AnalysisMethodology, CurrencyPreference, RegionPreference
)

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Categories for organizing preference templates"""
    USER_LEVEL = "user_level"          # Beginner, Professional, Expert
    INVESTMENT_STRATEGY = "strategy"    # Conservative, Growth, Value, etc.
    REGION_FOCUS = "region"            # US, Europe, Asia, Global
    ANALYSIS_TYPE = "analysis"         # Quick, Detailed, Research-intensive


class TemplateTags(Enum):
    """Tags for template filtering and search"""
    BEGINNER_FRIENDLY = "beginner_friendly"
    QUICK_SETUP = "quick_setup"
    COMPREHENSIVE = "comprehensive"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    HIGH_FREQUENCY = "high_frequency"
    LONG_TERM = "long_term"
    DIVIDEND_FOCUSED = "dividend_focused"
    GROWTH_FOCUSED = "growth_focused"
    VALUE_FOCUSED = "value_focused"
    EMERGING_MARKETS = "emerging_markets"
    DEVELOPED_MARKETS = "developed_markets"


@dataclass
class PreferenceTemplate:
    """A predefined preference template"""

    template_id: str
    name: str
    description: str
    category: TemplateCategory
    tags: List[TemplateTags] = field(default_factory=list)

    # Template preferences
    preferences: UserPreferences = field(default_factory=UserPreferences)

    # Template metadata
    version: str = "1.0"
    author: str = "system"
    created_date: str = ""
    popularity_score: float = 0.0
    usage_count: int = 0

    # Customization options
    is_customizable: bool = True
    locked_settings: List[str] = field(default_factory=list)  # Settings that can't be modified

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary format"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'tags': [tag.value for tag in self.tags],
            'preferences': self.preferences.to_dict() if hasattr(self.preferences, 'to_dict') else self.preferences.__dict__,
            'version': self.version,
            'author': self.author,
            'created_date': self.created_date,
            'popularity_score': self.popularity_score,
            'usage_count': self.usage_count,
            'is_customizable': self.is_customizable,
            'locked_settings': self.locked_settings
        }


class PreferenceTemplateManager:
    """Manages preference templates and presets"""

    def __init__(self):
        self._templates: Dict[str, PreferenceTemplate] = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        """Initialize the default system templates"""

        # Beginner Templates
        self._add_beginner_conservative_template()
        self._add_beginner_balanced_template()

        # Professional Templates
        self._add_professional_value_template()
        self._add_professional_growth_template()
        self._add_professional_dividend_template()

        # Expert Templates
        self._add_expert_quantitative_template()
        self._add_expert_contrarian_template()

        # Regional Templates
        self._add_us_focused_template()
        self._add_international_template()
        self._add_emerging_markets_template()

        # Analysis Type Templates
        self._add_quick_analysis_template()
        self._add_comprehensive_template()

        logger.info(f"Initialized {len(self._templates)} default preference templates")

    def _add_beginner_conservative_template(self) -> None:
        """Conservative template for beginners"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.12,  # Higher discount rate for conservatism
            default_terminal_growth_rate=0.02,  # Conservative growth
            default_projection_years=5,
            risk_free_rate=0.03,
            market_risk_premium=0.07,  # Higher risk premium
            methodology=AnalysisMethodology.CONSERVATIVE,
            primary_currency=CurrencyPreference.USD,
            preferred_regions=[RegionPreference.NORTH_AMERICA],
            dcf_sensitivity_analysis=True,
            include_beta_adjustment=True,
            use_country_risk_premium=False
        )

        display_prefs = DisplayPreferences(
            decimal_places=2,
            chart_theme="plotly",
            show_advanced_options=False,  # Hide complexity for beginners
            show_tooltips=True,
            compact_mode=False,
            animation_enabled=True
        )

        notification_prefs = NotificationPreferences(
            show_calculation_warnings=True,
            show_data_quality_alerts=True,
            show_performance_tips=True,
            price_change_threshold=0.03,  # More sensitive alerts
            valuation_change_threshold=0.08
        )

        data_source_prefs = DataSourcePreferences(
            prefer_excel_over_api=True,
            strict_validation=True,  # Stricter validation for safety
            allow_missing_data=False,
            outlier_detection=True,
            default_export_format="xlsx"
        )

        watch_list_prefs = WatchListPreferences(
            max_companies_per_list=20,  # Smaller lists for beginners
            auto_sort_by="market_cap",
            default_columns=["ticker", "company_name", "current_price", "market_cap", "pe_ratio"]
        )

        template = PreferenceTemplate(
            template_id="beginner_conservative",
            name="Conservative Beginner",
            description="Safe, conservative settings for new investors with simplified interface and higher safety margins",
            category=TemplateCategory.USER_LEVEL,
            tags=[TemplateTags.BEGINNER_FRIENDLY, TemplateTags.CONSERVATIVE, TemplateTags.QUICK_SETUP],
            preferences=UserPreferences(
                financial=financial_prefs,
                display=display_prefs,
                notifications=notification_prefs,
                data_sources=data_source_prefs,
                watch_lists=watch_list_prefs
            ),
            popularity_score=8.5
        )

        self._templates[template.template_id] = template

    def _add_beginner_balanced_template(self) -> None:
        """Balanced template for beginners"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.10,
            default_terminal_growth_rate=0.025,
            default_projection_years=5,
            methodology=AnalysisMethodology.MODERATE,
            primary_currency=CurrencyPreference.USD,
            preferred_regions=[RegionPreference.GLOBAL],
            dcf_sensitivity_analysis=True
        )

        display_prefs = DisplayPreferences(
            show_advanced_options=False,
            show_tooltips=True,
            compact_mode=False
        )

        template = PreferenceTemplate(
            template_id="beginner_balanced",
            name="Balanced Beginner",
            description="Moderate risk settings with balanced approach for learning investors",
            category=TemplateCategory.USER_LEVEL,
            tags=[TemplateTags.BEGINNER_FRIENDLY, TemplateTags.QUICK_SETUP],
            preferences=UserPreferences(financial=financial_prefs, display=display_prefs),
            popularity_score=7.8
        )

        self._templates[template.template_id] = template

    def _add_professional_value_template(self) -> None:
        """Value investing template for professionals"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.08,  # Lower discount rate for value approach
            default_terminal_growth_rate=0.02,  # Conservative terminal growth
            default_projection_years=7,  # Longer projection for value analysis
            methodology=AnalysisMethodology.CONSERVATIVE,
            dcf_terminal_method="exit_multiple",  # Value investors often use multiples
            dcf_sensitivity_analysis=True,
            include_beta_adjustment=True,
            custom_parameters={
                "margin_of_safety": 0.25,  # 25% margin of safety
                "focus_on_fcf": True,
                "debt_penalty_factor": 1.2
            }
        )

        watch_list_prefs = WatchListPreferences(
            auto_sort_by="fcf_yield",  # Value investors focus on FCF yield
            default_columns=[
                "ticker", "company_name", "current_price", "market_cap",
                "pe_ratio", "pb_ratio", "fcf_yield", "debt_to_equity", "roe"
            ],
            price_alerts_enabled=True,
            valuation_alerts_enabled=True
        )

        template = PreferenceTemplate(
            template_id="professional_value",
            name="Value Investor",
            description="Conservative approach focusing on undervalued companies with strong fundamentals",
            category=TemplateCategory.INVESTMENT_STRATEGY,
            tags=[TemplateTags.VALUE_FOCUSED, TemplateTags.CONSERVATIVE, TemplateTags.LONG_TERM],
            preferences=UserPreferences(
                financial=financial_prefs,
                watch_lists=watch_list_prefs
            ),
            popularity_score=8.2
        )

        self._templates[template.template_id] = template

    def _add_professional_growth_template(self) -> None:
        """Growth investing template for professionals"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.09,
            default_terminal_growth_rate=0.035,  # Higher terminal growth expectation
            default_projection_years=8,
            methodology=AnalysisMethodology.AGGRESSIVE,
            custom_parameters={
                "growth_sustainability_factor": 0.8,
                "revenue_growth_weight": 1.5,
                "market_expansion_factor": 1.2
            }
        )

        watch_list_prefs = WatchListPreferences(
            auto_sort_by="performance",
            default_columns=[
                "ticker", "company_name", "current_price", "market_cap",
                "revenue_growth", "earnings_growth", "pe_ratio", "peg_ratio", "price_momentum"
            ]
        )

        template = PreferenceTemplate(
            template_id="professional_growth",
            name="Growth Investor",
            description="Focus on high-growth companies with strong revenue and earnings expansion",
            category=TemplateCategory.INVESTMENT_STRATEGY,
            tags=[TemplateTags.GROWTH_FOCUSED, TemplateTags.AGGRESSIVE, TemplateTags.LONG_TERM],
            preferences=UserPreferences(
                financial=financial_prefs,
                watch_lists=watch_list_prefs
            ),
            popularity_score=7.9
        )

        self._templates[template.template_id] = template

    def _add_professional_dividend_template(self) -> None:
        """Dividend-focused template for professionals"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.07,  # Lower discount rate for stable dividend stocks
            default_terminal_growth_rate=0.02,
            methodology=AnalysisMethodology.CONSERVATIVE,
            custom_parameters={
                "dividend_sustainability_weight": 2.0,
                "payout_ratio_threshold": 0.6,
                "dividend_growth_importance": 1.5
            }
        )

        watch_list_prefs = WatchListPreferences(
            auto_sort_by="dividend_yield",
            default_columns=[
                "ticker", "company_name", "current_price", "dividend_yield",
                "payout_ratio", "dividend_growth_rate", "fcf_yield", "debt_to_equity"
            ]
        )

        template = PreferenceTemplate(
            template_id="professional_dividend",
            name="Dividend Investor",
            description="Focus on sustainable dividend-paying companies with strong cash flows",
            category=TemplateCategory.INVESTMENT_STRATEGY,
            tags=[TemplateTags.DIVIDEND_FOCUSED, TemplateTags.CONSERVATIVE, TemplateTags.LONG_TERM],
            preferences=UserPreferences(
                financial=financial_prefs,
                watch_lists=watch_list_prefs
            ),
            popularity_score=7.6
        )

        self._templates[template.template_id] = template

    def _add_expert_quantitative_template(self) -> None:
        """Quantitative analysis template for experts"""
        financial_prefs = FinancialPreferences(
            methodology=AnalysisMethodology.CUSTOM,
            dcf_sensitivity_analysis=True,
            include_beta_adjustment=True,
            use_country_risk_premium=True,
            custom_parameters={
                "monte_carlo_simulations": 10000,
                "var_confidence_level": 0.05,
                "stress_test_scenarios": ["recession", "inflation", "market_crash"],
                "correlation_analysis": True,
                "regime_switching_model": True
            }
        )

        display_prefs = DisplayPreferences(
            show_advanced_options=True,
            decimal_places=4,  # Higher precision for quantitative analysis
            chart_theme="plotly"
        )

        data_source_prefs = DataSourcePreferences(
            prefer_excel_over_api=False,  # Experts prefer API data for automation
            auto_refresh_data=True,
            strict_validation=False,  # More flexible for custom data
            outlier_detection=True
        )

        template = PreferenceTemplate(
            template_id="expert_quantitative",
            name="Quantitative Analyst",
            description="Advanced statistical and mathematical analysis with custom models and simulations",
            category=TemplateCategory.USER_LEVEL,
            tags=[TemplateTags.COMPREHENSIVE, TemplateTags.HIGH_FREQUENCY],
            preferences=UserPreferences(
                financial=financial_prefs,
                display=display_prefs,
                data_sources=data_source_prefs
            ),
            popularity_score=6.8
        )

        self._templates[template.template_id] = template

    def _add_expert_contrarian_template(self) -> None:
        """Contrarian investing template for experts"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.11,  # Higher discount rate for contrarian bets
            methodology=AnalysisMethodology.CUSTOM,
            custom_parameters={
                "sentiment_analysis_weight": -1.0,  # Contrarian to sentiment
                "volatility_opportunity_factor": 1.3,
                "distressed_value_multiplier": 0.7,
                "mean_reversion_timeframe": 24  # months
            }
        )

        notification_prefs = NotificationPreferences(
            price_change_threshold=0.15,  # Look for large moves
            valuation_change_threshold=0.20
        )

        template = PreferenceTemplate(
            template_id="expert_contrarian",
            name="Contrarian Investor",
            description="Opportunistic approach targeting undervalued or distressed situations",
            category=TemplateCategory.INVESTMENT_STRATEGY,
            tags=[TemplateTags.VALUE_FOCUSED, TemplateTags.AGGRESSIVE],
            preferences=UserPreferences(
                financial=financial_prefs,
                notifications=notification_prefs
            ),
            popularity_score=6.2
        )

        self._templates[template.template_id] = template

    def _add_us_focused_template(self) -> None:
        """US market focused template"""
        financial_prefs = FinancialPreferences(
            primary_currency=CurrencyPreference.USD,
            preferred_regions=[RegionPreference.NORTH_AMERICA],
            risk_free_rate=0.035,  # US 10-year treasury
            market_risk_premium=0.055,
            use_country_risk_premium=False
        )

        template = PreferenceTemplate(
            template_id="us_focused",
            name="US Market Focus",
            description="Optimized for US market analysis with USD-based calculations",
            category=TemplateCategory.REGION_FOCUS,
            tags=[TemplateTags.DEVELOPED_MARKETS],
            preferences=UserPreferences(financial=financial_prefs),
            popularity_score=8.0
        )

        self._templates[template.template_id] = template

    def _add_international_template(self) -> None:
        """International markets template"""
        financial_prefs = FinancialPreferences(
            preferred_regions=[RegionPreference.EUROPE, RegionPreference.ASIA_PACIFIC],
            use_country_risk_premium=True,
            custom_parameters={
                "currency_hedging_cost": 0.005,
                "political_risk_adjustment": 0.01,
                "liquidity_discount": 0.02
            }
        )

        template = PreferenceTemplate(
            template_id="international",
            name="International Markets",
            description="Multi-region analysis with currency and country risk adjustments",
            category=TemplateCategory.REGION_FOCUS,
            tags=[TemplateTags.DEVELOPED_MARKETS, TemplateTags.COMPREHENSIVE],
            preferences=UserPreferences(financial=financial_prefs),
            popularity_score=7.1
        )

        self._templates[template.template_id] = template

    def _add_emerging_markets_template(self) -> None:
        """Emerging markets template"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.13,  # Higher discount rate for EM
            preferred_regions=[RegionPreference.EMERGING_MARKETS],
            use_country_risk_premium=True,
            custom_parameters={
                "country_risk_premium": 0.04,
                "currency_volatility_adjustment": 0.02,
                "political_instability_factor": 1.2,
                "liquidity_discount": 0.05
            }
        )

        template = PreferenceTemplate(
            template_id="emerging_markets",
            name="Emerging Markets",
            description="Higher risk analysis framework for emerging market investments",
            category=TemplateCategory.REGION_FOCUS,
            tags=[TemplateTags.EMERGING_MARKETS, TemplateTags.AGGRESSIVE],
            preferences=UserPreferences(financial=financial_prefs),
            popularity_score=6.5
        )

        self._templates[template.template_id] = template

    def _add_quick_analysis_template(self) -> None:
        """Quick analysis template"""
        financial_prefs = FinancialPreferences(
            default_projection_years=3,  # Shorter projection
            dcf_sensitivity_analysis=False  # Skip sensitivity for speed
        )

        display_prefs = DisplayPreferences(
            show_advanced_options=False,
            compact_mode=True,
            animation_enabled=False  # Faster rendering
        )

        data_source_prefs = DataSourcePreferences(
            api_timeout_seconds=15,  # Shorter timeout
            max_retry_attempts=1,
            strict_validation=False
        )

        template = PreferenceTemplate(
            template_id="quick_analysis",
            name="Quick Analysis",
            description="Fast analysis with simplified calculations for rapid screening",
            category=TemplateCategory.ANALYSIS_TYPE,
            tags=[TemplateTags.QUICK_SETUP, TemplateTags.HIGH_FREQUENCY],
            preferences=UserPreferences(
                financial=financial_prefs,
                display=display_prefs,
                data_sources=data_source_prefs
            ),
            popularity_score=7.4
        )

        self._templates[template.template_id] = template

    def _add_comprehensive_template(self) -> None:
        """Comprehensive analysis template"""
        financial_prefs = FinancialPreferences(
            default_projection_years=10,  # Longer projection
            dcf_sensitivity_analysis=True,
            include_beta_adjustment=True,
            use_country_risk_premium=True,
            custom_parameters={
                "scenario_analysis": True,
                "monte_carlo_runs": 1000,
                "multiple_valuation_methods": True
            }
        )

        display_prefs = DisplayPreferences(
            show_advanced_options=True,
            decimal_places=3,
            show_tooltips=True
        )

        template = PreferenceTemplate(
            template_id="comprehensive",
            name="Comprehensive Analysis",
            description="Detailed analysis with multiple scenarios and validation methods",
            category=TemplateCategory.ANALYSIS_TYPE,
            tags=[TemplateTags.COMPREHENSIVE, TemplateTags.LONG_TERM],
            preferences=UserPreferences(
                financial=financial_prefs,
                display=display_prefs
            ),
            popularity_score=6.9
        )

        self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[PreferenceTemplate]:
        """Get a specific template by ID"""
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[TemplateTags]] = None,
        sort_by: str = "popularity"
    ) -> List[PreferenceTemplate]:
        """
        List available templates with optional filtering

        Args:
            category: Filter by template category
            tags: Filter by template tags (must have all specified tags)
            sort_by: Sort criteria ("popularity", "name", "usage")

        Returns:
            List of matching templates
        """
        templates = list(self._templates.values())

        # Apply category filter
        if category:
            templates = [t for t in templates if t.category == category]

        # Apply tags filter
        if tags:
            templates = [t for t in templates if all(tag in t.tags for tag in tags)]

        # Sort templates
        if sort_by == "popularity":
            templates.sort(key=lambda t: t.popularity_score, reverse=True)
        elif sort_by == "name":
            templates.sort(key=lambda t: t.name)
        elif sort_by == "usage":
            templates.sort(key=lambda t: t.usage_count, reverse=True)

        return templates

    def get_recommended_templates(self, user_experience: str = "beginner") -> List[PreferenceTemplate]:
        """
        Get recommended templates based on user experience level

        Args:
            user_experience: "beginner", "intermediate", or "expert"

        Returns:
            List of recommended templates
        """
        if user_experience.lower() == "beginner":
            return self.list_templates(tags=[TemplateTags.BEGINNER_FRIENDLY])
        elif user_experience.lower() == "expert":
            return self.list_templates(category=TemplateCategory.USER_LEVEL)
        else:  # intermediate
            # Return a mix of strategy and analysis templates
            strategy_templates = self.list_templates(category=TemplateCategory.INVESTMENT_STRATEGY)
            analysis_templates = self.list_templates(category=TemplateCategory.ANALYSIS_TYPE)
            return strategy_templates + analysis_templates

    def search_templates(self, query: str) -> List[PreferenceTemplate]:
        """
        Search templates by name, description, or tags

        Args:
            query: Search query string

        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        matching_templates = []

        for template in self._templates.values():
            # Search in name and description
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower()):
                matching_templates.append(template)
                continue

            # Search in tags
            for tag in template.tags:
                if query_lower in tag.value.lower():
                    matching_templates.append(template)
                    break

        return matching_templates

    def apply_template(self, template_id: str, user_preferences: UserPreferences) -> UserPreferences:
        """
        Apply a template to existing user preferences

        Args:
            template_id: ID of template to apply
            user_preferences: Current user preferences to modify

        Returns:
            Updated user preferences
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Create a copy of the template preferences
        new_preferences = UserPreferences(
            financial=template.preferences.financial,
            display=template.preferences.display,
            notifications=template.preferences.notifications,
            data_sources=template.preferences.data_sources,
            watch_lists=template.preferences.watch_lists
        )

        # Update usage count
        template.usage_count += 1

        logger.info(f"Applied template {template_id} ({template.name})")
        return new_preferences

    def create_custom_template(
        self,
        template_id: str,
        name: str,
        description: str,
        preferences: UserPreferences,
        category: TemplateCategory = TemplateCategory.USER_LEVEL,
        tags: Optional[List[TemplateTags]] = None,
        author: str = "user"
    ) -> PreferenceTemplate:
        """
        Create a custom user template

        Args:
            template_id: Unique ID for the template
            name: Template name
            description: Template description
            preferences: Template preferences
            category: Template category
            tags: Template tags
            author: Template author

        Returns:
            Created template
        """
        if template_id in self._templates:
            raise ValueError(f"Template {template_id} already exists")

        template = PreferenceTemplate(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            preferences=preferences,
            author=author
        )

        self._templates[template_id] = template
        logger.info(f"Created custom template {template_id} ({name})")
        return template

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a custom template (system templates cannot be deleted)

        Args:
            template_id: ID of template to delete

        Returns:
            True if deleted successfully
        """
        template = self.get_template(template_id)
        if not template:
            return False

        if template.author == "system":
            raise ValueError("Cannot delete system templates")

        del self._templates[template_id]
        logger.info(f"Deleted template {template_id}")
        return True

    def get_template_categories(self) -> List[TemplateCategory]:
        """Get all available template categories"""
        return list(TemplateCategory)

    def get_template_tags(self) -> List[TemplateTags]:
        """Get all available template tags"""
        return list(TemplateTags)


# Global instance
_template_manager: Optional[PreferenceTemplateManager] = None


def get_template_manager() -> PreferenceTemplateManager:
    """Get the global template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = PreferenceTemplateManager()
    return _template_manager