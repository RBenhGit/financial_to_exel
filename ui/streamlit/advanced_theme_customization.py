"""
Advanced Theme Customization System
===================================

Extended theme system with custom color palettes, typography options,
personalized branding features, and community theme sharing.
"""

import streamlit as st
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import colorsys
import hashlib
import urllib.parse

from .dashboard_themes import ThemeManager, DashboardTheme, ColorPalette, ThemeMode
from core.user_preferences.ui_preferences import UIPreferences, ThemePreferences

logger = logging.getLogger(__name__)


class FontProvider(Enum):
    """Available font providers"""
    GOOGLE_FONTS = "google"
    SYSTEM_FONTS = "system"
    CUSTOM_FONTS = "custom"


class AutoSwitchMode(Enum):
    """Auto-switching modes for theme"""
    DISABLED = "disabled"
    TIME_BASED = "time_based"
    SYSTEM_PREFERENCE = "system_preference"
    AMBIENT_LIGHT = "ambient_light"  # Future feature


@dataclass
class CustomFont:
    """Custom font definition"""
    name: str
    family: str
    weights: List[str] = field(default_factory=lambda: ["400", "500", "600", "700"])
    provider: FontProvider = FontProvider.GOOGLE_FONTS
    url: Optional[str] = None

    def get_font_url(self) -> str:
        """Generate font URL for import"""
        if self.provider == FontProvider.GOOGLE_FONTS:
            weights_str = ":wght@" + ";".join(self.weights)
            return f"https://fonts.googleapis.com/css2?family={urllib.parse.quote(self.family)}{weights_str}&display=swap"
        elif self.url:
            return self.url
        return ""


@dataclass
class BrandingSettings:
    """Custom branding configuration"""
    logo_url: Optional[str] = None
    logo_width: int = 200
    company_name: str = ""
    tagline: str = ""
    favicon_url: Optional[str] = None

    # Header customization
    show_logo_in_header: bool = True
    show_company_name: bool = True
    header_layout: str = "logo_left"  # logo_left, logo_center, logo_right

    # Footer customization
    show_footer: bool = False
    footer_text: str = ""
    footer_links: Dict[str, str] = field(default_factory=dict)


@dataclass
class AutoSwitchSettings:
    """Auto theme switching configuration"""
    mode: AutoSwitchMode = AutoSwitchMode.DISABLED
    light_theme_start: str = "06:00"  # HH:MM format
    dark_theme_start: str = "18:00"   # HH:MM format
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None


@dataclass
class ThemeMetadata:
    """Theme metadata for sharing and organization"""
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_date: str = field(default_factory=lambda: datetime.now().isoformat())
    popularity_score: int = 0
    category: str = "custom"  # custom, professional, creative, accessibility


@dataclass
class AdvancedColorPalette(ColorPalette):
    """Extended color palette with additional customization"""
    # Gradient colors
    gradient_start: str = ""
    gradient_end: str = ""
    gradient_direction: str = "135deg"  # CSS gradient direction

    # Additional semantic colors
    link: str = "#0066CC"
    visited_link: str = "#663399"
    focus: str = "#005FCC"
    selection: str = "#B3D4FC"

    # Component-specific colors
    sidebar_bg: str = ""
    header_bg: str = ""
    footer_bg: str = ""
    card_shadow: str = "rgba(0, 0, 0, 0.1)"

    # Data visualization colors (extended palette)
    chart_colors_extended: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        # Auto-generate derived colors if not provided
        if not self.gradient_start:
            self.gradient_start = self.primary
        if not self.gradient_end:
            self.gradient_end = self.secondary
        if not self.sidebar_bg:
            self.sidebar_bg = self.surface
        if not self.header_bg:
            self.header_bg = self.primary
        if not self.footer_bg:
            self.footer_bg = self.surface

        # Generate extended chart colors
        if not self.chart_colors_extended:
            self.chart_colors_extended = self._generate_extended_palette()

    def _generate_extended_palette(self) -> List[str]:
        """Generate an extended color palette for complex visualizations"""
        base_colors = [
            self.primary, self.secondary, self.accent,
            self.success, self.warning, self.danger, self.info
        ]

        extended = base_colors.copy()

        # Generate tints and shades for each base color
        for color in base_colors:
            if color.startswith('#'):
                # Convert to RGB
                rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

                # Generate lighter variant
                light_rgb = colorsys.hsv_to_rgb(h, s * 0.7, min(v * 1.2, 1.0))
                light_hex = '#{:02x}{:02x}{:02x}'.format(
                    int(light_rgb[0] * 255),
                    int(light_rgb[1] * 255),
                    int(light_rgb[2] * 255)
                )
                extended.append(light_hex)

                # Generate darker variant
                dark_rgb = colorsys.hsv_to_rgb(h, min(s * 1.2, 1.0), v * 0.8)
                dark_hex = '#{:02x}{:02x}{:02x}'.format(
                    int(dark_rgb[0] * 255),
                    int(dark_rgb[1] * 255),
                    int(dark_rgb[2] * 255)
                )
                extended.append(dark_hex)

        return extended

    def get_gradient_css(self) -> str:
        """Generate CSS gradient string"""
        return f"linear-gradient({self.gradient_direction}, {self.gradient_start}, {self.gradient_end})"


