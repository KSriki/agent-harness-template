"""THE model seam — the single place the harness touches an LLM.

Shells out to `claude -p` (headless). Everything above this seam is
deterministic and unit-testable with a mocked `call_model`. Swapping providers
means swapping this one function.

Honest unavailability: a missing or unauthenticated CLI raises ModelUnavailable;
run.py turns that into a LOUD skip (exit 0, never fake-green, never red for
absence of the tool).
"""

from __future__ import annotations

import shutil
import subprocess

DEFAULT_CLI = "claude"
DEFAULT_TIMEOUT_S = 120


class ModelUnavailable(Exception):
    """The model CLI is missing, unauthenticated, or not answering."""


def check_cli_available(cli: str = DEFAULT_CLI) -> tuple[bool, str]:
    """Cheap pre-flight: is the CLI on PATH at all?"""
    if shutil.which(cli) is None:
        return False, f"'{cli}' CLI not found on PATH"
    return True, ""


def call_model(
    prompt: str,
    model: str,
    cli: str = DEFAULT_CLI,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> str:
    """One prompt in, raw text out. Raises ModelUnavailable on any CLI failure."""
    argv = [cli, "-p", prompt, "--model", model]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        raise ModelUnavailable(f"'{cli}' call failed: {exc}") from exc
    if proc.returncode != 0:
        raise ModelUnavailable(
            f"'{cli}' exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout
