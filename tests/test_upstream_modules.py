"""The upstream drift guard must include hidden, missing and unexpected files."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_upstream_modules",
    Path(__file__).resolve().parents[1] / "scripts/check_upstream_modules.py",
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class UpstreamIdentityTest(unittest.TestCase):
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
