"""
Windows Unicode Support Utilities
==================================

Provides Windows-compatible alternatives for Unicode characters in test output.
Addresses Unicode encoding issues found in edge case tests on Windows systems.

This module ensures tests can run properly on Windows systems with cp1252 encoding
while maintaining readable output.
"""

import sys
import os
import platform
from typing import Dict, Any, Optional


class UnicodeHelper:
    """Helper class for cross-platform Unicode support in test output"""
    
    # Unicode character mappings for Windows compatibility
    UNICODE_MAPPINGS = {
        '\u2713': 'PASS',     # ✓ -> PASS
        '\u2717': 'FAIL',     # ✗ -> FAIL  
        '\u2192': '->',       # → -> ->
        '\u2190': '<-',       # ← -> <-
        '\u2022': '*',        # • -> *
        '\u2502': '|',        # │ -> |
        '\u250c': '+',        # ┌ -> +
        '\u2510': '+',        # ┐ -> +
        '\u2514': '+',        # └ -> +
        '\u2518': '+',        # ┘ -> +
        '\u2500': '-',        # ─ -> -
        '\u2550': '=',        # ═ -> =
    }
    
    @staticmethod
    def is_windows_cp1252():
        """Check if running on Windows with cp1252 encoding"""
        return (
            platform.system() == 'Windows' and 
            sys.stdout.encoding and 
            'cp1252' in sys.stdout.encoding.lower()
        )
    
    @staticmethod
    def safe_print(message: str, **kwargs):
        """Print message with Unicode character replacement on Windows"""
        if UnicodeHelper.is_windows_cp1252():
            # Replace problematic Unicode characters
            for unicode_char, replacement in UnicodeHelper.UNICODE_MAPPINGS.items():
                message = message.replace(unicode_char, replacement)
        
        try:
            print(message, **kwargs)
        except UnicodeEncodeError:
            # Fallback: encode to ASCII with replacement
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(safe_message, **kwargs)
    
    @staticmethod
    def format_test_result(test_name: str, passed: bool, details: str = "") -> str:
        """Format test result with Windows-safe characters"""
        if UnicodeHelper.is_windows_cp1252():
            status_symbol = "[PASS]" if passed else "[FAIL]"
        else:
            status_symbol = "✓" if passed else "✗"
        
        result = f"  {status_symbol} {test_name}"
        if details:
            result += f": {details}"
        
        return result
    
    @staticmethod
    def create_section_separator(title: str, width: int = 80) -> str:
        """Create a section separator with Windows-safe characters"""
        if UnicodeHelper.is_windows_cp1252():
            line_char = "="
        else:
            line_char = "═"
        
        # Create centered title with separators
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        separator = line_char * padding + title_line + line_char * padding
        
        # Ensure exact width
        if len(separator) < width:
            separator += line_char * (width - len(separator))
        elif len(separator) > width:
            separator = separator[:width]
        
        return separator
    
    @staticmethod
    def safe_format(template: str, **kwargs) -> str:
        """Format string with Unicode replacement for Windows compatibility"""
        formatted = template.format(**kwargs)
        
        if UnicodeHelper.is_windows_cp1252():
            for unicode_char, replacement in UnicodeHelper.UNICODE_MAPPINGS.items():
                formatted = formatted.replace(unicode_char, replacement)
        
        return formatted


