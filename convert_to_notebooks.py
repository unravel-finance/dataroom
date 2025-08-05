#!/usr/bin/env python3
"""
Convert run_*.py scripts to Jupyter notebooks using jupytext.
"""

import subprocess
import sys
from pathlib import Path


def convert_file_to_notebook(py_file: Path) -> None:
    """Convert a Python file to a Jupyter notebook using jupytext."""
    # Create notebook filename with 'notebook_' prefix instead of 'run_'
    notebook_name = py_file.stem.replace("run_", "notebook_") + ".ipynb"
    notebook_file = py_file.parent / notebook_name

    print(f"Converting {py_file} to {notebook_file}...")

    try:
        # Use jupytext to convert the Python file to a notebook
        result = subprocess.run(
            [
                "jupytext",
                "--to",
                "notebook",
                "--output",
                str(notebook_file),
                str(py_file),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print(f"✓ Successfully converted {py_file} to {notebook_file}")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error converting {py_file}: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
    except FileNotFoundError:
        print(
            "✗ Error: jupytext not found. Please install it with: pip install jupytext"
        )


def main():
    """Convert all run_*.py files in the root directory to notebooks."""

    # Check if jupytext is installed
    try:
        subprocess.run(["jupytext", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: jupytext is not installed.")
        print("Please install it with: pip install jupytext")
        sys.exit(1)

    # Get the current directory
    root_dir = Path(".")

    # Find all run_*.py files
    run_files = list(root_dir.glob("run_*.py"))

    if not run_files:
        print("No run_*.py files found in the current directory.")
        return

    print(f"Found {len(run_files)} run_*.py files to convert:")
    for file in run_files:
        print(f"  - {file}")

    print("\nStarting conversion...")

    # Convert each file
    for py_file in run_files:
        convert_file_to_notebook(py_file)

    print("\nConversion complete!")
    print("\nGenerated notebooks:")
    for py_file in run_files:
        notebook_name = py_file.stem.replace("run_", "notebook_") + ".ipynb"
        notebook_file = py_file.parent / notebook_name
        if notebook_file.exists():
            print(f"  - {notebook_file}")


if __name__ == "__main__":
    main()
