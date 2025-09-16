"""
Streamlit Performance Optimization Module

This module provides optimizations specifically for Streamlit applications including:
- Lazy loading of heavy modules
- Streamlit caching optimizations
- Memory management improvements
- Import optimization strategies
"""

import streamlit as st
import functools
import time
import gc
from typing import Any, Callable, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LazyModuleLoader:
    """Lazy loader for heavy modules to improve startup time"""

    def __init__(self):
        self._modules = {}
        self._import_times = {}

    def load_module(self, module_name: str, import_statement: str):
        """Lazily load a module and cache it"""
        if module_name not in self._modules:
            start_time = time.time()
            try:
                # Execute the import statement
                namespace = {}
                exec(import_statement, namespace)
                self._modules[module_name] = namespace
                import_time = time.time() - start_time
                self._import_times[module_name] = import_time
                logger.info(f"Lazy loaded {module_name} in {import_time:.3f}s")
            except ImportError as e:
                logger.warning(f"Failed to lazy load {module_name}: {e}")
                self._modules[module_name] = None

        return self._modules.get(module_name)

    def get_import_stats(self):
        """Get statistics about import times"""
        return self._import_times


# Global lazy loader instance
lazy_loader = LazyModuleLoader()


def optimized_streamlit_cache(
    func: Optional[Callable] = None,
    ttl: Optional[float] = None,
    max_entries: Optional[int] = None,
    show_spinner: bool = True,
    suppress_st_warning: bool = True
):
    """
    Enhanced Streamlit caching with performance optimizations
    """
    def decorator(func: Callable) -> Callable:
        # Use st.cache_data for better performance with recent Streamlit versions
        if hasattr(st, 'cache_data'):
            cache_decorator = st.cache_data(
                ttl=ttl,
                max_entries=max_entries,
                show_spinner=show_spinner
            )
        else:
            # Fallback for older Streamlit versions
            cache_decorator = st.cache(
                ttl=ttl,
                max_entries=max_entries,
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning
            )

        @cache_decorator
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


@optimized_streamlit_cache(ttl=300, max_entries=10)  # 5-minute TTL, max 10 entries
def load_financial_calculator(data_path: str):
    """Cached loading of financial calculator"""
    # Lazy load the module
    modules = lazy_loader.load_module(
        'financial_calculations',
        'from core.analysis.engines.financial_calculations import FinancialCalculator'
    )

    if modules and 'FinancialCalculator' in modules:
        return modules['FinancialCalculator'](data_path)
    return None


@optimized_streamlit_cache(ttl=3600, max_entries=5)  # 1-hour TTL
def load_heavy_visualization_modules():
    """Lazy load heavy visualization modules"""
    modules = {}

    # Load matplotlib only when needed
    matplotlib_modules = lazy_loader.load_module(
        'matplotlib',
        'import matplotlib.pyplot as plt; import matplotlib'
    )
    if matplotlib_modules:
        modules['matplotlib'] = matplotlib_modules

    # Load plotly only when needed
    plotly_modules = lazy_loader.load_module(
        'plotly',
        'import plotly.graph_objects as go; import plotly.express as px'
    )
    if plotly_modules:
        modules['plotly'] = plotly_modules

    return modules


def optimize_streamlit_config():
    """Apply Streamlit configuration optimizations"""
    if hasattr(st, 'set_page_config'):
        # Only set if not already configured
        try:
            st.set_page_config(
                page_title="FCF Analysis Tool",
                page_icon="📊",
                layout="wide",
                initial_sidebar_state="expanded",
                # Performance optimizations
                menu_items={
                    'Get help': None,  # Disable to reduce overhead
                    'Report a bug': None,  # Disable to reduce overhead
                    'About': None  # Disable to reduce overhead
                }
            )
        except st.errors.StreamlitAPIException:
            # Page config already set
            pass


class MemoryOptimizer:
    """Memory management optimizations for Streamlit"""

    @staticmethod
    def clear_cache():
        """Clear Streamlit cache and force garbage collection"""
        if hasattr(st, 'cache_data') and hasattr(st.cache_data, 'clear'):
            st.cache_data.clear()
        elif hasattr(st, 'legacy_caching') and hasattr(st.legacy_caching, 'clear_cache'):
            st.legacy_caching.clear_cache()

        # Force garbage collection
        gc.collect()

    @staticmethod
    def optimize_memory_usage():
        """Apply memory usage optimizations"""
        # Force garbage collection
        gc.collect()

        # Clear unused session state
        if hasattr(st, 'session_state'):
            keys_to_remove = []
            for key in st.session_state.keys():
                if key.startswith('_temp_') or key.startswith('_cache_'):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del st.session_state[key]


