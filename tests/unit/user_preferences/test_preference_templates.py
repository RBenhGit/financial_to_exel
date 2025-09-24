"""
Tests for Preference Templates System

Test suite for the preference template and preset system functionality.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.user_preferences.preference_templates import (
    PreferenceTemplateManager, PreferenceTemplate, TemplateCategory, TemplateTags,
    get_template_manager
)
from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, AnalysisMethodology,
    CurrencyPreference, RegionPreference
)


class TestPreferenceTemplate:
    """Test PreferenceTemplate class"""

    def test_template_creation(self):
        """Test creating a preference template"""
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.10,
            methodology=AnalysisMethodology.CONSERVATIVE
        )

        preferences = UserPreferences(financial=financial_prefs)

        template = PreferenceTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category=TemplateCategory.USER_LEVEL,
            tags=[TemplateTags.BEGINNER_FRIENDLY],
            preferences=preferences
        )

        assert template.template_id == "test_template"
        assert template.name == "Test Template"
        assert template.category == TemplateCategory.USER_LEVEL
        assert TemplateTags.BEGINNER_FRIENDLY in template.tags
        assert template.preferences.financial.default_discount_rate == 0.10

    def test_template_to_dict(self):
        """Test converting template to dictionary"""
        template = PreferenceTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category=TemplateCategory.USER_LEVEL,
            preferences=UserPreferences()
        )

        template_dict = template.to_dict()

        assert template_dict['template_id'] == "test_template"
        assert template_dict['name'] == "Test Template"
        assert template_dict['category'] == "user_level"
        assert 'preferences' in template_dict


class TestPreferenceTemplateManager:
    """Test PreferenceTemplateManager class"""

    def setup_method(self):
        """Setup for each test method"""
        self.manager = PreferenceTemplateManager()

    def test_manager_initialization(self):
        """Test manager initializes with default templates"""
        templates = self.manager.list_templates()
        assert len(templates) > 0

        # Check for some expected default templates
        template_ids = [t.template_id for t in templates]
        assert "beginner_conservative" in template_ids
        assert "professional_value" in template_ids
        assert "expert_quantitative" in template_ids

    def test_get_template(self):
        """Test getting a specific template"""
        template = self.manager.get_template("beginner_conservative")
        assert template is not None
        assert template.template_id == "beginner_conservative"
        assert template.name == "Conservative Beginner"
        assert TemplateTags.BEGINNER_FRIENDLY in template.tags
        assert TemplateTags.CONSERVATIVE in template.tags

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist"""
        template = self.manager.get_template("nonexistent_template")
        assert template is None

    def test_list_templates_no_filter(self):
        """Test listing all templates without filters"""
        templates = self.manager.list_templates()
        assert len(templates) > 0
        assert all(isinstance(t, PreferenceTemplate) for t in templates)

    def test_list_templates_by_category(self):
        """Test listing templates filtered by category"""
        strategy_templates = self.manager.list_templates(category=TemplateCategory.INVESTMENT_STRATEGY)
        assert len(strategy_templates) > 0
        assert all(t.category == TemplateCategory.INVESTMENT_STRATEGY for t in strategy_templates)

    def test_list_templates_by_tags(self):
        """Test listing templates filtered by tags"""
        beginner_templates = self.manager.list_templates(tags=[TemplateTags.BEGINNER_FRIENDLY])
        assert len(beginner_templates) > 0
        assert all(TemplateTags.BEGINNER_FRIENDLY in t.tags for t in beginner_templates)

    def test_list_templates_sorted_by_popularity(self):
        """Test templates are sorted by popularity"""
        templates = self.manager.list_templates(sort_by="popularity")
        assert len(templates) > 1

        # Check that templates are sorted by popularity (descending)
        for i in range(len(templates) - 1):
            assert templates[i].popularity_score >= templates[i + 1].popularity_score

    def test_list_templates_sorted_by_name(self):
        """Test templates are sorted by name"""
        templates = self.manager.list_templates(sort_by="name")
        assert len(templates) > 1

        # Check that templates are sorted by name (ascending)
        for i in range(len(templates) - 1):
            assert templates[i].name <= templates[i + 1].name

    def test_get_recommended_templates_beginner(self):
        """Test getting recommended templates for beginners"""
        templates = self.manager.get_recommended_templates("beginner")
        assert len(templates) > 0
        assert all(TemplateTags.BEGINNER_FRIENDLY in t.tags for t in templates)

    def test_get_recommended_templates_expert(self):
        """Test getting recommended templates for experts"""
        templates = self.manager.get_recommended_templates("expert")
        assert len(templates) > 0
        # Expert templates should have advanced features
        template_ids = [t.template_id for t in templates]
        assert "expert_quantitative" in template_ids

    def test_search_templates(self):
        """Test searching templates by query"""
        # Search by name
        conservative_templates = self.manager.search_templates("conservative")
        assert len(conservative_templates) > 0
        assert any("conservative" in t.name.lower() for t in conservative_templates)

        # Search by description
        value_templates = self.manager.search_templates("value")
        assert len(value_templates) > 0

        # Search by tag
        growth_templates = self.manager.search_templates("growth")
        assert len(growth_templates) > 0

    def test_apply_template(self):
        """Test applying a template to user preferences"""
        current_prefs = UserPreferences()
        original_discount_rate = current_prefs.financial.default_discount_rate

        # Apply conservative template
        new_prefs = self.manager.apply_template("beginner_conservative", current_prefs)

        assert new_prefs is not None
        assert isinstance(new_prefs, UserPreferences)

        # Check that template was applied (conservative template has higher discount rate)
        assert new_prefs.financial.default_discount_rate > original_discount_rate
        assert new_prefs.financial.methodology == AnalysisMethodology.CONSERVATIVE

    def test_apply_nonexistent_template(self):
        """Test applying a template that doesn't exist"""
        current_prefs = UserPreferences()

        with pytest.raises(ValueError, match="Template nonexistent_template not found"):
            self.manager.apply_template("nonexistent_template", current_prefs)

    def test_create_custom_template(self):
        """Test creating a custom template"""
        custom_prefs = UserPreferences(
            financial=FinancialPreferences(default_discount_rate=0.15)
        )

        template = self.manager.create_custom_template(
            template_id="my_custom_template",
            name="My Custom Template",
            description="My personal template",
            preferences=custom_prefs,
            author="test_user"
        )

        assert template.template_id == "my_custom_template"
        assert template.name == "My Custom Template"
        assert template.author == "test_user"
        assert template.preferences.financial.default_discount_rate == 0.15

    def test_create_duplicate_template(self):
        """Test creating a template with existing ID"""
        custom_prefs = UserPreferences()

        with pytest.raises(ValueError, match="Template beginner_conservative already exists"):
            self.manager.create_custom_template(
                template_id="beginner_conservative",  # This already exists
                name="Duplicate Template",
                description="This should fail",
                preferences=custom_prefs
            )

    def test_delete_custom_template(self):
        """Test deleting a custom template"""
        # First create a custom template
        custom_prefs = UserPreferences()
        self.manager.create_custom_template(
            template_id="deletable_template",
            name="Deletable Template",
            description="This will be deleted",
            preferences=custom_prefs,
            author="test_user"
        )

        # Verify it exists
        template = self.manager.get_template("deletable_template")
        assert template is not None

        # Delete it
        success = self.manager.delete_template("deletable_template")
        assert success is True

        # Verify it's gone
        template = self.manager.get_template("deletable_template")
        assert template is None

    def test_delete_system_template(self):
        """Test that system templates cannot be deleted"""
        with pytest.raises(ValueError, match="Cannot delete system templates"):
            self.manager.delete_template("beginner_conservative")

    def test_delete_nonexistent_template(self):
        """Test deleting a template that doesn't exist"""
        success = self.manager.delete_template("nonexistent_template")
        assert success is False

    def test_get_template_categories(self):
        """Test getting all template categories"""
        categories = self.manager.get_template_categories()
        assert len(categories) == len(TemplateCategory)
        assert TemplateCategory.USER_LEVEL in categories
        assert TemplateCategory.INVESTMENT_STRATEGY in categories

    def test_get_template_tags(self):
        """Test getting all template tags"""
        tags = self.manager.get_template_tags()
        assert len(tags) == len(TemplateTags)
        assert TemplateTags.BEGINNER_FRIENDLY in tags
        assert TemplateTags.CONSERVATIVE in tags

    def test_template_usage_tracking(self):
        """Test that template usage is tracked"""
        template_id = "beginner_conservative"
        template = self.manager.get_template(template_id)
        original_usage = template.usage_count

        # Apply template (this should increment usage)
        current_prefs = UserPreferences()
        self.manager.apply_template(template_id, current_prefs)

        # Check usage was incremented
        updated_template = self.manager.get_template(template_id)
        assert updated_template.usage_count == original_usage + 1