@dataclass
class AdvancedTheme:
    """Advanced theme with extended customization options"""
    metadata: ThemeMetadata
    color_palette: AdvancedColorPalette
    custom_font: Optional[CustomFont] = None
    branding: BrandingSettings = field(default_factory=BrandingSettings)
    auto_switch: AutoSwitchSettings = field(default_factory=AutoSwitchSettings)

    # Advanced typography
    font_scale: float = 1.0  # Scale factor for all font sizes
    line_height: float = 1.5
    letter_spacing: float = 0.0

    # Layout customization
    border_radius_scale: float = 1.0
    shadow_intensity: float = 1.0
    spacing_scale: float = 1.0

    # Component customization
    component_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dashboard_theme(self) -> DashboardTheme:
        """Convert to standard DashboardTheme for compatibility"""
        font_family = self.custom_font.family if self.custom_font else "Inter, sans-serif"

        # Scale font sizes
        base_sizes = {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem"
        }

        scaled_sizes = {}
        for size, value in base_sizes.items():
            numeric_value = float(value.replace('rem', ''))
            scaled_value = numeric_value * self.font_scale
            scaled_sizes[size] = f"{scaled_value}rem"

        return DashboardTheme(
            name=self.metadata.name,
            mode=ThemeMode.LIGHT,  # Will be overridden by theme manager
            color_palette=self.color_palette,
            font_family=font_family,
            font_sizes=scaled_sizes,
            border_radius=f"{8 * self.border_radius_scale}px"
        )


