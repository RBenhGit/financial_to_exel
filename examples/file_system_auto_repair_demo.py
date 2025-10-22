"""
File System Auto-Repair Tools Demo (Task 207)

Demonstrates usage of automated file system repair tools including:
- File name standardization
- Directory structure creation
- Duplicate detection and resolution
- Backup and rollback operations
- Batch repair across multiple companies

Usage:
    python examples/file_system_auto_repair_demo.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.file_system_auto_repair import FileSystemAutoRepair
from tools.file_system_validator import FileSystemOrganizationValidator


def demo_single_company_repair():
    """
    Demo: Repair a single company directory with full operations.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Single Company Comprehensive Repair")
    print("=" * 70)

    # Initialize repair system
    repair_system = FileSystemAutoRepair(
        base_path="data/companies",
        auto_confirm=False  # Interactive mode
    )

    # Example company
    company_ticker = "AAPL"
    company_path = Path("data/companies") / company_ticker

    print(f"\n🔧 Repairing company directory: {company_ticker}")
    print(f"📁 Path: {company_path}")

    # First, do a dry run to preview changes
    print("\n🔍 Running dry run to preview changes...")

    dry_run_result = repair_system.repair_company_directory(
        company_path=company_path,
        operations=['create_dirs', 'standardize_names', 'remove_duplicates'],
        dry_run=True,
        create_backup=False
    )

    if dry_run_result['success']:
        print("\n📋 Preview of Changes:")

        for op_name, op_result in dry_run_result['operations_performed'].items():
            print(f"\n  {op_name.replace('_', ' ').title()}:")

            if 'directories_needed' in op_result:
                for dir_path in op_result['directories_needed']:
                    print(f"    ➕ Create directory: {dir_path}")

            if 'renames_needed' in op_result:
                for rename_info in op_result['renames_needed']:
                    print(f"    📝 Rename: {Path(rename_info['from']).name} → "
                          f"{Path(rename_info['to']).name}")

            if 'duplicates_to_remove' in op_result:
                for dup_info in op_result['duplicates_to_remove']:
                    print(f"    🗑️  Remove duplicate: {Path(dup_info['file']).name}")
                    print(f"       (keeping: {Path(dup_info['kept']).name})")

        # Ask user if they want to proceed
        proceed = input("\n❓ Proceed with actual repair? (y/n): ")

        if proceed.lower() == 'y':
            print("\n✨ Performing repair with backup...")

            # Perform actual repair with backup
            repair_result = repair_system.repair_company_directory(
                company_path=company_path,
                operations=['create_dirs', 'standardize_names', 'remove_duplicates'],
                dry_run=False,
                create_backup=True
            )

            if repair_result['success']:
                print(f"\n✅ Repair completed successfully!")

                if repair_result['backup_id']:
                    print(f"💾 Backup ID: {repair_result['backup_id']}")
                    print(f"   (Use this ID for rollback if needed)")

                print("\n📊 Operations Summary:")
                for op_name, op_result in repair_result['operations_performed'].items():
                    if 'renames_performed' in op_result:
                        count = len(op_result['renames_performed'])
                        print(f"  📝 Files renamed: {count}")

                    if 'directories_created' in op_result:
                        count = len(op_result['directories_created'])
                        print(f"  📁 Directories created: {count}")

                    if 'duplicates_removed' in op_result:
                        count = len(op_result['duplicates_removed'])
                        space = op_result.get('space_freed_bytes', 0) / 1024
                        print(f"  🗑️  Duplicates removed: {count} ({space:.2f} KB freed)")
            else:
                print(f"\n❌ Repair failed!")
                for error in repair_result.get('errors', []):
                    print(f"  Error: {error}")
        else:
            print("\n⏭️  Repair cancelled by user")
    else:
        print(f"\n❌ Dry run failed!")


def demo_batch_repair():
    """
    Demo: Batch repair across multiple companies.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Batch Repair Across Multiple Companies")
    print("=" * 70)

    # Initialize repair system
    repair_system = FileSystemAutoRepair(
        base_path="data/companies",
        auto_confirm=True  # Auto-confirm for batch operations
    )

    # Example companies to repair
    company_tickers = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA']

    print(f"\n🔧 Batch repairing {len(company_tickers)} companies...")
    print(f"📋 Companies: {', '.join(company_tickers)}")

    # Progress callback
    def show_progress(current, total, ticker):
        percentage = (current / total) * 100
        print(f"[{current}/{total}] ({percentage:.0f}%) Processing: {ticker}")

    # Perform batch repair with dry run first
    print("\n🔍 Running batch dry run...")

    dry_run_result = repair_system.batch_repair(
        company_tickers=company_tickers,
        operations=['create_dirs', 'standardize_names'],
        dry_run=True,
        progress_callback=show_progress
    )

    if dry_run_result['success']:
        stats = dry_run_result['aggregate_statistics']

        print(f"\n📊 Dry Run Results:")
        print(f"  Total Companies: {dry_run_result['total_companies']}")
        print(f"  Would Create Directories: {stats['total_directories_created']}")
        print(f"  Would Rename Files: {stats['total_files_renamed']}")

        proceed = input("\n❓ Proceed with batch repair? (y/n): ")

        if proceed.lower() == 'y':
            print("\n✨ Performing batch repair...")

            # Actual batch repair
            repair_result = repair_system.batch_repair(
                company_tickers=company_tickers,
                operations=['create_dirs', 'standardize_names'],
                dry_run=False,
                progress_callback=show_progress
            )

            print(f"\n✅ Batch repair completed!")
            print(f"\n📊 Final Results:")
            print(f"  Successfully Repaired: {repair_result['companies_repaired']}")
            print(f"  Failed: {repair_result['companies_failed']}")
            print(f"  Success Rate: {repair_result['aggregate_statistics']['success_rate']}%")

            stats = repair_result['aggregate_statistics']
            print(f"\n📈 Aggregate Statistics:")
            print(f"  Files Renamed: {stats['total_files_renamed']}")
            print(f"  Directories Created: {stats['total_directories_created']}")
            print(f"  Duplicates Removed: {stats['total_duplicates_removed']}")
            print(f"  Space Freed: {stats['total_space_freed_bytes'] / 1024 / 1024:.2f} MB")
        else:
            print("\n⏭️  Batch repair cancelled")


def demo_duplicate_detection():
    """
    Demo: Detect and resolve duplicate files.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Duplicate File Detection and Resolution")
    print("=" * 70)

    # Initialize repair system
    repair_system = FileSystemAutoRepair(
        base_path="data/companies",
        auto_confirm=False
    )

    company_ticker = "AAPL"
    company_path = Path("data/companies") / company_ticker

    print(f"\n🔍 Scanning for duplicate files in: {company_ticker}")

    # Detect duplicates by checksum
    result = repair_system.detect_duplicates(
        company_path,
        comparison_method='checksum'
    )

    if result['success']:
        if result['total_duplicates'] > 0:
            print(f"\n📋 Found {result['total_duplicates']} duplicate file group(s):")

            for i, dup_group in enumerate(result['duplicates_found'], 1):
                print(f"\n  Group {i}:")
                print(f"  Checksum: {dup_group.get('checksum', 'N/A')[:16]}...")

                for file_path in dup_group['files']:
                    file_p = Path(file_path)
                    size = file_p.stat().st_size / 1024
                    print(f"    - {file_p.name} ({size:.2f} KB)")

            potential_savings = result['potential_savings_bytes'] / 1024
            print(f"\n💾 Potential space savings: {potential_savings:.2f} KB")

            # Ask if user wants to resolve duplicates
            resolve = input("\n❓ Resolve duplicates (keep newest)? (y/n): ")

            if resolve.lower() == 'y':
                resolve_result = repair_system.resolve_duplicates(
                    company_path,
                    strategy='keep_newest',
                    dry_run=False
                )

                if resolve_result['success']:
                    removed_count = len(resolve_result['duplicates_removed'])
                    space_freed = resolve_result['space_freed_bytes'] / 1024

                    print(f"\n✅ Duplicates resolved!")
                    print(f"  Files removed: {removed_count}")
                    print(f"  Space freed: {space_freed:.2f} KB")
        else:
            print("\n✨ No duplicate files found!")
    else:
        print(f"\n❌ Duplicate detection failed: {result.get('error')}")


def demo_backup_and_rollback():
    """
    Demo: Backup creation and rollback functionality.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Backup and Rollback Operations")
    print("=" * 70)

    # Initialize repair system
    repair_system = FileSystemAutoRepair(
        base_path="data/companies"
    )

    company_ticker = "AAPL"
    company_path = Path("data/companies") / company_ticker

    print(f"\n💾 Creating backup of: {company_ticker}")

    # Create backup
    backup_result = repair_system.create_backup(
        paths=[company_path],
        description=f"Manual backup of {company_ticker}"
    )

    if backup_result['success']:
        backup_id = backup_result['backup_id']
        manifest = backup_result['manifest']

        print(f"\n✅ Backup created successfully!")
        print(f"  Backup ID: {backup_id}")
        print(f"  Location: {backup_result['backup_path']}")
        print(f"  Files backed up: {manifest['total_files']}")
        print(f"  Total size: {manifest['total_size_bytes'] / 1024:.2f} KB")

        print("\n📝 Backup manifest:")
        for item in manifest['backed_up_paths'][:3]:  # Show first 3
            print(f"  - {Path(item['original']).name}")
            if item['type'] == 'file':
                print(f"    Size: {item['size_bytes'] / 1024:.2f} KB")
                print(f"    Checksum: {item['checksum'][:16]}...")

        if len(manifest['backed_up_paths']) > 3:
            remaining = len(manifest['backed_up_paths']) - 3
            print(f"  ... and {remaining} more items")

        # Ask if user wants to test rollback
        test_rollback = input("\n❓ Test rollback? (this will restore from backup) (y/n): ")

        if test_rollback.lower() == 'y':
            print(f"\n🔄 Rolling back to backup: {backup_id}")

            rollback_result = repair_system.rollback(backup_id)

            if rollback_result['success']:
                print(f"\n✅ Rollback successful!")
                print(f"  Items restored: {rollback_result['items_restored']}")
            else:
                print(f"\n❌ Rollback failed: {rollback_result.get('error')}")
    else:
        print(f"\n❌ Backup failed: {backup_result.get('error')}")


def demo_validation_and_repair_integration():
    """
    Demo: Integration with file system validator.
    """
    print("\n" + "=" * 70)
    print("DEMO 5: Validation + Repair Integration")
    print("=" * 70)

    # Initialize both validator and repair system
    validator = FileSystemOrganizationValidator(base_path="data/companies")
    repair_system = FileSystemAutoRepair(base_path="data/companies", auto_confirm=True)

    company_ticker = "AAPL"

    print(f"\n🔍 Step 1: Validate company directory: {company_ticker}")

    # Validate first
    validation_result = validator.validate_single_company(
        ticker=company_ticker,
        auto_fix=False
    )

    if validation_result:
        compliance = validation_result['overall_compliance']

        print(f"\n📊 Validation Results:")
        print(f"  Status: {compliance['status']}")
        print(f"  Overall Score: {compliance['overall_score']}")
        print(f"  Directory Score: {compliance['directory_score']}")
        print(f"  Excel Score: {compliance['excel_score']}")
        print(f"  Total Issues: {compliance['total_issues']}")

        # Show critical issues if any
        if compliance.get('categorized_issues', {}).get('critical'):
            print(f"\n🚨 Critical Issues:")
            for issue in compliance['categorized_issues']['critical'][:3]:
                print(f"  - {issue['message']}")

        # If not fully compliant, offer to repair
        if compliance['status'] != 'FULLY_COMPLIANT':
            print(f"\n🔧 Step 2: Auto-repair detected issues")

            company_path = Path("data/companies") / company_ticker

            repair_result = repair_system.repair_company_directory(
                company_path=company_path,
                operations=['create_dirs', 'standardize_names'],
                dry_run=False,
                create_backup=True
            )

            if repair_result['success']:
                print(f"\n✅ Repair completed!")

                # Re-validate
                print(f"\n🔍 Step 3: Re-validate after repair")

                new_validation = validator.validate_single_company(
                    ticker=company_ticker,
                    auto_fix=False
                )

                new_compliance = new_validation['overall_compliance']

                print(f"\n📈 Improvement:")
                print(f"  Before: {compliance['overall_score']}")
                print(f"  After: {new_compliance['overall_score']}")
                print(f"  Issues Fixed: {compliance['total_issues'] - new_compliance['total_issues']}")
        else:
            print(f"\n✨ Directory is fully compliant! No repairs needed.")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("FILE SYSTEM AUTO-REPAIR TOOLS - INTERACTIVE DEMO")
    print("=" * 70)

    demos = {
        '1': ('Single Company Repair', demo_single_company_repair),
        '2': ('Batch Repair', demo_batch_repair),
        '3': ('Duplicate Detection', demo_duplicate_detection),
        '4': ('Backup & Rollback', demo_backup_and_rollback),
        '5': ('Validation + Repair Integration', demo_validation_and_repair_integration),
        'a': ('Run All Demos', None)
    }

    while True:
        print("\n📋 Available Demos:")
        for key, (name, _) in demos.items():
            print(f"  {key}. {name}")
        print("  q. Quit")

        choice = input("\n❓ Select a demo to run: ").strip().lower()

        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        elif choice in demos:
            if choice == 'a':
                # Run all demos
                for key in ['1', '2', '3', '4', '5']:
                    try:
                        demos[key][1]()
                    except Exception as e:
                        print(f"\n❌ Demo {key} failed: {e}")
                    input("\nPress Enter to continue to next demo...")
            else:
                try:
                    demos[choice][1]()
                except Exception as e:
                    print(f"\n❌ Demo failed: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("\n❌ Invalid choice. Please try again.")

        input("\nPress Enter to return to menu...")


if __name__ == '__main__':
    main()
