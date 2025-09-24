# Advanced Theme Customization System

## Overview

The Advanced Theme Customization System extends the financial analysis application with comprehensive theme creation, customization, and management capabilities. This system allows users to create personalized themes with custom color palettes, typography options, branding features, and advanced settings.

## Features

### 🎨 Custom Color Palettes
- **Primary Colors**: Define primary, secondary, and accent colors
- **Semantic Colors**: Success, warning, danger, and info colors
- **Extended Palette**: Background, surface, text, and border colors
- **Gradient Support**: Custom gradient colors with direction control
- **Financial Colors**: Specialized colors for profit/loss indicators
- **Chart Colors**: Extended color palette for data visualizations

### 📝 Typography Customization
- **Font Selection**: Google Fonts integration with popular font families
- **Font Scaling**: Adjust overall font sizes with scale factor
- **Line Height**: Control text line spacing
- **Letter Spacing**: Fine-tune character spacing
- **Weight Options**: Support for multiple font weights

### 🏢 Personalized Branding
- **Logo Integration**: Add custom logos with size control
- **Company Information**: Company name and tagline display
- **Header Customization**: Control logo placement and visibility
- **Footer Options**: Custom footer text and links
- **Favicon Support**: Custom favicon URLs

### 🌙 Auto Theme Switching
- **Time-Based**: Automatic light/dark switching based on time
- **System Preference**: Follow system dark/light mode preference
- **Custom Schedule**: Set specific times for theme changes
- **Location-Based**: Future support for sunset/sunrise switching

### 🌍 Theme Sharing & Community
- **JSON Export/Import**: Share themes via JSON format
- **Theme Gallery**: Browse and organize themes by category
- **Search & Filter**: Find themes by name, tags, or category
- **Community Themes**: Import themes created by others

### 👁️ Real-Time Preview
- **Live Preview**: See changes instantly as you customize
- **Component Showcase**: Preview how themes affect different UI elements
- **Chart Integration**: See themed charts and visualizations
- **Layout Testing**: Test themes with various layout options

## System Architecture

### Core Components

1. **AdvancedThemeManager**: Central theme management and storage
2. **ThemeCustomizationUI**: User interface for theme creation and editing
3. **ThemePreviewSystem**: Real-time preview functionality
4. **ThemeIntegrationManager**: Integration with the main application

### Data Models

```python
@dataclass
class AdvancedTheme:
    metadata: ThemeMetadata
    color_palette: AdvancedColorPalette
    custom_font: Optional[CustomFont]
    branding: BrandingSettings
    auto_switch: AutoSwitchSettings
    # Layout and typography settings...
```

### File Structure

```
ui/streamlit/
├── advanced_theme_customization.py  # Core theme system
├── theme_customization_ui.py        # UI components
├── theme_preview_system.py          # Preview functionality
└── theme_integration.py             # Application integration

data/themes/
├── custom/                          # User-created themes
└── community/                       # Imported community themes

examples/
└── advanced_theme_demo.py          # Demonstration script
```

## Getting Started

### 1. Basic Usage

```python
from ui.streamlit.theme_integration import integrate_theme_system

# Initialize theme system in your Streamlit app
theme_integration = integrate_theme_system()

# Render theme controls in sidebar
theme_integration.render_theme_selector_sidebar()
```

### 2. Creating Your First Theme

1. **Open Theme Designer**: Navigate to User Preferences → UI Theme → Advanced Customization
2. **Choose Starting Point**: Select a preset color scheme or start from scratch
3. **Customize Colors**: Use color pickers to define your palette
4. **Set Typography**: Choose fonts and scaling options
5. **Add Branding**: Include logos and company information
6. **Preview & Save**: Use live preview and save your theme

### 3. Applying Themes

```python
# Apply an advanced theme
theme_integration.apply_advanced_theme(your_theme)

# Get current theme information
theme_info = theme_integration.get_current_theme_info()
```

## Theme Creation Guide

### Color Palette Design

1. **Start with Primary Color**: Choose your main brand color
2. **Define Secondary**: Complementary color for accents
3. **Add Semantic Colors**: Success (green), warning (yellow), danger (red)
4. **Set Background Colors**: Light/dark backgrounds and surfaces
5. **Configure Text Colors**: Primary and secondary text colors
6. **Create Gradients**: Define gradient start, end, and direction

### Typography Selection

1. **Choose Font Family**: Select from Google Fonts or system fonts
2. **Set Base Scale**: Adjust overall font size scaling
3. **Configure Line Height**: Set comfortable reading spacing
4. **Fine-tune Spacing**: Adjust letter spacing if needed

### Branding Integration

1. **Logo Setup**: Provide logo URL and size preferences
2. **Company Info**: Add company name and tagline
3. **Header Layout**: Choose logo placement (left, center, right)
4. **Footer Content**: Optional footer text and links

### Auto-Switching Configuration

1. **Choose Mode**: Time-based, system preference, or disabled
2. **Set Schedule**: Define light and dark theme start times
3. **Test Switching**: Verify automatic theme changes work correctly

## Advanced Features

### Component Overrides

Custom CSS overrides for specific components:

```python
component_overrides = {
    ".stMetric": {
        "background_color": "#f0f0f0",
        "border_radius": "12px",
        "box_shadow": "0 4px 8px rgba(0,0,0,0.1)"
    }
}
```

### Custom CSS Integration

Themes generate comprehensive CSS that includes:
- CSS custom properties for all colors
- Responsive typography scaling
- Component-specific styling
- Accessibility enhancements
- Animation and transition controls

### Performance Optimization

- **Theme Caching**: Themes are cached for fast loading
- **CSS Optimization**: Minimized CSS generation
- **Lazy Loading**: Preview components load on demand
- **Memory Management**: Efficient theme storage and retrieval

