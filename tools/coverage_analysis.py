#!/usr/bin/env python3
"""
Coverage Analysis Tool

This script generates a comprehensive analysis of test coverage gaps
and provides actionable recommendations for improving test coverage.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_coverage_data(coverage_file: str = "coverage.json") -> Dict:
    """Load coverage data from JSON file."""
    try:
        with open(coverage_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Coverage file {coverage_file} not found. Run pytest with coverage first.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing coverage JSON: {e}")
        return {}


def analyze_coverage_by_module(coverage_data: Dict) -> Dict[str, Dict]:
    """Analyze coverage data by module/package."""
    if not coverage_data.get('files'):
        return {}
    
    module_analysis = {}
    
    for file_path, file_data in coverage_data['files'].items():
        # Normalize path separators and extract module path
        normalized_path = file_path.replace('\\', '/').replace('.py', '')
        
        # Skip test files and non-core modules
        if '/test' in normalized_path or normalized_path.startswith('test'):
            continue
        
        # Extract module hierarchy
        parts = normalized_path.split('/')
        if len(parts) >= 2:
            package = parts[0]  # core, config, utils, etc.
            if package not in ['core', 'config', 'utils']:
                continue
                
            subpackage = parts[1] if len(parts) > 2 else 'root'
            
            # Initialize package structure
            if package not in module_analysis:
                module_analysis[package] = {
                    'subpackages': {},
                    'total_statements': 0,
                    'total_missing': 0,
                    'coverage_percent': 0.0
                }
            
            if subpackage not in module_analysis[package]['subpackages']:
                module_analysis[package]['subpackages'][subpackage] = {
                    'files': {},
                    'total_statements': 0,
                    'total_missing': 0,
                    'coverage_percent': 0.0
                }
            
            # Extract coverage metrics
            summary = file_data.get('summary', {})
            statements = summary.get('num_statements', 0)
            missing = summary.get('missing_lines', 0)
            covered = statements - len(missing) if isinstance(missing, list) else statements - missing
            coverage = (covered / statements * 100) if statements > 0 else 0.0
            
            # Store file-level data
            module_analysis[package]['subpackages'][subpackage]['files'][file_path] = {
                'statements': statements,
                'missing': len(missing) if isinstance(missing, list) else missing,
                'coverage_percent': coverage,
                'missing_lines': missing if isinstance(missing, list) else []
            }
            
            # Update subpackage totals
            module_analysis[package]['subpackages'][subpackage]['total_statements'] += statements
            module_analysis[package]['subpackages'][subpackage]['total_missing'] += len(missing) if isinstance(missing, list) else missing
            
            # Update package totals
            module_analysis[package]['total_statements'] += statements
            module_analysis[package]['total_missing'] += len(missing) if isinstance(missing, list) else missing
    
    # Calculate coverage percentages
    for package_name, package_data in module_analysis.items():
        if package_data['total_statements'] > 0:
            covered = package_data['total_statements'] - package_data['total_missing']
            package_data['coverage_percent'] = (covered / package_data['total_statements']) * 100
        
        for subpackage_name, subpackage_data in package_data['subpackages'].items():
            if subpackage_data['total_statements'] > 0:
                covered = subpackage_data['total_statements'] - subpackage_data['total_missing']
                subpackage_data['coverage_percent'] = (covered / subpackage_data['total_statements']) * 100
    
    return module_analysis


def identify_coverage_priorities(module_analysis: Dict) -> List[Dict]:
    """Identify high-priority files for test coverage improvement."""
    priorities = []
    
    for package_name, package_data in module_analysis.items():
        for subpackage_name, subpackage_data in package_data['subpackages'].items():
            for file_path, file_data in subpackage_data['files'].items():
                # Priority calculation based on:
                # - Number of statements (complexity weight)
                # - Coverage percentage (urgency weight)
                # - Core importance (package weight)
                
                complexity_weight = min(file_data['statements'] / 100, 3.0)  # Max weight of 3
                urgency_weight = (100 - file_data['coverage_percent']) / 100  # 0-1 scale
                
                # Package importance weights
                package_weights = {
                    'core': 3.0,
                    'config': 2.0,
                    'utils': 1.5
                }
                importance_weight = package_weights.get(package_name, 1.0)
                
                priority_score = complexity_weight * urgency_weight * importance_weight
                
                priorities.append({
                    'file_path': file_path,
                    'package': package_name,
                    'subpackage': subpackage_name,
                    'statements': file_data['statements'],
                    'missing': file_data['missing'],
                    'coverage_percent': file_data['coverage_percent'],
                    'priority_score': priority_score,
                    'missing_lines': file_data.get('missing_lines', [])
                })
    
    # Sort by priority score (highest first)
    return sorted(priorities, key=lambda x: x['priority_score'], reverse=True)


def generate_coverage_report(module_analysis: Dict, priorities: List[Dict]) -> str:
    """Generate a comprehensive coverage analysis report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Test Coverage Analysis Report
Generated on: {timestamp}

## Executive Summary

