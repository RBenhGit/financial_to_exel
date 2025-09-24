"""
Preference Templates Example

Demonstrates how to use the preference template system for different user types
and investment strategies.
"""

import sys
import os
import logging
from typing import List

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_preferences.preference_templates import (
    get_template_manager, TemplateCategory, TemplateTags
)
from core.user_preferences.preference_manager import get_preference_manager
from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, create_default_user_profile,
    AnalysisMethodology, CurrencyPreference
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demonstrate_template_system():
    """Demonstrate the complete preference template system"""

    print("=" * 60)
    print("PREFERENCE TEMPLATES SYSTEM DEMONSTRATION")
    print("=" * 60)

    # Get managers
    template_manager = get_template_manager()
    preference_manager = get_preference_manager()

    # 1. Show available templates
    print("\n1. AVAILABLE TEMPLATES")
    print("-" * 30)
    templates = template_manager.list_templates()
    for template in templates:
        print(f"• {template.name} ({template.template_id})")
        print(f"  Category: {template.category.value}")
        print(f"  Tags: {', '.join([tag.value for tag in template.tags[:3]])}")
        print(f"  Popularity: {template.popularity_score}/10")
        print()

    # 2. Demonstrate template filtering
    print("\n2. TEMPLATE FILTERING EXAMPLES")
    print("-" * 35)

    # Filter by category
    print("Strategy-focused templates:")
    strategy_templates = template_manager.list_templates(category=TemplateCategory.INVESTMENT_STRATEGY)
    for template in strategy_templates:
        print(f"  • {template.name}: {template.description[:50]}...")

    print("\nBeginner-friendly templates:")
    beginner_templates = template_manager.list_templates(tags=[TemplateTags.BEGINNER_FRIENDLY])
    for template in beginner_templates:
        print(f"  • {template.name}: {template.description[:50]}...")

    # 3. Template search
    print("\n3. TEMPLATE SEARCH")
    print("-" * 20)
    search_results = template_manager.search_templates("conservative")
    print("Search results for 'conservative':")
    for template in search_results:
        print(f"  • {template.name}")

    # 4. Create sample users and apply templates
    print("\n4. USER SCENARIOS")
    print("-" * 18)

    # Scenario 1: New beginner investor
    print("Scenario 1: New Beginner Investor")
    beginner_user = preference_manager.create_user(
        user_id="beginner_user_001",
        username="Alice Newcomer",
        email="alice@example.com"
    )

    # Apply beginner template
    new_prefs = template_manager.apply_template("beginner_conservative", beginner_user.preferences)
    preference_manager.update_preferences(beginner_user.user_id, new_prefs)

    print(f"Applied 'Conservative Beginner' template to {beginner_user.username}")
    print(f"  Discount Rate: {new_prefs.financial.default_discount_rate:.1%}")
    print(f"  Methodology: {new_prefs.financial.methodology.value}")
    print(f"  Show Advanced Options: {new_prefs.display.show_advanced_options}")

    # Scenario 2: Professional value investor
    print("\nScenario 2: Professional Value Investor")
    value_user = preference_manager.create_user(
        user_id="value_investor_001",
        username="Bob Buffett",
        email="bob@example.com"
    )

    # Apply value investor template
    value_prefs = template_manager.apply_template("professional_value", value_user.preferences)
    preference_manager.update_preferences(value_user.user_id, value_prefs)

    print(f"Applied 'Value Investor' template to {value_user.username}")
    print(f"  Discount Rate: {value_prefs.financial.default_discount_rate:.1%}")
    print(f"  Terminal Method: {value_prefs.financial.dcf_terminal_method}")
    print(f"  Custom Parameters: {list(value_prefs.financial.custom_parameters.keys())}")

    # Scenario 3: Expert quantitative analyst
    print("\nScenario 3: Expert Quantitative Analyst")
    quant_user = preference_manager.create_user(
        user_id="quant_analyst_001",
        username="Dr. Charlie Quantson",
        email="charlie@quantfund.com"
    )

    # Apply quantitative template
    quant_prefs = template_manager.apply_template("expert_quantitative", quant_user.preferences)
    preference_manager.update_preferences(quant_user.user_id, quant_prefs)

    print(f"Applied 'Quantitative Analyst' template to {quant_user.username}")
    print(f"  Methodology: {quant_prefs.financial.methodology.value}")
    print(f"  Advanced Options: {quant_prefs.display.show_advanced_options}")
    print(f"  Decimal Precision: {quant_prefs.display.decimal_places}")

    # 5. Template comparison
    print("\n5. TEMPLATE COMPARISON")
    print("-" * 23)
    compare_templates = ["beginner_conservative", "professional_value", "expert_quantitative"]
    print("Comparing discount rates across user types:")
    for template_id in compare_templates:
        template = template_manager.get_template(template_id)
        discount_rate = template.preferences.financial.default_discount_rate
        print(f"  {template.name}: {discount_rate:.1%}")

    # 6. Create custom template
    print("\n6. CUSTOM TEMPLATE CREATION")
    print("-" * 30)

    # Create a custom dividend-focused template with specific settings
    custom_financial = FinancialPreferences(
        default_discount_rate=0.07,  # Lower rate for stable dividend stocks
        default_terminal_growth_rate=0.02,
        methodology=AnalysisMethodology.CONSERVATIVE,
        custom_parameters={
            "dividend_focus": True,
            "min_dividend_yield": 0.03,
            "max_payout_ratio": 0.6,
            "dividend_growth_weight": 2.0
        }
    )

    custom_preferences = UserPreferences(financial=custom_financial)

    custom_template = template_manager.create_custom_template(
        template_id="custom_dividend_focus",
        name="High-Yield Dividend Focus",
        description="Focus on high-yield, sustainable dividend-paying companies",
        preferences=custom_preferences,
        category=TemplateCategory.INVESTMENT_STRATEGY,
        tags=[TemplateTags.DIVIDEND_FOCUSED, TemplateTags.CONSERVATIVE],
        author="example_user"
    )

    print(f"Created custom template: {custom_template.name}")
    print(f"  Discount Rate: {custom_template.preferences.financial.default_discount_rate:.1%}")
    print(f"  Custom Parameters: {list(custom_template.preferences.financial.custom_parameters.keys())}")

    # 7. Template recommendations
    print("\n7. TEMPLATE RECOMMENDATIONS")
    print("-" * 28)

    for experience_level in ["beginner", "intermediate", "expert"]:
        recommendations = template_manager.get_recommended_templates(experience_level)
        print(f"{experience_level.title()} recommendations:")
        for template in recommendations[:3]:  # Show top 3
            print(f"  • {template.name}")
        print()

    # 8. Usage analytics
    print("\n8. TEMPLATE USAGE ANALYTICS")
    print("-" * 29)
    all_templates = template_manager.list_templates(sort_by="usage")
    print("Most used templates:")
    for template in all_templates[:5]:
        print(f"  • {template.name}: {template.usage_count} times")

    print("\nMost popular templates:")
    popular_templates = template_manager.list_templates(sort_by="popularity")
    for template in popular_templates[:5]:
        print(f"  • {template.name}: {template.popularity_score}/10")


