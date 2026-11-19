"""The upstream drift guard must include hidden, missing and unexpected files."""

import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import call, patch

spec = importlib.util.spec_from_file_location(
    "check_upstream_modules",
    Path(__file__).resolve().parents[1] / "scripts/check_upstream_modules.py",
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class UpstreamIdentityTest(unittest.TestCase):
    def test_authenticated_fetch_keeps_tokens_out_of_command(self):
        for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
            with self.subTest(variable=variable), patch.dict(
                os.environ, {variable: "unit-test-token"}, clear=True
            ), patch.object(guard.subprocess, "check_output", return_value=b'{"tree": []}') as request:
                self.assertEqual(guard.fetch_tree("a" * 40), {"tree": []})
                command = request.call_args.args[0]
                self.assertEqual(command[:4], ["gh", "api", "--method", "GET"])
                self.assertNotIn("unit-test-token", " ".join(command))
                self.assertEqual(request.call_count, 1)

    def test_authenticated_failure_does_not_fall_back_to_anonymous(self):
        with patch.dict(os.environ, {"GH_TOKEN": "unit-test-token"}, clear=True), patch.object(
            guard.subprocess, "check_output", side_effect=subprocess.CalledProcessError(1, ["gh", "api"])
        ) as request:
            with self.assertRaises(subprocess.CalledProcessError):
                guard.fetch_tree("a" * 40)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[0][0], "gh")

    def test_unauthenticated_fetch_preserves_curl_error_controls(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            guard.subprocess, "check_output", return_value=b'{"tree": []}'
        ) as request:
            self.assertEqual(guard.fetch_tree("a" * 40), {"tree": []})
            command = request.call_args.args[0]
            self.assertEqual(command[:4], ["curl", "--fail", "--silent", "--show-error"])
            self.assertEqual(command[command.index("--retry") + 1], "3")
            self.assertIn("--max-time", command)

    def test_malformed_response_fails_closed(self):
        with patch.dict(os.environ, {"GH_TOKEN": "unit-test-token"}, clear=True), patch.object(
            guard.subprocess, "check_output", return_value=b"<html>not a tree</html>"
        ):
            with self.assertRaises(ValueError):
                guard.fetch_tree("a" * 40)

    @staticmethod
    def manifest(modules):
        return {"repos": {"https://github.com/nf-core/modules.git": {"modules": {"nf-core": modules}}}}

    def test_shared_revisions_fetch_once_but_every_module_is_checked(self):
        modules = {f"fairbioheaders/{name}": {"git_sha": sha} for name, sha in (
            ("combine", "a" * 40), ("convert", "b" * 40),
            ("validate", "a" * 40), ("verify", "a" * 40),
        )}
        tree = {"tree": [{"path": f"modules/nf-core/{name}/main.nf", "type": "blob",
                          "sha": "blob", "mode": "100644"} for name in modules]}
        with patch.object(Path, "read_text", return_value=json.dumps(self.manifest(modules))), patch.object(
            guard, "fetch_tree", return_value=tree
        ) as request, patch.object(guard, "local_files", return_value={"main.nf": ("blob", "100644")}) as local:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(guard.main(), 0)
            self.assertEqual(request.call_args_list, [call("a" * 40), call("b" * 40)])
            self.assertEqual(local.call_count, 4)

    def test_missing_and_truncated_upstream_trees_fail_closed(self):
        manifest = self.manifest({"fairbioheaders/combine": {"git_sha": "a" * 40}})
        for tree in ({"tree": []}, {"tree": [], "truncated": True}):
            with self.subTest(tree=tree), patch.object(Path, "read_text", return_value=json.dumps(manifest)), patch.object(
                guard, "fetch_tree", return_value=tree
            ), patch.object(guard, "local_files") as local:
                with self.assertRaises(ValueError):
                    guard.main()
                local.assert_not_called()

    def test_hidden_files_and_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".conda-lock").mkdir()
            lock = root / ".conda-lock/linux.txt"
            lock.write_text("pinned\n")
            expected = guard.local_files(root)
            self.assertEqual(list(expected), [".conda-lock/linux.txt"])
            self.assertEqual(guard.compare(expected, guard.local_files(root)), [])
            lock.write_text("changed\n")
            self.assertIn(
                "changed:", guard.compare(expected, guard.local_files(root))[0]
            )
            lock.unlink()
            self.assertEqual(
                guard.compare(expected, guard.local_files(root)),
                ["missing: .conda-lock/linux.txt"],
            )
            (root / "stray.txt").write_text("extra")
            self.assertIn(
                "extra: stray.txt", guard.compare(expected, guard.local_files(root))
            )

    def test_tree_filters_prefix_and_rejects_truncation(self):
        prefix = "modules/nf-core/fairbioheaders/combine/"
        tree = {
            "tree": [
                {
                    "path": prefix + ".conda-lock",
                    "type": "tree",
                    "sha": "unused",
                    "mode": "040000",
                },
                {
                    "path": prefix + ".conda-lock/linux.txt",
                    "type": "blob",
                    "sha": "abc",
                    "mode": "100644",
                },
                {
                    "path": "another/main.nf",
                    "type": "blob",
                    "sha": "other",
                    "mode": "100644",
                },
            ]
        }
        self.assertEqual(
            guard.tree_files(tree, prefix), {".conda-lock/linux.txt": ("abc", "100644")}
        )
        with self.assertRaises(ValueError):
            guard.tree_files(dict(tree, truncated=True), prefix)


if __name__ == "__main__":
    unittest.main()
