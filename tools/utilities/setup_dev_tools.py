#!/usr/bin/env python3
"""
Development Tools Setup Script
=============================

This script sets up development tools and pre-commit hooks for the financial analysis project.
Run this script once after cloning the repository to configure code quality tools.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Set up development tools."""
    print("🚀 Setting up development tools for Financial Analysis project")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path(".pre-commit-config.yaml").exists():
        print("❌ .pre-commit-config.yaml not found. Please run this script from the project root.")
        sys.exit(1)

    # Install development dependencies
    dev_packages = ["pre-commit", "black", "isort", "flake8", "mypy"]

    for package in dev_packages:
        if not run_command(f"python -m pip install {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, but continuing...")

    # Install pre-commit hooks
    if run_command("pre-commit install", "Installing pre-commit hooks"):
        print("✅ Pre-commit hooks installed successfully")
        print("\n📝 Pre-commit hooks will now run automatically on git commit")
        print("   To run manually: pre-commit run --all-files")
    else:
        print("❌ Failed to install pre-commit hooks")
        print("   You can install manually with: pre-commit install")

    print("\n" + "=" * 60)
    print("🎉 Development tools setup complete!")
    print("\nNext steps:")
    print("1. Commit your changes: git add . && git commit -m 'Setup development tools'")
    print("2. Pre-commit hooks will run automatically on future commits")
    print("3. To run code quality checks manually: pre-commit run --all-files")


if __name__ == "__main__":
    main()
