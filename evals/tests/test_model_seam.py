"""Model-seam tests. The seam shells out to `claude -p`; tests NEVER call the
real CLI — subprocess/which are patched at the boundary."""

import subprocess
import tempfile
import unittest
from unittest import mock

from evals.runners.model import ModelUnavailable, call_model, check_cli_available


class TestCallModel(unittest.TestCase):
    @mock.patch("evals.runners.model.subprocess.run")
    def test_shells_out_to_claude_p_with_model(self, run):
        run.return_value = mock.Mock(returncode=0, stdout="feature\n", stderr="")
        out = call_model("classify this", model="claude-haiku-4-5")
        self.assertEqual(out, "feature\n")
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "claude")
        self.assertIn("-p", argv)
        self.assertIn("classify this", argv)
        self.assertIn("--model", argv)
        self.assertIn("claude-haiku-4-5", argv)

    @mock.patch("evals.runners.model.subprocess.run")
    def test_runs_from_neutral_cwd_so_repo_hooks_never_fire(self, run):
        """Regression (ticket yxr): `claude -p` inheriting the repo cwd fires the
        repo's SessionStart hook (bd prime — dolt lock contention with the
        calling session) and the Stop-hook gate, which re-runs the evals:
        recursive spawn. The seam must run the CLI from a neutral directory."""
        run.return_value = mock.Mock(returncode=0, stdout="ok\n", stderr="")
        call_model("x", model="m")
        cwd = run.call_args.kwargs.get("cwd")
        self.assertEqual(cwd, tempfile.gettempdir())

    @mock.patch("evals.runners.model.subprocess.run")
    def test_nonzero_exit_raises_unavailable_with_stderr(self, run):
        run.return_value = mock.Mock(
            returncode=1, stdout="", stderr="not authenticated"
        )
        with self.assertRaises(ModelUnavailable) as ctx:
            call_model("x", model="m")
        self.assertIn("not authenticated", str(ctx.exception))

    @mock.patch("evals.runners.model.subprocess.run")
    def test_timeout_raises_unavailable(self, run):
        run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)
        with self.assertRaises(ModelUnavailable):
            call_model("x", model="m")


class TestCliAvailability(unittest.TestCase):
    @mock.patch("evals.runners.model.shutil.which", return_value=None)
    def test_missing_cli_reported(self, _which):
        ok, reason = check_cli_available()
        self.assertFalse(ok)
        self.assertIn("claude", reason)
        self.assertIn("not found", reason)

    @mock.patch("evals.runners.model.shutil.which", return_value="/usr/bin/claude")
    def test_present_cli_ok(self, _which):
        ok, reason = check_cli_available()
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
