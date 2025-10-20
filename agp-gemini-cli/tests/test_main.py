import subprocess
import sys


def test_cli_help_command():
    """
    Tests if the CLI runs and the --help command works without errors.
    This is a basic smoke test.
    """
    # The test is run from the 'agp-gemini-cli' directory, so the path is just 'main.py'
    cli_main_path = "main.py"

    result = subprocess.run(
        [sys.executable, cli_main_path, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Print stdout for debugging purposes, especially on failure
    print(f"CLI STDOUT:\n---\n{result.stdout}\n---")
    print(f"CLI STDERR:\n---\n{result.stderr}\n---")

    assert result.returncode == 0, (
        f"CLI command failed with exit code {result.returncode}\nStderr: {result.stderr}"
    )
    assert "Usage: main.py [OPTIONS] COMMAND [ARGS]..." in result.stdout
    assert "dashboard" in result.stdout
    assert "hablar" in result.stdout
    assert "setup" in result.stdout
