#!/usr/bin/env python3
"""
Dependency Analyzer for Financial Analysis Codebase
Analyzes import dependencies across all Python files in the project.
"""

import ast
import os
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import json

class DependencyAnalyzer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.dependencies = defaultdict(set)  # file -> set of dependencies
        self.reverse_dependencies = defaultdict(set)  # file -> set of files that depend on it
        self.all_files = set()
        self.external_imports = defaultdict(set)  # track external library imports too
        
    def is_local_module(self, import_name: str) -> bool:
        """Check if an import is a local module (not external library)"""
        # Common external libraries to exclude
        external_libs = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'scipy',
            'requests', 'json', 'os', 'sys', 'time', 'datetime', 'logging',
            'typing', 'pathlib', 'dataclasses', 'abc', 'enum', 'functools',
            'collections', 'itertools', 're', 'argparse', 'hashlib',
            'warnings', 'traceback', 'tkinter', 'openpyxl', 'yfinance',
            'streamlit', 'sqlite3', 'threading', 'concurrent', 'asyncio'
        }
        
        # Split on dots to get base module name
        base_module = import_name.split('.')[0]
        
        # If it's in external libs, it's external
        if base_module in external_libs:
            return False
            
        # If it starts with these patterns, it's external
        external_patterns = ['__', 'email', 'urllib', 'http', 'xml', 'html']
        if any(base_module.startswith(pattern) for pattern in external_patterns):
            return False
            
        # Check if it's a file that exists in our project
        potential_file = self.project_root / f"{base_module}.py"
        if potential_file.exists():
            return True
            
        # If we can't find it as a file, assume it's external unless it looks local
        # Local modules typically don't have common library patterns
        return not any(char in base_module for char in ['_internal', 'pkg_resources'])
    
    def extract_imports_from_file(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """Extract import statements from a Python file"""
        local_imports = set()
        external_imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self.is_local_module(alias.name):
                            local_imports.add(alias.name)
                        else:
                            external_imports.add(alias.name)
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if self.is_local_module(node.module):
                            local_imports.add(node.module)
                        else:
                            external_imports.add(node.module)
                            
        except (SyntaxError, UnicodeDecodeError, Exception) as e:
            print(f"Error parsing {file_path}: {e}")
            
        return local_imports, external_imports
    
    def analyze_project(self) -> None:
        """Analyze all Python files in the project"""
        print("Scanning Python files...")
        
        # Find all Python files (excluding venv and __pycache__)
        python_files = []
        for py_file in self.project_root.glob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):
                python_files.append(py_file)
                
        print(f"Found {len(python_files)} Python files to analyze")
        
        # Extract dependencies from each file
        for py_file in python_files:
            file_stem = py_file.stem
            self.all_files.add(file_stem)
            
            local_imports, external_imports = self.extract_imports_from_file(py_file)
            
            # Store dependencies
            self.dependencies[file_stem] = local_imports
            self.external_imports[file_stem] = external_imports
            
            # Build reverse dependencies
            for dep in local_imports:
                self.reverse_dependencies[dep].add(file_stem)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependency chains using DFS"""
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, set()):
                if neighbor not in self.all_files:
                    continue  # Skip external dependencies
                    
                if neighbor in rec_stack:
                    # Found a cycle - extract the cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor, path, visited, rec_stack)
            
            path.pop()
            rec_stack.remove(node)
        
        cycles = []
        visited = set()
        
        for file in self.all_files:
            if file not in visited:
                dfs(file, [], visited, set())
        
        return cycles
    
    def get_module_metrics(self) -> Dict[str, Dict[str, int]]:
        """Calculate metrics for each module"""
        metrics = {}
        
        for file in self.all_files:
            local_deps = len([dep for dep in self.dependencies.get(file, set()) 
                             if dep in self.all_files])
            external_deps = len(self.external_imports.get(file, set()))
            dependents = len(self.reverse_dependencies.get(file, set()))
            
            metrics[file] = {
                'local_dependencies': local_deps,
                'external_dependencies': external_deps,
                'dependents': dependents,
                'coupling_score': local_deps + dependents
            }
            
        return metrics
    
    def classify_modules(self, metrics: Dict[str, Dict[str, int]]) -> Dict[str, List[str]]:
        """Classify modules into categories"""
        core_modules = []      # High dependents, moderate dependencies
        leaf_modules = []      # Low/no dependents, may have dependencies
        utility_modules = []   # Moderate dependents, low dependencies
        bridge_modules = []    # High coupling (both dependencies and dependents)
        
        for file, metric in metrics.items():
            dependents = metric['dependents']
            local_deps = metric['local_dependencies']
            coupling = metric['coupling_score']
            
            if dependents >= 5:  # Many other modules depend on this
                if local_deps <= 3:
                    utility_modules.append(file)
                else:
                    core_modules.append(file)
            elif dependents == 0:  # Nothing depends on this
                leaf_modules.append(file)
            elif coupling >= 8:  # High overall coupling
                bridge_modules.append(file)
            else:
                if dependents >= 2:
                    core_modules.append(file)
                else:
                    leaf_modules.append(file)
        
        return {
            'core_modules': sorted(core_modules),
            'leaf_modules': sorted(leaf_modules),
            'utility_modules': sorted(utility_modules),
            'bridge_modules': sorted(bridge_modules)
        }
    
    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive dependency analysis report"""
        print("Generating dependency analysis report...")
        
        # Calculate metrics
        metrics = self.get_module_metrics()
        classifications = self.classify_modules(metrics)
        circular_deps = self.find_circular_dependencies()
        
        # Sort modules by different criteria
        most_depended_upon = sorted(metrics.items(), 
                                  key=lambda x: x[1]['dependents'], reverse=True)[:10]
        highest_coupling = sorted(metrics.items(), 
                                key=lambda x: x[1]['coupling_score'], reverse=True)[:10]
        most_dependencies = sorted(metrics.items(), 
                                 key=lambda x: x[1]['local_dependencies'], reverse=True)[:10]
        
        report = {
            'summary': {
                'total_files_analyzed': len(self.all_files),
                'total_local_dependencies': sum(len(deps) for deps in self.dependencies.values()),
                'circular_dependency_chains': len(circular_deps),
                'average_coupling': sum(m['coupling_score'] for m in metrics.values()) / len(metrics)
            },
            'classifications': classifications,
            'circular_dependencies': circular_deps,
            'top_metrics': {
                'most_depended_upon': [(f, m['dependents']) for f, m in most_depended_upon],
                'highest_coupling': [(f, m['coupling_score']) for f, m in highest_coupling],
                'most_dependencies': [(f, m['local_dependencies']) for f, m in most_dependencies]
            },
            'detailed_metrics': metrics,
            'dependency_graph': {f: list(deps) for f, deps in self.dependencies.items()}
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = "dependency_analysis_report.json"):
        """Save the report to a JSON file"""
        output_path = self.project_root / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report saved to: {output_path}")
    
    def print_summary(self, report: Dict):
        """Print a human-readable summary of the analysis"""
        print("\n" + "="*80)
        print("DEPENDENCY ANALYSIS REPORT")
        print("="*80)
        
        summary = report['summary']
        print(f"\nSUMMARY:")
        print(f"   * Total Python files analyzed: {summary['total_files_analyzed']}")
        print(f"   * Total local dependencies: {summary['total_local_dependencies']}")
        print(f"   * Circular dependency chains: {summary['circular_dependency_chains']}")
        print(f"   * Average coupling score: {summary['average_coupling']:.2f}")
        
        # Classifications
        print(f"\nMODULE CLASSIFICATIONS:")
        for category, modules in report['classifications'].items():
            print(f"   * {category.replace('_', ' ').title()}: {len(modules)} modules")
            if modules:
                print(f"     {', '.join(modules[:5])}")
                if len(modules) > 5:
                    print(f"     ... and {len(modules) - 5} more")
        
        # Top metrics
        print(f"\nTOP METRICS:")
        print(f"   * Most depended upon modules:")
        for module, count in report['top_metrics']['most_depended_upon'][:5]:
            print(f"     - {module}: {count} dependents")
            
        print(f"   * Highest coupling modules:")
        for module, score in report['top_metrics']['highest_coupling'][:5]:
            print(f"     - {module}: coupling score {score}")
        
        # Circular dependencies
        if report['circular_dependencies']:
            print(f"\nCIRCULAR DEPENDENCIES FOUND:")
            for i, cycle in enumerate(report['circular_dependencies'], 1):
                print(f"   {i}. {' -> '.join(cycle)}")
        else:
            print(f"\nNo circular dependencies found!")
        
        print("\n" + "="*80)

def main():
    """Main function to run the dependency analysis"""
    project_root = "."  # Current directory
    
    analyzer = DependencyAnalyzer(project_root)
    analyzer.analyze_project()
    
    report = analyzer.generate_report()
    analyzer.print_summary(report)
    analyzer.save_report(report)

if __name__ == "__main__":
    main()