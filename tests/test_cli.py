import sys
import subprocess
from pathlib import Path
import importlib
import pytest


def test_main_module_exists():
    """Test that the __main__ module exists and has a main function."""
    # Import the __main__ module
    main_module = importlib.import_module("populationsim.__main__")

    # Check that the main function exists
    assert hasattr(main_module, "main")
    assert callable(main_module.main)


def test_cli_execution():
    """Test that the CLI can be executed with basic arguments."""
    # Get the path to the example_test directory
    example_dir = Path(__file__).parent.parent / "examples" / "example_test"

    # Define the paths for configs, data, and output
    configs_dir = example_dir / "configs"
    data_dir = example_dir / "data"
    output_dir = Path(__file__).parent / "output" / "cli_test"

    # Ensure the output directory exists
    output_dir.mkdir(exist_ok=True, parents=True)

    # Build the command to run populationsim
    command = [
        sys.executable,
        "-m",
        "populationsim",
        "-c",
        str(configs_dir),
        "-d",
        str(data_dir),
        "-o",
        str(output_dir),
        "--settings_file",
        "settings.yaml",
    ]

    # Run the command with a timeout to prevent hanging
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 seconds timeout
        )

        # Check that the command completed successfully
        assert result.returncode == 0

        # List all files in the output directory
        output_files = list(output_dir.glob("*"))
        print(f"Files in output directory: {[f.name for f in output_files]}")

        # Check that the output directory contains the pipeline.h5 file
        # This file should always be created
        assert (
            output_dir / "pipeline.h5"
        ).exists(), "pipeline.h5 not found in output directory"

        # Check that at least one output file was created
        # The exact names might vary depending on the configuration
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0, "No CSV files found in output directory"

        # Check for specific types of output files
        # We're looking for files with names containing "summary" or "weights"
        summary_files = [f for f in csv_files if "summary" in f.name]
        weights_files = [f for f in csv_files if "weights" in f.name]

        assert len(summary_files) > 0, "No summary files found in output directory"
        assert len(weights_files) > 0, "No weights files found in output directory"

    except subprocess.TimeoutExpired:
        pytest.fail("CLI execution timed out")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"CLI execution failed with exit code {e.returncode}: {e.stderr}")