def demonstrate_template_integration():
    """Demonstrate integration with the financial analysis system"""

    print("\n" + "=" * 60)
    print("TEMPLATE INTEGRATION WITH FINANCIAL ANALYSIS")
    print("=" * 60)

    template_manager = get_template_manager()

    # Show how different templates affect calculation parameters
    templates_to_test = ["beginner_conservative", "professional_growth", "expert_quantitative"]

    print("\nCalculation Parameter Comparison:")
    print("-" * 38)

    for template_id in templates_to_test:
        template = template_manager.get_template(template_id)
        financial = template.preferences.financial

        print(f"\n{template.name}:")
        print(f"  Discount Rate: {financial.default_discount_rate:.1%}")
        print(f"  Terminal Growth: {financial.default_terminal_growth_rate:.1%}")
        print(f"  Projection Years: {financial.default_projection_years}")
        print(f"  Methodology: {financial.methodology.value}")
        print(f"  Currency: {financial.primary_currency.value}")

        if financial.custom_parameters:
            print(f"  Custom Parameters:")
            for param, value in financial.custom_parameters.items():
                print(f"    • {param}: {value}")


def demonstrate_advanced_features():
    """Demonstrate advanced template features"""

    print("\n" + "=" * 60)
    print("ADVANCED TEMPLATE FEATURES")
    print("=" * 60)

    template_manager = get_template_manager()

    # 1. Template versioning and metadata
    print("\n1. TEMPLATE METADATA")
    print("-" * 20)
    template = template_manager.get_template("professional_value")
    print(f"Template: {template.name}")
    print(f"Version: {template.version}")
    print(f"Author: {template.author}")
    print(f"Popularity Score: {template.popularity_score}")
    print(f"Usage Count: {template.usage_count}")
    print(f"Customizable: {template.is_customizable}")

    # 2. Template categories and tags system
    print("\n2. CATEGORIZATION SYSTEM")
    print("-" * 25)
    categories = template_manager.get_template_categories()
    tags = template_manager.get_template_tags()

    print(f"Available Categories ({len(categories)}):")
    for category in categories:
        count = len(template_manager.list_templates(category=category))
        print(f"  • {category.value.replace('_', ' ').title()}: {count} templates")

    print(f"\nAvailable Tags ({len(tags)}):")
    for tag in tags[:10]:  # Show first 10 tags
        templates_with_tag = template_manager.list_templates(tags=[tag])
        print(f"  • {tag.value.replace('_', ' ').title()}: {len(templates_with_tag)} templates")

    # 3. Template composition (combining multiple templates)
    print("\n3. TEMPLATE COMPOSITION EXAMPLE")
    print("-" * 33)

    print("Creating composite template from multiple sources:")

    # Start with base template
    base_template = template_manager.get_template("professional_value")
    composite_prefs = UserPreferences(
        financial=base_template.preferences.financial,
        display=base_template.preferences.display
    )

    # Add display preferences from expert template
    expert_template = template_manager.get_template("expert_quantitative")
    composite_prefs.display = expert_template.preferences.display

    # Add notification preferences from beginner template
    beginner_template = template_manager.get_template("beginner_conservative")
    composite_prefs.notifications = beginner_template.preferences.notifications

    print("Composite template combines:")
    print(f"  • Financial settings from: {base_template.name}")
    print(f"  • Display settings from: {expert_template.name}")
    print(f"  • Notification settings from: {beginner_template.name}")


if __name__ == "__main__":
    """Run the complete demonstration"""
    try:
        demonstrate_template_system()
        demonstrate_template_integration()
        demonstrate_advanced_features()

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\nKey Benefits of the Template System:")
        print("• Quick setup for new users")
        print("• Consistent best practices")
        print("• Customizable for specific needs")
        print("• Easy sharing and collaboration")
        print("• Built-in expertise and optimization")

    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        raise