class AdvancedThemeManager:
    """Enhanced theme manager with advanced customization features"""

    def __init__(self, themes_dir: str = "data/themes"):
        self.themes_dir = themes_dir
        self.custom_themes: Dict[str, AdvancedTheme] = {}
        self.community_themes: Dict[str, AdvancedTheme] = {}
        self._ensure_themes_directory()
        self._load_themes()

    def _ensure_themes_directory(self):
        """Ensure themes directory exists"""
        os.makedirs(self.themes_dir, exist_ok=True)
        os.makedirs(os.path.join(self.themes_dir, "custom"), exist_ok=True)
        os.makedirs(os.path.join(self.themes_dir, "community"), exist_ok=True)

    def _load_themes(self):
        """Load custom and community themes from disk"""
        try:
            # Load custom themes
            custom_dir = os.path.join(self.themes_dir, "custom")
            for filename in os.listdir(custom_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(custom_dir, filename)
                    theme = self._load_theme_from_file(theme_path)
                    if theme:
                        self.custom_themes[theme.metadata.name] = theme

            # Load community themes
            community_dir = os.path.join(self.themes_dir, "community")
            for filename in os.listdir(community_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(community_dir, filename)
                    theme = self._load_theme_from_file(theme_path)
                    if theme:
                        self.community_themes[theme.metadata.name] = theme

        except Exception as e:
            logger.error(f"Error loading themes: {e}")

    def _load_theme_from_file(self, filepath: str) -> Optional[AdvancedTheme]:
        """Load theme from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Convert dict back to dataclass
            metadata = ThemeMetadata(**data['metadata'])
            color_palette = AdvancedColorPalette(**data['color_palette'])

            custom_font = None
            if data.get('custom_font'):
                custom_font = CustomFont(**data['custom_font'])

            branding = BrandingSettings(**data.get('branding', {}))
            auto_switch = AutoSwitchSettings(**data.get('auto_switch', {}))

            theme = AdvancedTheme(
                metadata=metadata,
                color_palette=color_palette,
                custom_font=custom_font,
                branding=branding,
                auto_switch=auto_switch,
                font_scale=data.get('font_scale', 1.0),
                line_height=data.get('line_height', 1.5),
                letter_spacing=data.get('letter_spacing', 0.0),
                border_radius_scale=data.get('border_radius_scale', 1.0),
                shadow_intensity=data.get('shadow_intensity', 1.0),
                spacing_scale=data.get('spacing_scale', 1.0),
                component_overrides=data.get('component_overrides', {})
            )

            return theme

        except Exception as e:
            logger.error(f"Error loading theme from {filepath}: {e}")
            return None

    def save_theme(self, theme: AdvancedTheme, is_community: bool = False):
        """Save theme to disk"""
        try:
            # Convert theme to dict
            theme_dict = {
                'metadata': asdict(theme.metadata),
                'color_palette': asdict(theme.color_palette),
                'custom_font': asdict(theme.custom_font) if theme.custom_font else None,
                'branding': asdict(theme.branding),
                'auto_switch': asdict(theme.auto_switch),
                'font_scale': theme.font_scale,
                'line_height': theme.line_height,
                'letter_spacing': theme.letter_spacing,
                'border_radius_scale': theme.border_radius_scale,
                'shadow_intensity': theme.shadow_intensity,
                'spacing_scale': theme.spacing_scale,
                'component_overrides': theme.component_overrides
            }

            # Generate filename
            safe_name = "".join(c for c in theme.metadata.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            filename = f"{safe_name}.json"

            # Determine directory
            if is_community:
                filepath = os.path.join(self.themes_dir, "community", filename)
                self.community_themes[theme.metadata.name] = theme
            else:
                filepath = os.path.join(self.themes_dir, "custom", filename)
                self.custom_themes[theme.metadata.name] = theme

            # Save to file
            with open(filepath, 'w') as f:
                json.dump(theme_dict, f, indent=2)

            logger.info(f"Saved theme '{theme.metadata.name}' to {filepath}")

        except Exception as e:
            logger.error(f"Error saving theme: {e}")
            raise

    def delete_theme(self, theme_name: str, is_community: bool = False):
        """Delete a custom or community theme"""
        try:
            # Remove from memory
            if is_community and theme_name in self.community_themes:
                del self.community_themes[theme_name]
            elif theme_name in self.custom_themes:
                del self.custom_themes[theme_name]

            # Remove file
            safe_name = "".join(c for c in theme_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            filename = f"{safe_name}.json"

            directory = "community" if is_community else "custom"
            filepath = os.path.join(self.themes_dir, directory, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted theme file: {filepath}")

        except Exception as e:
            logger.error(f"Error deleting theme: {e}")
            raise

    def get_all_themes(self) -> Dict[str, AdvancedTheme]:
        """Get all available themes"""
        all_themes = {}
        all_themes.update(self.custom_themes)
        all_themes.update(self.community_themes)
        return all_themes

    def get_theme_by_category(self, category: str) -> Dict[str, AdvancedTheme]:
        """Get themes by category"""
        all_themes = self.get_all_themes()
        return {name: theme for name, theme in all_themes.items()
                if theme.metadata.category == category}

    def search_themes(self, query: str) -> Dict[str, AdvancedTheme]:
        """Search themes by name, description, or tags"""
        query_lower = query.lower()
        all_themes = self.get_all_themes()

        matching_themes = {}
        for name, theme in all_themes.items():
            if (query_lower in theme.metadata.name.lower() or
                query_lower in theme.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in theme.metadata.tags)):
                matching_themes[name] = theme

        return matching_themes

    def duplicate_theme(self, source_theme_name: str, new_name: str) -> AdvancedTheme:
        """Create a copy of an existing theme"""
        all_themes = self.get_all_themes()
        if source_theme_name not in all_themes:
            raise ValueError(f"Source theme '{source_theme_name}' not found")

        source_theme = all_themes[source_theme_name]

        # Create new metadata
        new_metadata = ThemeMetadata(
            name=new_name,
            description=f"Copy of {source_theme.metadata.name}",
            author=source_theme.metadata.author,
            version="1.0.0",
            tags=source_theme.metadata.tags.copy(),
            category=source_theme.metadata.category
        )

        # Create new theme with same properties
        new_theme = AdvancedTheme(
            metadata=new_metadata,
            color_palette=AdvancedColorPalette(**asdict(source_theme.color_palette)),
            custom_font=CustomFont(**asdict(source_theme.custom_font)) if source_theme.custom_font else None,
            branding=BrandingSettings(**asdict(source_theme.branding)),
            auto_switch=AutoSwitchSettings(**asdict(source_theme.auto_switch)),
            font_scale=source_theme.font_scale,
            line_height=source_theme.line_height,
            letter_spacing=source_theme.letter_spacing,
            border_radius_scale=source_theme.border_radius_scale,
            shadow_intensity=source_theme.shadow_intensity,
            spacing_scale=source_theme.spacing_scale,
            component_overrides=source_theme.component_overrides.copy()
        )

        return new_theme

    def export_theme(self, theme_name: str) -> str:
        """Export theme as JSON string for sharing"""
        all_themes = self.get_all_themes()
        if theme_name not in all_themes:
            raise ValueError(f"Theme '{theme_name}' not found")

        theme = all_themes[theme_name]
        theme_dict = {
            'metadata': asdict(theme.metadata),
            'color_palette': asdict(theme.color_palette),
            'custom_font': asdict(theme.custom_font) if theme.custom_font else None,
            'branding': asdict(theme.branding),
            'auto_switch': asdict(theme.auto_switch),
            'font_scale': theme.font_scale,
            'line_height': theme.line_height,
            'letter_spacing': theme.letter_spacing,
            'border_radius_scale': theme.border_radius_scale,
            'shadow_intensity': theme.shadow_intensity,
            'spacing_scale': theme.spacing_scale,
            'component_overrides': theme.component_overrides
        }

        return json.dumps(theme_dict, indent=2)

    def import_theme(self, theme_json: str, is_community: bool = False) -> AdvancedTheme:
        """Import theme from JSON string"""
        try:
            data = json.loads(theme_json)

            metadata = ThemeMetadata(**data['metadata'])
            color_palette = AdvancedColorPalette(**data['color_palette'])

            custom_font = None
            if data.get('custom_font'):
                custom_font = CustomFont(**data['custom_font'])

            branding = BrandingSettings(**data.get('branding', {}))
            auto_switch = AutoSwitchSettings(**data.get('auto_switch', {}))

            theme = AdvancedTheme(
                metadata=metadata,
                color_palette=color_palette,
                custom_font=custom_font,
                branding=branding,
                auto_switch=auto_switch,
                font_scale=data.get('font_scale', 1.0),
                line_height=data.get('line_height', 1.5),
                letter_spacing=data.get('letter_spacing', 0.0),
                border_radius_scale=data.get('border_radius_scale', 1.0),
                shadow_intensity=data.get('shadow_intensity', 1.0),
                spacing_scale=data.get('spacing_scale', 1.0),
                component_overrides=data.get('component_overrides', {})
            )

            # Save the imported theme
            self.save_theme(theme, is_community)

            return theme

        except Exception as e:
            logger.error(f"Error importing theme: {e}")
            raise

    def should_auto_switch(self, theme: AdvancedTheme) -> Optional[ThemeMode]:
        """Check if theme should auto-switch and return target mode"""
        if theme.auto_switch.mode == AutoSwitchMode.DISABLED:
            return None

        if theme.auto_switch.mode == AutoSwitchMode.TIME_BASED:
            current_time = datetime.now().time()

            try:
                light_start = datetime.strptime(theme.auto_switch.light_theme_start, "%H:%M").time()
                dark_start = datetime.strptime(theme.auto_switch.dark_theme_start, "%H:%M").time()

                if light_start <= current_time < dark_start:
                    return ThemeMode.LIGHT
                else:
                    return ThemeMode.DARK

            except ValueError:
                logger.warning("Invalid time format in auto-switch settings")
                return None

        elif theme.auto_switch.mode == AutoSwitchMode.SYSTEM_PREFERENCE:
            # This would require JavaScript integration to detect system preference
            # For now, default to light mode
            return ThemeMode.LIGHT

        return None


def create_default_themes() -> Dict[str, AdvancedTheme]:
    """Create a set of default advanced themes"""
    themes = {}

    # Professional Corporate Theme
    professional_metadata = ThemeMetadata(
        name="Professional Corporate",
        description="Clean, corporate-friendly theme with professional color palette",
        author="System",
        category="professional",
        tags=["corporate", "professional", "blue", "clean"]
    )

    professional_colors = AdvancedColorPalette(
        primary="#1E40AF",
        secondary="#3B82F6",
        accent="#8B5CF6",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        info="#06B6D4",
        background="#FFFFFF",
        surface="#F9FAFB",
        text_primary="#111827",
        text_secondary="#6B7280",
        border="#E5E7EB",
        hover="#F3F4F6",
        disabled="#D1D5DB",
        gradient_start="#1E40AF",
        gradient_end="#3B82F6"
    )

    themes["Professional Corporate"] = AdvancedTheme(
        metadata=professional_metadata,
        color_palette=professional_colors,
        custom_font=CustomFont(
            name="Inter",
            family="Inter",
            provider=FontProvider.GOOGLE_FONTS
        )
    )

    # Dark Professional Theme
    dark_professional_metadata = ThemeMetadata(
        name="Dark Professional",
        description="Professional dark theme optimized for extended use",
        author="System",
        category="professional",
        tags=["dark", "professional", "eye-friendly"]
    )

    dark_professional_colors = AdvancedColorPalette(
        primary="#3B82F6",
        secondary="#60A5FA",
        accent="#A78BFA",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        info="#06B6D4",
        background="#0F172A",
        surface="#1E293B",
        text_primary="#F1F5F9",
        text_secondary="#CBD5E1",
        border="#334155",
        hover="#334155",
        disabled="#475569",
        gradient_start="#1E293B",
        gradient_end="#334155"
    )

    themes["Dark Professional"] = AdvancedTheme(
        metadata=dark_professional_metadata,
        color_palette=dark_professional_colors,
        custom_font=CustomFont(
            name="Inter",
            family="Inter",
            provider=FontProvider.GOOGLE_FONTS
        )
    )

    # Creative Vibrant Theme
    creative_metadata = ThemeMetadata(
        name="Creative Vibrant",
        description="Colorful, energetic theme for creative professionals",
        author="System",
        category="creative",
        tags=["colorful", "creative", "vibrant", "energy"]
    )

    creative_colors = AdvancedColorPalette(
        primary="#7C3AED",
        secondary="#F59E0B",
        accent="#EF4444",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        info="#06B6D4",
        background="#FFFFFF",
        surface="#FEFCE8",
        text_primary="#1F2937",
        text_secondary="#6B7280",
        border="#FDE047",
        hover="#FEF3C7",
        disabled="#D1D5DB",
        gradient_start="#7C3AED",
        gradient_end="#F59E0B",
        gradient_direction="45deg"
    )

    themes["Creative Vibrant"] = AdvancedTheme(
        metadata=creative_metadata,
        color_palette=creative_colors,
        custom_font=CustomFont(
            name="Poppins",
            family="Poppins",
            provider=FontProvider.GOOGLE_FONTS
        ),
        font_scale=1.1,
        border_radius_scale=1.5
    )

    return themes


if __name__ == "__main__":
    # Demo usage
    print("Advanced Theme Customization System")

    # Create theme manager
    manager = AdvancedThemeManager()

    # Create and save default themes
    default_themes = create_default_themes()
    for theme in default_themes.values():
        manager.save_theme(theme)

    print(f"Created {len(default_themes)} default themes")
    print("Available themes:", list(manager.get_all_themes().keys()))