## API Reference

### AdvancedThemeManager

```python
class AdvancedThemeManager:
    def save_theme(self, theme: AdvancedTheme, is_community: bool = False)
    def delete_theme(self, theme_name: str, is_community: bool = False)
    def get_all_themes(self) -> Dict[str, AdvancedTheme]
    def search_themes(self, query: str) -> Dict[str, AdvancedTheme]
    def duplicate_theme(self, source_name: str, new_name: str) -> AdvancedTheme
    def export_theme(self, theme_name: str) -> str
    def import_theme(self, theme_json: str, is_community: bool = False) -> AdvancedTheme
```

### Theme Data Structures

```python
@dataclass
class ThemeMetadata:
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    category: str = "custom"

@dataclass
class AdvancedColorPalette(ColorPalette):
    gradient_start: str = ""
    gradient_end: str = ""
    gradient_direction: str = "135deg"
    # Extended color properties...

@dataclass
class CustomFont:
    name: str
    family: str
    weights: List[str] = field(default_factory=lambda: ["400", "500", "600", "700"])
    provider: FontProvider = FontProvider.GOOGLE_FONTS
```

## Integration Examples

### Basic Integration

```python
import streamlit as st
from ui.streamlit.theme_integration import integrate_theme_system, render_theme_sidebar

# In your main app
def main():
    st.set_page_config(page_title="Financial Analysis", layout="wide")

    # Initialize theme system
    integrate_theme_system()

    # Render theme controls in sidebar
    render_theme_sidebar()

    # Your app content
    st.title("Financial Analysis Dashboard")
    # ... rest of your app
```

### Custom Theme Application

```python
from ui.streamlit.advanced_theme_customization import AdvancedTheme, AdvancedColorPalette

# Create a custom theme programmatically
custom_colors = AdvancedColorPalette(
    primary="#1E40AF",
    secondary="#3B82F6",
    background="#FFFFFF",
    # ... other colors
)

# Apply the theme
theme_integration._apply_advanced_theme(custom_theme)
```

### Theme Export/Import

```python
# Export a theme
theme_json = manager.export_theme("My Custom Theme")

# Save to file
with open("my_theme.json", "w") as f:
    f.write(theme_json)

# Import a theme
with open("shared_theme.json", "r") as f:
    imported_theme = manager.import_theme(f.read())
```

## Best Practices

### Design Guidelines

1. **Consistency**: Maintain consistent color relationships across themes
2. **Accessibility**: Ensure sufficient contrast ratios for text readability
3. **Brand Alignment**: Align themes with your organization's brand guidelines
4. **User Testing**: Test themes with actual users and use cases

### Performance Tips

1. **Optimize Images**: Use optimized logos and images
2. **Limit Overrides**: Minimize custom CSS overrides for better performance
3. **Cache Themes**: Leverage built-in caching for frequently used themes
4. **Monitor Memory**: Clean up unused themes from session state

### Theme Organization

1. **Naming Convention**: Use descriptive, consistent theme names
2. **Categorization**: Organize themes by purpose (professional, creative, etc.)
3. **Version Control**: Track theme versions and changes
4. **Documentation**: Document custom themes and their intended use

## Troubleshooting

### Common Issues

**Theme Not Applying**
- Check if theme exists in the themes directory
- Verify theme JSON format is valid
- Ensure proper permissions for file access

**CSS Conflicts**
- Check for conflicting CSS rules
- Verify CSS custom properties are properly defined
- Clear browser cache and refresh

**Performance Issues**
- Reduce number of active themes
- Optimize image sizes and formats
- Clear theme cache if needed

**Import/Export Problems**
- Validate JSON format before importing
- Check file permissions and paths
- Ensure all required theme properties are present

### Debug Mode

Enable debug logging for theme operations:

```python
import logging
logging.getLogger('ui.streamlit.advanced_theme_customization').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Theme Templates**: Pre-built theme templates for common use cases
2. **Color Accessibility Tools**: Built-in contrast checking and suggestions
3. **Animation Controls**: Custom animation and transition settings
4. **Theme Versioning**: Git-like versioning for theme changes
5. **Collaborative Editing**: Multiple users editing themes simultaneously
6. **AI-Powered Suggestions**: AI recommendations for color combinations
7. **Mobile Optimization**: Mobile-specific theme variations
8. **Integration APIs**: REST APIs for external theme management

### Community Features

1. **Theme Marketplace**: Browse and download community themes
2. **Rating System**: Rate and review themes
3. **Theme Contests**: Community theme creation competitions
4. **Contributor Recognition**: Highlight theme creators and contributors

## Contributing

To contribute to the advanced theme system:

1. **Fork the Repository**: Create your own fork for development
2. **Create Feature Branch**: Work on features in dedicated branches
3. **Follow Standards**: Adhere to existing code style and conventions
4. **Add Tests**: Include tests for new functionality
5. **Update Documentation**: Keep documentation current with changes
6. **Submit Pull Request**: Submit PRs with clear descriptions

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ui/test_advanced_themes.py

# Run demo
streamlit run examples/advanced_theme_demo.py
```

## Support

For support with the advanced theme system:

1. **Check Documentation**: Review this guide and API reference
2. **Search Issues**: Look for existing issues in the repository
3. **Create Issue**: Submit detailed issue reports with reproduction steps
4. **Community Forum**: Engage with the community for help and tips

## License

The Advanced Theme Customization System is part of the financial analysis application and follows the same license terms. See the main project LICENSE file for details.

---

*This documentation covers the comprehensive Advanced Theme Customization System. For basic theme usage, see the standard theme documentation.*