"""
    
    # Overall statistics
    total_statements = sum(pkg['total_statements'] for pkg in module_analysis.values())
    total_missing = sum(pkg['total_missing'] for pkg in module_analysis.values())
    overall_coverage = ((total_statements - total_missing) / total_statements * 100) if total_statements > 0 else 0
    
    report += f"""
- **Total Statements**: {total_statements:,}
- **Missing Coverage**: {total_missing:,}
- **Overall Coverage**: {overall_coverage:.2f}%
- **Packages Analyzed**: {len(module_analysis)}

"""
    
    # Package-level breakdown
    report += "## Package Coverage Breakdown\n\n"
    for package_name, package_data in sorted(module_analysis.items()):
        report += f"### {package_name.title()} Package\n"
        report += f"- **Coverage**: {package_data['coverage_percent']:.2f}%\n"
        report += f"- **Statements**: {package_data['total_statements']:,}\n"
        report += f"- **Missing**: {package_data['total_missing']:,}\n"
        report += f"- **Subpackages**: {len(package_data['subpackages'])}\n\n"
        
        # Subpackage breakdown
        for sub_name, sub_data in sorted(package_data['subpackages'].items()):
            if sub_data['total_statements'] > 0:
                report += f"  - **{sub_name}**: {sub_data['coverage_percent']:.1f}% "
                report += f"({sub_data['total_statements']} statements)\n"
        report += "\n"
    
    # High-priority files
    report += "## High-Priority Coverage Gaps\n\n"
    report += "Files ranked by priority for test coverage improvement:\n\n"
    
    for i, priority in enumerate(priorities[:15], 1):  # Top 15 files
        report += f"### {i}. {priority['file_path']}\n"
        report += f"- **Package**: {priority['package']}/{priority['subpackage']}\n"
        report += f"- **Coverage**: {priority['coverage_percent']:.1f}%\n"
        report += f"- **Statements**: {priority['statements']}\n"
        report += f"- **Priority Score**: {priority['priority_score']:.2f}\n"
        if priority['missing_lines']:
            sample_lines = priority['missing_lines'][:5]  # Show first 5 missing lines
            report += f"- **Sample Missing Lines**: {sample_lines}\n"
        report += "\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    report += "### Immediate Actions (Next 2 weeks)\n"
    report += "1. **Focus on Core Analysis Engines**: The financial calculation engines have 0% coverage\n"
    report += "2. **Implement DCF Module Tests**: Critical valuation functionality needs comprehensive testing\n"
    report += "3. **Add Data Processing Tests**: Core data handling logic requires validation\n\n"
    
    report += "### Medium-term Goals (Next month)\n"
    report += "1. **Achieve 70% Overall Coverage**: Set minimum coverage threshold\n"
    report += "2. **Complete P/B Analysis Testing**: Historical analysis and statistical modules\n"
    report += "3. **Configuration Module Coverage**: Ensure settings and constants are validated\n\n"
    
    report += "### Long-term Strategy (Next quarter)\n"
    report += "1. **90% Coverage Target**: Comprehensive test suite for all core functionality\n"
    report += "2. **Integration Test Coverage**: End-to-end workflow validation\n"
    report += "3. **Performance Test Coverage**: Ensure scalability and efficiency\n\n"
    
    report += "### Coverage Implementation Strategy\n\n"
    report += "#### Test Categories to Implement:\n"
    report += "- **Unit Tests**: Individual function and method testing\n"
    report += "- **Integration Tests**: Module interaction validation\n"
    report += "- **Property-based Tests**: Edge case and boundary testing\n"
    report += "- **Mock Tests**: External dependency isolation\n\n"
    
    report += "#### Suggested Test Frameworks:\n"
    report += "- **pytest**: Primary testing framework (already configured)\n"
    report += "- **pytest-mock**: For mocking external dependencies\n"
    report += "- **hypothesis**: For property-based testing\n"
    report += "- **pytest-benchmark**: For performance testing\n\n"
    
    return report


def main():
    """Main function to run coverage analysis."""
    logger.info("Starting coverage analysis...")
    
    # Load coverage data
    coverage_data = load_coverage_data()
    if not coverage_data:
        logger.error("No coverage data available. Exiting.")
        return
    
    # Analyze coverage by module
    logger.info("Analyzing coverage by module...")
    module_analysis = analyze_coverage_by_module(coverage_data)
    
    if not module_analysis:
        logger.warning("No module analysis data generated.")
        return
    
    # Identify priorities
    logger.info("Identifying coverage priorities...")
    priorities = identify_coverage_priorities(module_analysis)
    
    # Generate report
    logger.info("Generating coverage report...")
    report = generate_coverage_report(module_analysis, priorities)
    
    # Save report
    report_path = Path("reports") / "coverage_analysis_report.md"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Coverage analysis report saved to: {report_path}")
    
    # Print summary
    total_files = sum(len(pkg['subpackages']) for pkg in module_analysis.values())
    print(f"\nCoverage Analysis Complete!")
    print(f"   - Total modules analyzed: {len(module_analysis)}")
    print(f"   - High-priority files identified: {len(priorities)}")
    print(f"   - Report saved to: {report_path}")
    print(f"   - HTML coverage report available in: htmlcov/index.html")


if __name__ == "__main__":
    main()