"""
Module Interface Analysis Report
===============================

Analysis of existing module interfaces to identify coupling issues and
standardization opportunities for improved architecture design.

Findings Summary:
- High coupling between modules due to direct imports and hardcoded dependencies
- Inconsistent data exchange formats across modules  
- Missing abstraction layers for data source integration
- Validation logic scattered across multiple modules
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class CouplingLevel(Enum):
    """Levels of module coupling"""
    LOW = "low"           # Minimal dependencies, well-abstracted
    MEDIUM = "medium"     # Some dependencies, mostly through interfaces  
    HIGH = "high"         # Many direct dependencies, tight coupling
    CRITICAL = "critical" # Extremely coupled, refactoring required


class InterfaceIssue(Enum):
    """Types of interface issues identified"""
    DIRECT_IMPORTS = "direct_imports"
    HARDCODED_PATHS = "hardcoded_paths"
    MIXED_CONCERNS = "mixed_concerns"
    NO_ABSTRACTION = "no_abstraction"
    INCONSISTENT_DATA = "inconsistent_data"
    VALIDATION_SCATTER = "validation_scatter"
    TIGHT_COUPLING = "tight_coupling"


@dataclass
class ModuleAnalysis:
    """Analysis result for a single module"""
    module_name: str
    coupling_level: CouplingLevel
    direct_dependencies: List[str]
    interface_issues: List[InterfaceIssue]
    data_exchange_patterns: List[str]
    refactoring_priority: int  # 1-10, 10 being highest priority
    recommendations: List[str]


# Analysis Results
ANALYSIS_RESULTS = [
    ModuleAnalysis(
        module_name="centralized_data_manager.py",
        coupling_level=CouplingLevel.HIGH,
        direct_dependencies=[
            "yfinance_logger", "input_validator", "data_validator", 
            "error_handler", "pathlib", "numpy", "pandas"
        ],
        interface_issues=[
            InterfaceIssue.DIRECT_IMPORTS,
            InterfaceIssue.MIXED_CONCERNS,
            InterfaceIssue.HARDCODED_PATHS
        ],
        data_exchange_patterns=[
            "Returns raw dictionaries and DataFrames",
            "Uses custom DataCacheEntry class",
            "Mixed return types (dict, DataFrame, None)",
            "Hardcoded data scaling and formatting"
        ],
        refactoring_priority=8,
        recommendations=[
            "Extract data source interface abstraction",
            "Implement standardized data contracts from data_contracts.py",
            "Create dependency injection for logger and validators",
            "Separate caching concerns into dedicated module",
            "Use consistent return types across all methods"
        ]
    ),
    
    ModuleAnalysis(
        module_name="financial_calculations.py",
        coupling_level=CouplingLevel.HIGH,
        direct_dependencies=[
            "enhanced_data_manager", "data_validator", "error_handler",
            "numpy", "pandas", "os", "pathlib"
        ],
        interface_issues=[
            InterfaceIssue.DIRECT_IMPORTS,
            InterfaceIssue.TIGHT_COUPLING,
            InterfaceIssue.MIXED_CONCERNS,
            InterfaceIssue.HARDCODED_PATHS
        ],
        data_exchange_patterns=[
            "Directly accesses file system for Excel data",
            "Returns inconsistent data structures",
            "Mixes calculation and data loading responsibilities",
            "Hardcoded file path patterns and folder structures"
        ],
        refactoring_priority=9,
        recommendations=[
            "Extract data loading into separate data access layer",
            "Implement calculation engine interface",
            "Use standardized CalculationResult contracts",
            "Remove direct file system dependencies",
            "Create separate factory for calculator initialization"
        ]
    ),
    
    ModuleAnalysis(
        module_name="data_sources.py", 
        coupling_level=CouplingLevel.MEDIUM,
        direct_dependencies=[
            "requests", "numpy", "pandas", "pathlib", "hashlib", "json"
        ],
        interface_issues=[
            InterfaceIssue.INCONSISTENT_DATA,
            InterfaceIssue.NO_ABSTRACTION
        ],
        data_exchange_patterns=[
            "Uses DataSourceResponse class (good)",
            "Inconsistent field naming across providers",
            "Different data formats from each API source",
            "Manual field mapping in each provider"
        ],
        refactoring_priority=6,
        recommendations=[
            "Implement field standardization using data_contracts mappings",
            "Create adapter layer for consistent data transformation",
            "Extract common provider functionality to base class",
            "Use unified error handling across all providers"
        ]
    ),
    
    ModuleAnalysis(
        module_name="unified_data_adapter.py",
        coupling_level=CouplingLevel.MEDIUM,
        direct_dependencies=[
            "data_sources", "datetime", "pathlib", "threading"
        ],
        interface_issues=[
            InterfaceIssue.DIRECT_IMPORTS,
            InterfaceIssue.MIXED_CONCERNS
        ],
        data_exchange_patterns=[
            "Good use of dataclasses for internal structures",
            "Consistent caching and usage tracking",
            "Still returns DataSourceResponse - needs standardization",
            "Mixes data access with caching and statistics"
        ],
        refactoring_priority=5,
        recommendations=[
            "Integrate with standardized data contracts",
            "Extract caching into separate service",
            "Extract usage statistics into separate module",
            "Focus on core data adaptation responsibilities"
        ]
    ),
    
    ModuleAnalysis(
        module_name="config.py",
        coupling_level=CouplingLevel.LOW,
        direct_dependencies=[
            "dataclasses", "pathlib", "json"
        ],
        interface_issues=[
            InterfaceIssue.MIXED_CONCERNS
        ],
        data_exchange_patterns=[
            "Good use of dataclasses for configuration",
            "Consistent configuration structure",
            "Multiple config classes could be better organized"
        ],
        refactoring_priority=3,
        recommendations=[
            "Group related configurations into modules",
            "Create configuration factory pattern",
            "Add validation for configuration values"
        ]
    )
]


def get_high_priority_refactoring() -> List[ModuleAnalysis]:
    """Get modules that require immediate refactoring attention"""
    return [
        analysis for analysis in ANALYSIS_RESULTS 
        if analysis.refactoring_priority >= 7
    ]


def get_coupling_issues() -> Dict[CouplingLevel, List[str]]:
    """Group modules by coupling level"""
    coupling_groups = {level: [] for level in CouplingLevel}
    
    for analysis in ANALYSIS_RESULTS:
        coupling_groups[analysis.coupling_level].append(analysis.module_name)
    
    return coupling_groups


def get_common_issues() -> Dict[InterfaceIssue, List[str]]:
    """Get modules grouped by common interface issues"""
    issue_groups = {issue: [] for issue in InterfaceIssue}
    
    for analysis in ANALYSIS_RESULTS:
        for issue in analysis.interface_issues:
            issue_groups[issue].append(analysis.module_name)
    
    return issue_groups


# Refactoring Recommendations Summary
REFACTORING_PLAN = {
    "immediate_priority": [
        {
            "module": "financial_calculations.py",
            "actions": [
                "Extract DataAccessLayer interface",
                "Implement CalculationEngine interface", 
                "Remove direct file system dependencies",
                "Use dependency injection for data manager"
            ]
        },
        {
            "module": "centralized_data_manager.py", 
            "actions": [
                "Extract IDataSourceAdapter interface",
                "Implement standardized data contracts",
                "Separate caching into CacheService",
                "Create DataManagerFactory"
            ]
        }
    ],
    
    "medium_priority": [
        {
            "module": "data_sources.py",
            "actions": [
                "Implement field standardization using data_contracts",
                "Create BaseDataProvider abstraction",
                "Extract common provider patterns"
            ]
        },
        {
            "module": "unified_data_adapter.py",
            "actions": [
                "Integrate standardized contracts",
                "Extract caching and statistics services",
                "Focus on core adaptation logic"
            ]
        }
    ],
    
    "long_term": [
        {
            "module": "config.py",
            "actions": [
                "Organize configurations into logical groups",
                "Implement configuration validation",
                "Create configuration factory"
            ]
        }
    ]
}


def generate_refactoring_report() -> str:
    """Generate a comprehensive refactoring report"""
    report = []
    report.append("=" * 60)
    report.append("MODULE INTERFACE REFACTORING REPORT")
    report.append("=" * 60)
    report.append("")
    
    # High priority modules
    high_priority = get_high_priority_refactoring()
    report.append(f"HIGH PRIORITY REFACTORING ({len(high_priority)} modules):")
    report.append("-" * 40)
    for analysis in high_priority:
        report.append(f"• {analysis.module_name} (Priority: {analysis.refactoring_priority}/10)")
        report.append(f"  Coupling: {analysis.coupling_level.value.upper()}")
        report.append(f"  Issues: {', '.join([issue.value for issue in analysis.interface_issues])}")
        report.append("")
    
    # Coupling analysis
    coupling_issues = get_coupling_issues()
    report.append("COUPLING ANALYSIS:")
    report.append("-" * 20)
    for level, modules in coupling_issues.items():
        if modules:
            report.append(f"{level.value.upper()}: {', '.join(modules)}")
    report.append("")
    
    # Common issues
    common_issues = get_common_issues()
    report.append("COMMON INTERFACE ISSUES:")
    report.append("-" * 25)
    for issue, modules in common_issues.items():
        if modules:
            report.append(f"{issue.value.upper()}: {len(modules)} modules")
            for module in modules:
                report.append(f"  - {module}")
    report.append("")
    
    # Recommendations
    report.append("REFACTORING RECOMMENDATIONS:")
    report.append("-" * 28)
    for priority, items in REFACTORING_PLAN.items():
        report.append(f"\n{priority.upper().replace('_', ' ')}:")
        for item in items:
            report.append(f"  {item['module']}:")
            for action in item['actions']:
                report.append(f"    - {action}")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Print the analysis report
    print(generate_refactoring_report())