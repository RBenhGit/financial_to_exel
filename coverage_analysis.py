#!/usr/bin/env python3
"""
Comprehensive Test Coverage Analysis Script
Analyzes coverage.json to generate baseline inventory and prioritization matrix
"""

import json
import os

def analyze_coverage():
    with open('coverage.json', 'r') as f:
        data = json.load(f)

    files = data['files']

    # Categorize by module type and criticality
    categories = {
        'Core Analysis Engines': [],
        'DCF Valuation': [],
        'DDM Valuation': [],
        'P/B Analysis': [],
        'Data Processing': [],
        'Data Sources': [],
        'Excel Integration': [],
        'Configuration': [],
        'Utilities': [],
        'Other': []
    }

    for file, info in files.items():
        coverage = info['summary']['percent_covered']
        total = info['summary']['num_statements']
        missing = info['summary']['missing_lines']

        if total == 0:  # Skip empty files
            continue

        entry = {
            'file': file,
            'coverage': coverage,
            'total_lines': total,
            'missing_lines': missing,
            'criticality': 'HIGH' if 'engine' in file.lower() or 'calculation' in file.lower() else 'MEDIUM'
        }

        if 'analysis/engines' in file:
            categories['Core Analysis Engines'].append(entry)
        elif 'analysis/dcf' in file:
            categories['DCF Valuation'].append(entry)
        elif 'analysis/ddm' in file:
            categories['DDM Valuation'].append(entry)
        elif 'analysis/pb' in file:
            categories['P/B Analysis'].append(entry)
        elif 'data_processing' in file:
            categories['Data Processing'].append(entry)
        elif 'data_sources' in file:
            categories['Data Sources'].append(entry)
        elif 'excel' in file:
            categories['Excel Integration'].append(entry)
        elif 'config' in file:
            categories['Configuration'].append(entry)
        elif 'utils' in file:
            categories['Utilities'].append(entry)
        else:
            categories['Other'].append(entry)

    print('=' * 80)
    print('COMPREHENSIVE TEST COVERAGE BASELINE ANALYSIS')
    print('=' * 80)
    print()

    for category, files_list in categories.items():
        if files_list:
            files_list.sort(key=lambda x: x['coverage'])
            total_lines = sum(f['total_lines'] for f in files_list)
            avg_coverage = sum(f['coverage'] * f['total_lines'] for f in files_list) / total_lines if total_lines > 0 else 0

            print(f'{category.upper()}:')
            print(f'  Average Coverage: {avg_coverage:.1f}%')
            print(f'  Total Lines: {total_lines}')
            print(f'  Files: {len(files_list)}')
            print('  Priority Files (lowest coverage):')

            for entry in files_list[:3]:  # Show top 3 priority files
                file_short = entry['file'].replace('core\\', '').replace('utils\\', '').replace('config\\', '')
                print(f'    - {entry["coverage"]:5.1f}% | {entry["total_lines"]:4d} lines | {file_short}')
            print()

    print('PRIORITIZATION MATRIX:')
    print('-' * 60)

    all_files = []
    for files_list in categories.values():
        all_files.extend(files_list)

    # Priority scoring: weight by total lines and inverse coverage
    priority_files = []
    for entry in all_files:
        if entry['total_lines'] > 50:  # Focus on substantial files
            # Priority score: (lines * (100 - coverage)) / 100
            priority_score = (entry['total_lines'] * (100 - entry['coverage'])) / 100
            entry['priority_score'] = priority_score
            priority_files.append(entry)

    priority_files.sort(key=lambda x: x['priority_score'], reverse=True)

    print('TOP 15 PRIORITY FILES FOR TEST COVERAGE:')
    print(f'{"Rank":<4} | {"Score":<6} | {"Cov%":<5} | {"Lines":<5} | {"File":<50}')
    print('-' * 80)

    for i, entry in enumerate(priority_files[:15], 1):
        file_short = entry['file'].replace('core\\', '').replace('utils\\', '').replace('config\\', '')
        print(f'{i:<4} | {entry["priority_score"]:6.0f} | {entry["coverage"]:4.1f}% | {entry["total_lines"]:4d} | {file_short}')

    return priority_files

if __name__ == '__main__':
    analyze_coverage()