class SessionStateManager:
    """Optimized session state management"""

    @staticmethod
    def initialize_session_state():
        """Initialize session state with performance optimizations"""
        # Only initialize keys that don't exist
        defaults = {
            'company_folder': None,
            'financial_calculator': None,
            'ticker_symbol': None,
            'data_source_priority': ['excel', 'api'],
            'last_update_time': None,
            'cache_version': 1
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def clean_expired_session_data():
        """Clean up expired session data"""
        current_time = time.time()
        expiry_time = 3600  # 1 hour

        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('_temp_'):
                # Check if temporary data has expired
                timestamp_key = f"{key}_timestamp"
                if timestamp_key in st.session_state:
                    if current_time - st.session_state[timestamp_key] > expiry_time:
                        keys_to_remove.extend([key, timestamp_key])

        for key in keys_to_remove:
            del st.session_state[key]


def performance_monitoring_sidebar():
    """Add performance monitoring to sidebar"""
    with st.sidebar:
        with st.expander("🚀 Performance Monitor", expanded=False):
            if st.button("Clear Cache"):
                MemoryOptimizer.clear_cache()
                st.success("Cache cleared!")

            if st.button("Optimize Memory"):
                MemoryOptimizer.optimize_memory_usage()
                st.success("Memory optimized!")

            # Show import statistics
            stats = lazy_loader.get_import_stats()
            if stats:
                st.subheader("Import Times")
                for module, time_taken in stats.items():
                    st.text(f"{module}: {time_taken:.3f}s")


def apply_css_optimizations():
    """Apply CSS optimizations for better performance"""
    st.markdown(
        """
        <style>
        /* Optimize rendering */
        .main > div {
            padding-top: 1rem;
        }

        /* Reduce animation overhead */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }

        /* Optimize metric cards */
        .metric-card {
            background-color: #f0f2f6;
            padding: 0.75rem;
            border-radius: 0.25rem;
            margin: 0.25rem 0;
        }

        /* Hide unnecessary elements for performance */
        .viewerBadge_container__1QSob {
            display: none !important;
        }

        /* Optimize table rendering */
        .dataframe {
            font-size: 0.9rem;
        }

        /* Reduce sidebar overhead */
        .css-1d391kg {
            padding: 1rem 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


class StreamlitPerformanceOptimizer:
    """Main optimizer class for Streamlit applications"""

    def __init__(self, enable_monitoring: bool = True):
        self.enable_monitoring = enable_monitoring
        self.session_manager = SessionStateManager()
        self.memory_optimizer = MemoryOptimizer()

    def initialize_app(self):
        """Initialize the Streamlit app with all optimizations"""
        # Apply configuration optimizations
        optimize_streamlit_config()

        # Initialize session state
        self.session_manager.initialize_session_state()

        # Apply CSS optimizations
        apply_css_optimizations()

        # Add performance monitoring if enabled
        if self.enable_monitoring:
            performance_monitoring_sidebar()

        # Clean expired data
        self.session_manager.clean_expired_session_data()

        logger.info("Streamlit app initialized with performance optimizations")

    def periodic_optimization(self):
        """Run periodic optimizations"""
        # Clean expired session data
        self.session_manager.clean_expired_session_data()

        # Optimize memory usage
        self.memory_optimizer.optimize_memory_usage()


# Global optimizer instance
optimizer = StreamlitPerformanceOptimizer()


def optimize_dataframe_display(df, max_rows: int = 1000):
    """Optimize dataframe display for better performance"""
    if len(df) > max_rows:
        st.warning(f"Displaying first {max_rows} rows of {len(df)} total rows for performance")
        return df.head(max_rows)
    return df


def lazy_import_wrapper(module_path: str, items: list):
    """Wrapper for lazy imports"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Load modules lazily
            import_statement = f"from {module_path} import {', '.join(items)}"
            modules = lazy_loader.load_module(module_path, import_statement)

            if modules:
                # Inject modules into function's global namespace temporarily
                original_globals = func.__globals__.copy()
                for item in items:
                    if item in modules:
                        func.__globals__[item] = modules[item]

                try:
                    result = func(*args, **kwargs)
                finally:
                    # Restore original globals
                    func.__globals__.clear()
                    func.__globals__.update(original_globals)

                return result
            else:
                st.error(f"Failed to load required modules from {module_path}")
                return None

        return wrapper
    return decorator


# Example usage decorator
def requires_heavy_modules(modules: list):
    """Decorator that ensures heavy modules are loaded before function execution"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner("Loading required modules..."):
                load_heavy_visualization_modules()
            return func(*args, **kwargs)
        return wrapper
    return decorator