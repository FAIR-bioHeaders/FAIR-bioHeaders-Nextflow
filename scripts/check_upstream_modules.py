"""Compare complete installed module trees with the revisions in modules.json."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def tree_files(tree, prefix):
    if tree.get("truncated"):
        raise ValueError("GitHub returned a truncated tree; cannot verify identity")
    return {
        item["path"][len(prefix) :]: (item["sha"], item["mode"])
        for item in tree["tree"]
        if item["path"].startswith(prefix) and item["type"] != "tree"
    }


def local_files(directory):
    files = {}
    for parent, dirs, names in os.walk(directory, followlinks=False):
        # Include directory symlinks themselves, never traverse their targets.
        names += [name for name in dirs if (Path(parent) / name).is_symlink()]
        dirs[:] = [name for name in dirs if not (Path(parent) / name).is_symlink()]
        for name in names:
            path = Path(parent) / name
            if path.is_symlink():
                content = os.fsencode(os.readlink(path))
                mode = "120000"
            else:
                content = path.read_bytes()
                mode = "100755" if path.stat().st_mode & 0o111 else "100644"
            blob = b"blob " + str(len(content)).encode() + b"\0" + content
            files[path.relative_to(directory).as_posix()] = (
                hashlib.sha1(blob).hexdigest(),
                mode,
            )
    return files


def compare(expected, actual):
    errors = []
    for name in sorted(expected.keys() | actual.keys()):
        if name not in actual:
            errors.append(f"missing: {name}")
        elif name not in expected:
            errors.append(f"extra: {name}")
        elif expected[name] != actual[name]:
            errors.append(f"changed: {name} (blob or file mode)")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "modules.json").read_text())
    modules = manifest["repos"]["https://github.com/nf-core/modules.git"]["modules"][
        "nf-core"
    ]
    failed = False
    for name, entry in modules.items():
        sha = entry["git_sha"]
        result = subprocess.check_output(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--retry",
                "3",
                "--connect-timeout",
                "15",
                "--max-time",
                "120",
                f"https://api.github.com/repos/nf-core/modules/git/trees/{sha}?recursive=1",
            ]
        )
        prefix = f"modules/nf-core/{name}/"
        expected = tree_files(json.loads(result), prefix)
        if not expected:
            raise ValueError(f"No upstream files for {name} at {sha}")
        errors = compare(expected, local_files(root / prefix))
        for error in errors:
            print(f"{name}: {error}", file=sys.stderr)
        failed |= bool(errors)
        if not errors:
            print(f"{name}: all {len(expected)} files match {sha}")
    return int(failed)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f"Cannot verify upstream modules: {error}")
