# Windows Unicode Support

This document describes the Unicode encoding fixes implemented to ensure the Financial Analysis application works smoothly in Windows environments.

## Overview

The application has been enhanced with comprehensive Unicode support to handle international characters, symbols, and various encodings properly on Windows systems.

## Key Features

### 1. Automatic Windows Configuration
- **Console Setup**: Automatically configures Windows console for UTF-8 support
- **Environment Variables**: Sets `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`
- **Code Page**: Changes console code page to UTF-8 (65001) when possible

### 2. File Operations
- **JSON Files**: All JSON operations use UTF-8 encoding with `ensure_ascii=False`
- **CSV Files**: Uses UTF-8-BOM (`utf-8-sig`) for Excel compatibility
- **Text Files**: Explicit UTF-8 encoding for all text file operations
- **Configuration Files**: YAML and JSON configs use UTF-8 encoding

### 3. Pandas Integration
- **Display Options**: Configured for proper Unicode character display
- **CSV Export**: Automatic encoding selection for Windows compatibility
- **DataFrame Operations**: Full Unicode support for all string operations

## Files Modified

### Core Modules
1. **`registry_config_loader.py`**: Fixed YAML file encoding
2. **`field_normalizer.py`**: Fixed JSON file encoding
3. **`core/validation/validation_registry.py`**: Fixed config file encoding
4. **`watch_list_manager.py`**: Fixed JSON and CSV encoding
5. **`fcf_analysis_streamlit.py`**: Fixed CSV export encoding

### New Utilities
1. **`utils/encoding_utils.py`**: Comprehensive encoding utilities
2. **`run_streamlit_windows.py`**: Windows-optimized launcher
3. **`run_app_windows.bat`**: Windows batch launcher
4. **`test_windows_unicode.py`**: Unicode compatibility test suite

## Usage

### Option 1: Batch File (Recommended)
```bash
run_app_windows.bat
```

### Option 2: Python Launcher
```bash
python run_streamlit_windows.py
```

### Option 3: Direct Launch
```bash
python fcf_analysis_streamlit.py
```

## Encoding Standards

### File Types
- **CSV Files**: `utf-8-sig` (UTF-8 with BOM for Excel)
- **JSON Files**: `utf-8` with `ensure_ascii=False`
- **Text Files**: `utf-8`
- **Configuration**: `utf-8`

### Best Practices
```python
# Use the encoding utilities
from utils.encoding_utils import safe_csv_export, safe_json_dump

# CSV export
safe_csv_export(dataframe, "output.csv")

# JSON operations
safe_json_dump(data, "config.json")
```

## Testing

Run the Unicode compatibility test:
```bash
python test_windows_unicode.py
```

The test validates:
- Unicode string handling
- File operations with Unicode content
- Pandas operations with international characters
- System-level compatibility

## Troubleshooting

### Common Issues

1. **Characters appear as '?'**
   - Ensure you're using the Windows launchers
   - Check console code page: `chcp 65001`

2. **CSV files show encoding issues in Excel**
   - Files now use UTF-8-BOM for Excel compatibility
   - Use the provided export functions

3. **JSON files with special characters**
   - All JSON operations now use UTF-8 with Unicode preservation

### Environment Setup
```bash
# Set these environment variables if needed
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
```

## Supported Character Sets

The application now properly handles:
- **Latin Extended**: Café, résumé, naïve
- **Currency Symbols**: €, £, ¥, $
- **Mathematical**: α, β, γ, π, ≈
- **Asian Characters**: 日本語, 中文, 한국어
- **Special Symbols**: →, ←, ★, ♦, ✓, ✗
- **Emojis**: 📈, 💰, 📊, 💼, 🚀

## Implementation Details

### Automatic Setup
The main application automatically:
1. Detects Windows environment
2. Configures console encoding
3. Sets pandas display options
4. Applies UTF-8 environment variables

### File Operations
```python
# Example of safe file operations
with safe_open_file("data.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Company", "Value"])
    writer.writerow(["Café Corp", "€100"])
```

### Error Handling
All encoding operations include proper error handling:
- Graceful fallback for unsupported systems
- Clear error messages for encoding issues
- Validation of Unicode support

## Future Enhancements

Planned improvements:
1. **Automatic encoding detection** for input files
2. **Multi-language UI support** using i18n
3. **Enhanced error reporting** for encoding issues
4. **Configuration-based encoding** preferences

---

*This Unicode support ensures the Financial Analysis application works reliably with international data and company names across different Windows configurations.*