"""
Preference Templates UI Components

Streamlit UI components for managing and applying preference templates.
"""

import streamlit as st
import logging
from typing import Optional, List

from core.user_preferences.preference_templates import (
    get_template_manager, PreferenceTemplate, TemplateCategory, TemplateTags
)
from core.user_preferences.preference_manager import get_preference_manager
from core.user_preferences.user_profile import UserPreferences

logger = logging.getLogger(__name__)


def display_template_selector() -> Optional[str]:
    """
    Display a template selection interface

    Returns:
        Selected template ID or None
    """
    template_manager = get_template_manager()

    st.subheader("🎯 Preference Templates")
    st.markdown("""
    Choose from predefined preference templates to quickly configure your analysis settings
    based on your experience level and investment strategy.
    """)

    # Template filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        experience_level = st.selectbox(
            "Experience Level",
            ["All", "Beginner", "Intermediate", "Expert"],
            help="Filter templates by experience level"
        )

    with col2:
        category_filter = st.selectbox(
            "Category",
            ["All"] + [cat.value.replace("_", " ").title() for cat in TemplateCategory],
            help="Filter templates by category"
        )

    with col3:
        strategy_filter = st.selectbox(
            "Strategy Focus",
            ["All", "Conservative", "Aggressive", "Value Focused", "Growth Focused", "Dividend Focused"],
            help="Filter templates by investment strategy"
        )

    # Get filtered templates
    templates = _get_filtered_templates(template_manager, experience_level, category_filter, strategy_filter)

    if not templates:
        st.warning("No templates match your filter criteria.")
        return None

    # Display templates
    selected_template_id = None

    for template in templates[:6]:  # Show top 6 templates
        with st.expander(f"📋 {template.name}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Description:** {template.description}")

                # Display tags
                if template.tags:
                    tag_display = " • ".join([tag.value.replace("_", " ").title() for tag in template.tags[:4]])
                    st.markdown(f"**Tags:** {tag_display}")

                # Display key settings
                _display_template_preview(template)

            with col2:
                st.markdown(f"**Popularity:** ⭐ {template.popularity_score:.1f}")
                st.markdown(f"**Usage:** {template.usage_count} times")

                if st.button(f"Select Template", key=f"select_{template.template_id}"):
                    selected_template_id = template.template_id

    return selected_template_id


def _get_filtered_templates(template_manager, experience_level: str, category_filter: str, strategy_filter: str) -> List[PreferenceTemplate]:
    """Get templates based on filter criteria"""

    # Get base templates
    if experience_level != "All":
        templates = template_manager.get_recommended_templates(experience_level.lower())
    else:
        templates = template_manager.list_templates()

    # Apply category filter
    if category_filter != "All":
        category_map = {cat.value.replace("_", " ").title(): cat for cat in TemplateCategory}
        if category_filter in category_map:
            templates = [t for t in templates if t.category == category_map[category_filter]]

    # Apply strategy filter
    if strategy_filter != "All":
        strategy_tag_map = {
            "Conservative": TemplateTags.CONSERVATIVE,
            "Aggressive": TemplateTags.AGGRESSIVE,
            "Value Focused": TemplateTags.VALUE_FOCUSED,
            "Growth Focused": TemplateTags.GROWTH_FOCUSED,
            "Dividend Focused": TemplateTags.DIVIDEND_FOCUSED
        }
        if strategy_filter in strategy_tag_map:
            target_tag = strategy_tag_map[strategy_filter]
            templates = [t for t in templates if target_tag in t.tags]

    return templates


def _display_template_preview(template: PreferenceTemplate) -> None:
    """Display a preview of template settings"""

    st.markdown("**Key Settings:**")

    # Financial settings preview
    financial = template.preferences.financial
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"• Discount Rate: {financial.default_discount_rate:.1%}")
        st.markdown(f"• Methodology: {financial.methodology.value.title()}")

    with col2:
        st.markdown(f"• Terminal Growth: {financial.default_terminal_growth_rate:.1%}")
        st.markdown(f"• Projection Years: {financial.default_projection_years}")


def apply_template_to_user(template_id: str, user_id: str) -> bool:
    """
    Apply a template to a user's preferences

    Args:
        template_id: ID of template to apply
        user_id: User ID to apply template to

    Returns:
        True if successful
    """
    try:
        template_manager = get_template_manager()
        preference_manager = get_preference_manager()

        # Get current user preferences
        current_preferences = preference_manager.get_preferences(user_id)
        if not current_preferences:
            current_preferences = UserPreferences()

        # Apply template
        new_preferences = template_manager.apply_template(template_id, current_preferences)

        # Save updated preferences
        success = preference_manager.update_preferences(user_id, new_preferences)

        if success:
            template = template_manager.get_template(template_id)
            st.success(f"✅ Applied template: {template.name}")
            logger.info(f"Applied template {template_id} to user {user_id}")
        else:
            st.error("Failed to save template preferences")

        return success

    except Exception as e:
        st.error(f"Error applying template: {e}")
        logger.error(f"Error applying template {template_id} to user {user_id}: {e}")
        return False