class TestReporter:
    """Test reporter with Windows-compatible output"""
    
    def __init__(self, title: str = "Test Results"):
        self.title = title
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def start_testing(self):
        """Mark start of testing session"""
        import time
        self.start_time = time.time()
        
        UnicodeHelper.safe_print(UnicodeHelper.create_section_separator(self.title))
        UnicodeHelper.safe_print(f"Starting {self.title}...")
        UnicodeHelper.safe_print("")
    
    def report_test(self, test_name: str, passed: bool, details: str = "", error: Optional[str] = None):
        """Report individual test result"""
        result = {
            'name': test_name,
            'passed': passed,
            'details': details,
            'error': error
        }
        self.test_results.append(result)
        
        # Print immediate result
        result_line = UnicodeHelper.format_test_result(test_name, passed, details)
        UnicodeHelper.safe_print(result_line)
        
        if error and not passed:
            UnicodeHelper.safe_print(f"    Error: {error}")
    
    def report_section(self, section_name: str):
        """Report start of new test section"""
        UnicodeHelper.safe_print("")
        UnicodeHelper.safe_print(f"[{section_name.upper()}]")
    
    def finish_testing(self):
        """Complete testing session and show summary"""
        import time
        self.end_time = time.time()
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        execution_time = self.end_time - self.start_time if self.start_time else 0
        
        # Print summary
        UnicodeHelper.safe_print("")
        UnicodeHelper.safe_print(UnicodeHelper.create_section_separator("TEST SUMMARY"))
        UnicodeHelper.safe_print(f"Total Tests: {total_tests}")
        UnicodeHelper.safe_print(f"Passed: {passed_tests}")
        UnicodeHelper.safe_print(f"Failed: {failed_tests}")
        UnicodeHelper.safe_print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        UnicodeHelper.safe_print(f"Execution Time: {execution_time:.2f} seconds")
        
        if failed_tests > 0:
            UnicodeHelper.safe_print("")
            UnicodeHelper.safe_print("FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    UnicodeHelper.safe_print(f"  - {result['name']}")
                    if result['error']:
                        UnicodeHelper.safe_print(f"    {result['error']}")
        
        UnicodeHelper.safe_print(UnicodeHelper.create_section_separator("END"))
        
        return passed_tests == total_tests
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary as dictionary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'execution_time': (self.end_time - self.start_time) if self.start_time and self.end_time else 0,
            'all_passed': passed_tests == total_tests,
            'results': self.test_results
        }


def configure_windows_console():
    """Configure Windows console for better Unicode support"""
    if platform.system() == 'Windows':
        try:
            # Try to set console to UTF-8 on Windows 10+
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass  # Ignore if command fails
        
        # Set environment variable for Python Unicode support
        os.environ['PYTHONIOENCODING'] = 'utf-8'


def create_safe_test_output(content: str) -> str:
    """Convert test output to Windows-safe format"""
    if UnicodeHelper.is_windows_cp1252():
        for unicode_char, replacement in UnicodeHelper.UNICODE_MAPPINGS.items():
            content = content.replace(unicode_char, replacement)
    
    return content


# Context manager for safe test execution

class SafeTestExecution:
    """Context manager for safe test execution with proper Unicode handling"""
    
    def __init__(self, test_title: str = "Test Execution"):
        self.test_title = test_title
        self.reporter = TestReporter(test_title)
        self.original_encoding = None
    
    def __enter__(self):
        # Configure console if on Windows
        configure_windows_console()
        
        # Start test reporting
        self.reporter.start_testing()
        
        return self.reporter
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle any uncaught exceptions
        if exc_type:
            self.reporter.report_test(
                "Uncaught Exception", 
                False, 
                error=str(exc_val)
            )
        
        # Finish reporting
        success = self.reporter.finish_testing()
        
        # Return False to propagate exceptions, True to suppress
        return False


if __name__ == "__main__":
    # Demo the Unicode support
    print("Windows Unicode Support Demo")
    print("=" * 40)
    
    print(f"Platform: {platform.system()}")
    print(f"Encoding: {sys.stdout.encoding}")
    print(f"Is Windows CP1252: {UnicodeHelper.is_windows_cp1252()}")
    print("")
    
    # Test Unicode characters
    test_chars = ['✓', '✗', '→', '←', '•']
    
    print("Unicode character test:")
    for char in test_chars:
        try:
            safe_char = UnicodeHelper.UNICODE_MAPPINGS.get(char, char)
            UnicodeHelper.safe_print(f"  {char} -> {safe_char}")
        except Exception as e:
            print(f"  Error with {repr(char)}: {e}")
    
    print("")
    
    # Demo test reporter
    with SafeTestExecution("Demo Tests") as reporter:
        reporter.report_section("Basic Tests")
        reporter.report_test("Unicode Support", True, "All characters converted successfully")
        reporter.report_test("File Creation", True, "Test files created")
        reporter.report_test("Error Handling", False, "Intentional failure", "Demo error message")
        
        reporter.report_section("Advanced Tests") 
        reporter.report_test("Integration Test", True, "All systems operational")
    
    print("\nDemo completed!")