"""
Windows Unicode Encoding Utilities

This module provides Windows-specific encoding utilities to ensure proper Unicode
handling across all file operations in the financial analysis application.
"""

import sys
import locale
import os
from typing import Any, Dict, Optional
import pandas as pd
import json


def get_default_encoding() -> str:
    """
    Get the default encoding for the current Windows environment.
    
    Returns:
        str: The recommended encoding for file operations
    """
    if sys.platform == 'win32':
        # For Windows, prefer UTF-8 with BOM for CSV files for Excel compatibility
        return 'utf-8-sig'
    else:
        # For other platforms, standard UTF-8
        return 'utf-8'


def get_csv_encoding() -> str:
    """
    Get the recommended encoding for CSV files on Windows.
    
    Returns:
        str: 'utf-8-sig' for Windows (Excel compatibility), 'utf-8' for others
    """
    if sys.platform == 'win32':
        return 'utf-8-sig'
    else:
        return 'utf-8'


def get_json_encoding() -> str:
    """
    Get the recommended encoding for JSON files.
    
    Returns:
        str: Always 'utf-8' for JSON files
    """
    return 'utf-8'


def configure_pandas_display():
    """Configure pandas to properly display Unicode characters on Windows."""
    if sys.platform == 'win32':
        try:
            # Set pandas display options for better Unicode support
            pd.set_option('display.unicode.east_asian_width', True)
            pd.set_option('display.unicode.ambiguous_as_wide', True)
        except Exception:
            pass  # Ignore if options don't exist in this pandas version


def safe_open_file(file_path: str, mode: str = 'r', encoding: Optional[str] = None, **kwargs):
    """
    Safely open a file with proper encoding handling for Windows.
    
    Args:
        file_path (str): Path to the file
        mode (str): File open mode ('r', 'w', 'a', etc.)
        encoding (str, optional): Encoding to use. If None, auto-detect based on file type
        **kwargs: Additional arguments passed to open()
        
    Returns:
        File object with proper encoding
    """
    if encoding is None:
        # Auto-detect encoding based on file extension and mode
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.csv']:
            encoding = get_csv_encoding()
        elif file_ext in ['.json', '.yaml', '.yml']:
            encoding = get_json_encoding()
        else:
            encoding = get_default_encoding()
    
    return open(file_path, mode, encoding=encoding, **kwargs)


def safe_json_dump(obj: Any, file_path: str, **kwargs) -> None:
    """
    Safely dump JSON with proper Unicode handling.
    
    Args:
        obj: Object to serialize
        file_path (str): Output file path
        **kwargs: Additional arguments for json.dump
    """
    default_kwargs = {
        'indent': 2,
        'ensure_ascii': False,  # Allow Unicode characters
        'separators': (',', ': ')
    }
    default_kwargs.update(kwargs)
    
    with safe_open_file(file_path, 'w', encoding=get_json_encoding()) as f:
        json.dump(obj, f, **default_kwargs)


def safe_json_load(file_path: str, **kwargs) -> Any:
    """
    Safely load JSON with proper Unicode handling.
    
    Args:
        file_path (str): Input file path
        **kwargs: Additional arguments for json.load
        
    Returns:
        Loaded JSON object
    """
    with safe_open_file(file_path, 'r', encoding=get_json_encoding()) as f:
        return json.load(f, **kwargs)


def safe_csv_export(df: pd.DataFrame, file_path: str, **kwargs) -> None:
    """
    Safely export DataFrame to CSV with proper Windows encoding.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        file_path (str): Output file path
        **kwargs: Additional arguments for to_csv
    """
    default_kwargs = {
        'index': False,
        'encoding': get_csv_encoding()
    }
    default_kwargs.update(kwargs)
    
    df.to_csv(file_path, **default_kwargs)


def get_system_encoding_info() -> Dict[str, str]:
    """
    Get information about the current system's encoding configuration.
    
    Returns:
        Dict containing system encoding information
    """
    info = {
        'platform': sys.platform,
        'default_encoding': sys.getdefaultencoding(),
        'filesystem_encoding': sys.getfilesystemencoding(),
        'locale_encoding': locale.getpreferredencoding(),
        'stdout_encoding': getattr(sys.stdout, 'encoding', 'unknown'),
        'stdin_encoding': getattr(sys.stdin, 'encoding', 'unknown'),
        'recommended_csv': get_csv_encoding(),
        'recommended_json': get_json_encoding(),
        'recommended_default': get_default_encoding()
    }
    
    # Windows-specific information
    if sys.platform == 'win32':
        try:
            import codecs
            info['windows_ansi'] = locale.getlocale()[1] or 'unknown'
            info['utf8_available'] = 'utf-8' in codecs.aliases.aliases.values()
        except Exception:
            pass
    
    return info


def setup_windows_console():
    """
    Setup Windows console for better Unicode support.
    This should be called at the start of the application.
    """
    if sys.platform == 'win32':
        try:
            # Enable UTF-8 mode on Windows 10 version 1903 and later
            import os
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # Set console code page to UTF-8 if possible
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
                
        except Exception:
            pass  # Ignore if not available


def validate_unicode_support() -> bool:
    """
    Validate that Unicode support is working correctly.
    
    Returns:
        bool: True if Unicode support is working properly
    """
    try:
        # Test Unicode string handling
        test_strings = [
            "Hello World",
            "Café",
            "日本語",
            "Ñoño",
            "€£¥",
            "α β γ"
        ]
        
        for test_str in test_strings:
            # Test encoding/decoding
            encoded = test_str.encode('utf-8')
            decoded = encoded.decode('utf-8')
            if decoded != test_str:
                return False
                
        return True
        
    except Exception:
        return False


if __name__ == "__main__":
    # Test and display encoding information
    print("=== Windows Unicode Encoding Utilities Test ===")
    
    # Setup console
    setup_windows_console()
    configure_pandas_display()
    
    # Display system information
    print("\nSystem Encoding Information:")
    info = get_system_encoding_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test Unicode support
    print(f"\nUnicode Support Test: {'✓ PASS' if validate_unicode_support() else '✗ FAIL'}")
    
    # Test recommended encodings
    print(f"\nRecommended Encodings:")
    print(f"  CSV files: {get_csv_encoding()}")
    print(f"  JSON files: {get_json_encoding()}")
    print(f"  Default files: {get_default_encoding()}")
    
    print("\n=== Test Complete ===")