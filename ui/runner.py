"""
Subprocess runner for analytics scripts.

Executes customer_360.py, loan_scoring.py, and fraud_detect.py scripts
and returns their fixed-width output records.
"""

import subprocess
import sys
from pathlib import Path


class RunnerError(Exception):
    """Raised when script execution fails."""
    pass


def run_script(script_path: str, args: list) -> str:
    """
    Execute a Python script and return its stdout output.

    Args:
        script_path: Relative path to script (e.g., "python/customer_360.py")
        args: List of command-line arguments

    Returns:
        String output from script (stripped of CRLF)

    Raises:
        RunnerError: If script execution fails or returns error code
    """
    try:
        # Get project root (parent of ui/)
        project_root = Path(__file__).parent.parent.resolve()

        # Build command: use sys.executable for maximum portability
        cmd = [sys.executable, str(project_root / script_path)] + args

        # Execute with project root as working directory
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check for execution errors
        if result.returncode != 0:
            raise RunnerError(
                f"Script {script_path} exited with code {result.returncode}\n"
                f"stderr: {result.stderr}"
            )

        # Return stdout, stripped only of newlines (preserve spaces in fixed-width record)
        output = result.stdout.rstrip('\n\r')
        if not output:
            raise RunnerError(f"Script {script_path} produced no output")

        return output

    except subprocess.TimeoutExpired:
        raise RunnerError(f"Script {script_path} timed out (>30s)")
    except FileNotFoundError as e:
        raise RunnerError(f"Script not found: {script_path}\n{e}")
    except Exception as e:
        raise RunnerError(f"Failed to execute {script_path}: {e}")