class TestSpecificTemplates:
    """Test specific template configurations"""

    def setup_method(self):
        """Setup for each test method"""
        self.manager = PreferenceTemplateManager()

    def test_beginner_conservative_template(self):
        """Test beginner conservative template settings"""
        template = self.manager.get_template("beginner_conservative")
        assert template is not None

        financial = template.preferences.financial
        assert financial.methodology == AnalysisMethodology.CONSERVATIVE
        assert financial.default_discount_rate == 0.12  # Higher for conservatism
        assert financial.default_terminal_growth_rate == 0.02  # Conservative growth
        assert financial.dcf_sensitivity_analysis is True

        display = template.preferences.display
        assert display.show_advanced_options is False  # Simplified for beginners
        assert display.show_tooltips is True  # Helpful for beginners

    def test_professional_value_template(self):
        """Test professional value investor template"""
        template = self.manager.get_template("professional_value")
        assert template is not None

        financial = template.preferences.financial
        assert financial.methodology == AnalysisMethodology.CONSERVATIVE
        assert financial.default_discount_rate == 0.08  # Lower for value approach
        assert financial.dcf_terminal_method == "exit_multiple"
        assert "margin_of_safety" in financial.custom_parameters

        watch_list = template.preferences.watch_lists
        assert "fcf_yield" in watch_list.default_columns
        assert "debt_to_equity" in watch_list.default_columns

    def test_expert_quantitative_template(self):
        """Test expert quantitative template"""
        template = self.manager.get_template("expert_quantitative")
        assert template is not None

        financial = template.preferences.financial
        assert financial.methodology == AnalysisMethodology.CUSTOM
        assert financial.use_country_risk_premium is True
        assert "monte_carlo_simulations" in financial.custom_parameters

        display = template.preferences.display
        assert display.show_advanced_options is True
        assert display.decimal_places == 4  # Higher precision

    def test_emerging_markets_template(self):
        """Test emerging markets template"""
        template = self.manager.get_template("emerging_markets")
        assert template is not None

        financial = template.preferences.financial
        assert financial.default_discount_rate == 0.13  # Higher for EM risk
        assert financial.use_country_risk_premium is True
        assert "country_risk_premium" in financial.custom_parameters
        assert "currency_volatility_adjustment" in financial.custom_parameters


class TestGlobalTemplateManager:
    """Test global template manager function"""

    def test_get_template_manager_singleton(self):
        """Test that get_template_manager returns the same instance"""
        manager1 = get_template_manager()
        manager2 = get_template_manager()
        assert manager1 is manager2

    def test_template_manager_functionality(self):
        """Test that global manager has expected functionality"""
        manager = get_template_manager()
        assert isinstance(manager, PreferenceTemplateManager)

        templates = manager.list_templates()
        assert len(templates) > 0


if __name__ == "__main__":
    pytest.main([__file__])