def display_template_comparison() -> None:
    """Display a comparison view of multiple templates"""

    template_manager = get_template_manager()

    st.subheader("📊 Template Comparison")

    # Template selection for comparison
    all_templates = template_manager.list_templates()
    template_names = [f"{t.name} ({t.template_id})" for t in all_templates]

    selected_names = st.multiselect(
        "Select templates to compare (max 3)",
        template_names,
        max_selections=3,
        help="Choose up to 3 templates to compare side by side"
    )

    if not selected_names:
        st.info("Select templates above to view comparison")
        return

    # Extract template IDs
    selected_ids = []
    for name in selected_names:
        template_id = name.split("(")[-1].rstrip(")")
        selected_ids.append(template_id)

    # Display comparison table
    selected_templates = [template_manager.get_template(tid) for tid in selected_ids]

    comparison_data = []

    for template in selected_templates:
        if template:
            financial = template.preferences.financial
            display = template.preferences.display

            comparison_data.append({
                "Template": template.name,
                "Category": template.category.value.replace("_", " ").title(),
                "Methodology": financial.methodology.value.title(),
                "Discount Rate": f"{financial.default_discount_rate:.1%}",
                "Terminal Growth": f"{financial.default_terminal_growth_rate:.1%}",
                "Projection Years": financial.default_projection_years,
                "Currency": financial.primary_currency.value,
                "Advanced Options": "Yes" if display.show_advanced_options else "No",
                "Popularity": f"{template.popularity_score:.1f}⭐"
            })

    if comparison_data:
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df.set_index("Template"), use_container_width=True)


def display_custom_template_creator() -> None:
    """Display interface for creating custom templates"""

    st.subheader("🛠️ Create Custom Template")

    with st.expander("Create New Template", expanded=False):
        template_id = st.text_input(
            "Template ID",
            placeholder="my_custom_template",
            help="Unique identifier for your template (lowercase, underscores allowed)"
        )

        name = st.text_input(
            "Template Name",
            placeholder="My Investment Strategy",
            help="Display name for your template"
        )

        description = st.text_area(
            "Description",
            placeholder="Describe your template's purpose and settings...",
            help="Detailed description of what this template does"
        )

        category = st.selectbox(
            "Category",
            [cat.value.replace("_", " ").title() for cat in TemplateCategory],
            help="Template category for organization"
        )

        # Basic settings configuration
        st.markdown("**Basic Financial Settings:**")

        col1, col2 = st.columns(2)
        with col1:
            discount_rate = st.number_input("Discount Rate", 0.01, 0.30, 0.10, 0.005, format="%.3f")
            terminal_growth = st.number_input("Terminal Growth Rate", 0.00, 0.10, 0.025, 0.005, format="%.3f")

        with col2:
            projection_years = st.number_input("Projection Years", 1, 15, 5, 1)
            methodology = st.selectbox("Methodology", ["conservative", "moderate", "aggressive", "custom"])

        if st.button("Create Template"):
            if template_id and name and description:
                try:
                    # Create basic preferences with user settings
                    from core.user_preferences.user_profile import (
                        UserPreferences, FinancialPreferences, AnalysisMethodology
                    )

                    financial_prefs = FinancialPreferences(
                        default_discount_rate=discount_rate,
                        default_terminal_growth_rate=terminal_growth,
                        default_projection_years=projection_years,
                        methodology=AnalysisMethodology(methodology)
                    )

                    preferences = UserPreferences(financial=financial_prefs)

                    # Create template
                    template_manager = get_template_manager()
                    category_enum = next(cat for cat in TemplateCategory if cat.value.replace("_", " ").title() == category)

                    template = template_manager.create_custom_template(
                        template_id=template_id,
                        name=name,
                        description=description,
                        preferences=preferences,
                        category=category_enum,
                        author="user"
                    )

                    st.success(f"✅ Created custom template: {name}")

                except Exception as e:
                    st.error(f"Error creating template: {e}")
            else:
                st.warning("Please fill in all required fields")


def display_template_management() -> None:
    """Display template management interface"""

    template_manager = get_template_manager()

    st.subheader("🔧 Template Management")

    # Show user templates
    all_templates = template_manager.list_templates()
    user_templates = [t for t in all_templates if t.author == "user"]

    if user_templates:
        st.markdown("**Your Custom Templates:**")

        for template in user_templates:
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{template.name}** - {template.description[:50]}...")

            with col2:
                st.markdown(f"Used {template.usage_count} times")

            with col3:
                if st.button("Delete", key=f"delete_{template.template_id}"):
                    try:
                        template_manager.delete_template(template.template_id)
                        st.success(f"Deleted template: {template.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting template: {e}")
    else:
        st.info("No custom templates created yet. Use the template creator above to make your own!")


def display_template_search() -> Optional[str]:
    """
    Display template search interface

    Returns:
        Selected template ID or None
    """
    template_manager = get_template_manager()

    st.subheader("🔍 Search Templates")

    search_query = st.text_input(
        "Search templates",
        placeholder="Enter keywords to search templates...",
        help="Search in template names, descriptions, and tags"
    )

    if search_query:
        matching_templates = template_manager.search_templates(search_query)

        if matching_templates:
            st.markdown(f"**Found {len(matching_templates)} matching templates:**")

            selected_template_id = None

            for template in matching_templates:
                with st.expander(f"📋 {template.name}", expanded=False):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Description:** {template.description}")
                        _display_template_preview(template)

                    with col2:
                        if st.button(f"Select", key=f"search_select_{template.template_id}"):
                            selected_template_id = template.template_id

            return selected_template_id
        else:
            st.warning(f"No templates found matching '{search_query}'")

    return None