#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Derive and verify docs/CAPABILITY-MATRIX.md against the working tree.

The capability matrix is a hand-authored table with machine-enforced honesty:

- every evidence citation (`path :: verbatim text`) must resolve against the
  real file contents of this repository;
- every `tested` or `partial` cell in a type matrix must carry a citation;
- the FHT and FHGM columns may never claim more than `no released contract`
  or `n/a` (rule V7 of FAIR-bioHeaders-Specification: drafts take no release
  form), and no release-shaped FHT/FHGM string may appear anywhere;
- the `matrix-pins` block must agree with modules.json, the module container
  and conda references, environment/requirements.in, nextflow.config and
  .github/workflows/ci.yml, in both directions;
- every process and named workflow under modules/, subworkflows/ and
  workflows/ must have a row in the matrix, and the recorded nf-test case
  counts must match the test files;
- relative links in the document must resolve.

`--self-test` mutates an in-memory copy of the document (fake citation,
citation-free tested cell, perturbed pin, FHT cell marked tested, blank cell)
and fails unless every mutation is caught, so this guard cannot rot into a
no-op. Standard library only; run from anywhere:

    python3 scripts/check_capability_matrix.py [--self-test]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_REL = "docs/CAPABILITY-MATRIX.md"

CITATION_RE = re.compile(r"`([\w./-]+ :: [^`]+?)`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PROCESS_RE = re.compile(r"(?m)^\s*process\s+([A-Z][A-Z0-9_]*)")
WORKFLOW_RE = re.compile(r"(?m)^\s*workflow\s+([A-Z][A-Z0-9_]*)\s*\{")

TYPE_COLUMNS = ("FHR", "FHP", "FHGFF3", "FHT", "FHGM")
RELEASED_COLUMNS = ("FHR", "FHP", "FHGFF3")
DRAFT_COLUMNS = ("FHT", "FHGM")
# Longest prefix first: 'not tested' must be tried before 'tested'.
STATES = (
    "no released contract",
    "not tested",
    "unsupported",
    "partial",
    "tested",
    "n/a",
)
DRAFT_ALLOWED = ("no released contract", "n/a")
# Rule V7: nothing release-shaped for the draft types, anywhere in the document.
FORBIDDEN = (
    re.compile(r"(?i)\bfht/v\d"),
    re.compile(r"(?i)\bfhgm/v\d"),
    re.compile(r"(?i)\breleased FHT\b"),
    re.compile(r"(?i)\breleased FHGM\b"),
    re.compile(r"(?i)\bFHT is released\b"),
    re.compile(r"(?i)\bFHGM is released\b"),
    re.compile(r"(?i)\bofficial FHT\b"),
    re.compile(r"(?i)\bofficial FHGM\b"),
)

UPSTREAM_DIR = "modules/nf-core/fairbioheaders"
CONDA_ENV_FILES = (
    f"{UPSTREAM_DIR}/combine/environment.yml",
    f"{UPSTREAM_DIR}/convert/environment.yml",
    f"{UPSTREAM_DIR}/validate/environment.yml",
    f"{UPSTREAM_DIR}/verify/environment.yml",
    "modules/local/strip/environment.yml",
    "modules/local/verify_links/environment.yml",
    "modules/local/converter_tests/environment.yml",
    "workflows/fairbioheaders/environment.yml",
)


def norm(text):
    """Collapse whitespace so citations may span hard-wrapped source lines."""
    return " ".join(text.split())


class Checker:
    def __init__(self):
        self._cache = {}

    def text(self, rel):
        if rel not in self._cache:
            path = ROOT / rel
            if not path.is_file():
                self._cache[rel] = None
            else:
                self._cache[rel] = norm(
                    path.read_text(encoding="utf-8", errors="replace")
                )
        return self._cache[rel]


def split_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells):
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell) and any(cells)


def parse_tables(doc_lines):
    """Yield (start, end, header_cells, [(line_index, [cells, ...]), ...]) per pipe table."""
    tables = []
    start = 0
    n = len(doc_lines)
    while start < n:
        if doc_lines[start].lstrip().startswith("|"):
            end = start
            while end < n and doc_lines[end].lstrip().startswith("|"):
                end += 1
            header = split_cells(doc_lines[start])
            body = end - start - 1
            if body >= 1 and is_separator(split_cells(doc_lines[start + 1])):
                rows = [
                    (i, split_cells(doc_lines[i])) for i in range(start + 2, end)
                ]
                tables.append((start, end, header, rows))
            start = end
        else:
            start += 1
    return tables


def state_of(cell):
    stripped = cell.strip().strip("*").strip("` ").lower()
    for state in STATES:
        if stripped.startswith(state):
            return state
    return None


def check_citations(doc, ck):
    errors = []
    count = 0
    for match in CITATION_RE.finditer(doc):
        body = match.group(1)
        path, _, needle = body.partition(" :: ")
        count += 1
        haystack = ck.text(path.strip())
        if haystack is None:
            errors.append(f"citation target does not exist: {path.strip()!r}")
            continue
        if norm(needle) not in haystack:
            errors.append(f"citation text not found in {path.strip()}: {norm(needle)[:90]!r}")
    return errors, count


def check_matrix_tables(doc_lines, ck):
    errors = []
    tables = cells = 0
    for _, _, header, rows in parse_tables(doc_lines):
        if header is None or set(TYPE_COLUMNS) - {h.strip("* `") for h in header}:
            continue
        columns = [h.strip("* `") for h in header]
        tables += 1
        for _, row in rows:
            if len(row) != len(columns):
                errors.append(f"matrix row has {len(row)} cells, header has {len(columns)}: {row[0][:40]!r}")
                continue
            for name, cell in zip(columns[1:], row[1:]):
                cells += 1
                if not cell.strip():
                    errors.append(f"blank cell in column {name} of row {row[0][:40]!r}")
                    continue
                state = state_of(cell)
                if state is None:
                    errors.append(f"cell in column {name} does not start with a matrix state word: {cell[:60]!r}")
                    continue
                if name in DRAFT_COLUMNS and state not in DRAFT_ALLOWED:
                    errors.append(f"rule V7 violation: column {name} claims {state!r}: {cell[:60]!r}")
                if state in ("tested", "partial") and "::" not in cell:
                    errors.append(f"{state} cell for {name} carries no citation: {cell[:60]!r}")
    return errors, tables, cells


def parse_pins(doc):
    match = re.search(r"```matrix-pins\n(.*?)```", doc, re.S)
    if not match:
        return None
    pins = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition("=")
        if not sep:
            return None
        pins[key.strip()] = value.strip()
    return pins


def check_pins(doc, ck):
    pins = parse_pins(doc)
    if pins is None:
        return ["docs/CAPABILITY-MATRIX.md has no parseable ```matrix-pins block```"], 0
    errors = []
    required = (
        "toolkit",
        "toolkit_wheel_sha256",
        "converter_checkout_commit",
        "wave_build",
        "biocontainers_build",
        "gff3_validator",
        "suite_version",
        "nextflow_supported",
        "nextflow_nextflow_version_directive",
        "nextflow_dual_leg",
        "nextflow_dist_sha256",
        "nf_test",
    )
    for key in required:
        if key not in pins:
            errors.append(f"matrix-pins is missing {key}")

    def expect(rel, needle, what):
        haystack = ck.text(rel)
        if haystack is None:
            errors.append(f"{what}: cannot read {rel}")
        elif norm(needle) not in haystack:
            errors.append(f"{what}: {rel} does not contain {norm(needle)[:80]!r}")

    for module in ("combine", "convert", "validate", "verify"):
        rel = f"{UPSTREAM_DIR}/{module}/main.nf"
        expect(rel, f"community.wave.seqera.io/library/fair-bioheaders:{pins['toolkit']}--{pins['wave_build']}", f"Wave image pin of {module}")
        expect(f"{UPSTREAM_DIR}/{module}/environment.yml", f"bioconda::fair-bioheaders={pins['toolkit']}", f"conda pin of {module}")
    for rel in ("modules/local/strip/main.nf", "modules/local/verify_links/main.nf"):
        expect(rel, f"quay.io/biocontainers/fair-bioheaders:{pins['toolkit']}--{pins['biocontainers_build']}", f"BioContainers image in {rel}")
        expect(rel, f"depot.galaxyproject.org/singularity/fair-bioheaders:{pins['toolkit']}--{pins['biocontainers_build']}", f"Galaxy depot image in {rel}")
    for rel in CONDA_ENV_FILES:
        expect(rel, f"bioconda::fair-bioheaders={pins['toolkit']}", f"conda environment of {rel}")
    expect("environment/requirements.in", f"fair_bioheaders-{pins['toolkit']}-py3-none-any.whl#sha256={pins['toolkit_wheel_sha256']}", "toolkit wheel hash lock")
    expect("environment/requirements.in", f"gff3-validator=={pins['gff3_validator']}", "gff3-validator pin")
    expect("nextflow.config", f"version = '{pins['suite_version']}'", "suite version")
    expect("nextflow.config", f"nextflowVersion = '{pins['nextflow_nextflow_version_directive']}'", "nextflowVersion directive")
    expect(".github/workflows/ci.yml", f"NXF_VER: {pins['nextflow_supported']}", "CI Nextflow baseline")
    expect(".github/workflows/ci.yml", f"NXF_DIST_SHA256: {pins['nextflow_dist_sha256']}", "CI Nextflow download hash")
    expect(".github/workflows/ci.yml", f"CONVERTER_COMMIT: {pins['converter_checkout_commit']}", "CI toolkit checkout pin")
    expect(".github/workflows/ci.yml", pins["nextflow_dual_leg"], "CI dual snapshot leg")
    expect(".github/workflows/ci.yml", f"version: {pins['nf_test']}", "CI nf-test version")

    manifest_path = ROOT / "modules.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded = {
        name.split("/")[-1]: entry["git_sha"]
        for name, entry in manifest["repos"]["https://github.com/nf-core/modules.git"]["modules"]["nf-core"].items()
    }
    declared = {
        key[len("upstream_pin("):-len(")")]: value
        for key, value in pins.items()
        if key.startswith("upstream_pin(")
    }
    for name, sha in sorted(recorded.items()):
        if declared.get(name) != sha:
            errors.append(f"upstream pin for {name} is {sha} in modules.json but {declared.get(name)!r} in the matrix")
    for name in sorted(declared):
        if name not in recorded:
            errors.append(f"matrix pins an upstream module {name!r} that modules.json does not record")
    return errors, len(pins)


def check_components(doc, ck):
    errors = []
    names = set()
    directories = set()
    for base in ("modules", "subworkflows", "workflows"):
        for nf in sorted((ROOT / base).rglob("main.nf")):
            rel = nf.relative_to(ROOT)
            directories.add(rel.parent.as_posix())
            body = nf.read_text(encoding="utf-8")
            names.update(PROCESS_RE.findall(body))
            names.update(WORKFLOW_RE.findall(body))
    for name in sorted(names):
        if name not in doc:
            errors.append(f"process/workflow {name} is not mentioned in {DOC_REL}")
    for directory in sorted(directories):
        leaf = directory.rsplit("/", 1)[-1]
        if leaf not in doc:
            errors.append(f"module directory {leaf} is not mentioned in {DOC_REL}")
    # nf-test case counts must match the committed suites.
    total = 0
    for module in ("combine", "convert", "validate", "verify"):
        rel = f"{UPSTREAM_DIR}/{module}/tests/main.nf.test"
        count = (ck.text(rel) or "").count('test("')
        total += count
        if f"({count} cases)" not in doc:
            errors.append(f"{module} carries {count} nf-test cases; the matrix must record '(N cases)' with N={count}")
    if f"{total} tests total" not in doc:
        errors.append(f"the four pinned suites hold {total} nf-test cases in total; the matrix must state '{total} tests total'")
    return errors, len(names)


def check_links(doc, ck):
    errors = []
    for match in LINK_RE.finditer(doc):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        resolved = (ROOT / "docs" / target).resolve()
        if not resolved.exists():
            errors.append(f"broken relative link: {target}")
    return errors


def check_forbidden(doc):
    errors = []
    for pattern in FORBIDDEN:
        for match in pattern.finditer(doc):
            line = doc.count("\n", 0, match.start()) + 1
            errors.append(f"rule V7 violation on line {line}: {match.group(0)!r} gives a draft type release form")
    return errors


def run_checks(doc):
    ck = Checker()
    errors = []
    stats = {}
    if "Status date:" not in doc:
        errors.append("the matrix needs a Status date line")
    citation_errors, stats["citations"] = check_citations(doc, ck)
    matrix_errors, stats["matrix tables"], stats["matrix cells"] = check_matrix_tables(doc.splitlines(), ck)
    pin_errors, stats["pins"] = check_pins(doc, ck)
    component_errors, stats["components"] = check_components(doc, ck)
    link_errors = check_links(doc, ck)
    forbidden_errors = check_forbidden(doc)
    errors.extend(citation_errors + matrix_errors + pin_errors + component_errors + link_errors + forbidden_errors)
    return errors, stats


def mutate(doc, name):
    """Return a deliberately wrong copy of the document, or None if unapplied."""
    if name == "fake-citation":
        match = CITATION_RE.search(doc)
        if not match:
            return None
        path, _, _ = match.group(1).partition(" :: ")
        return doc[: match.start()] + f"`{path} :: NO-SUCH-EVIDENCE-SELFTEST`" + doc[match.end() :]
    if name == "pin-drift":
        mutated, count = re.subn(r"(?m)^toolkit = .*$", "toolkit = 9.9.9", doc, count=1)
        return mutated if count else None
    lines = doc.splitlines()
    for start, end, header, rows in parse_tables(lines):
        columns = [h.strip("* `") for h in header]
        if set(TYPE_COLUMNS) - set(columns):
            continue
        row_index, row = rows[0]
        if name == "fht-tested":
            cell = "tested `nextflow.config :: dsl = 2`"
            row[columns.index("FHT")] = cell
        elif name == "blank-cell":
            row[columns.index("FHGM")] = ""
        elif name == "uncited-tested":
            if not any(state_of(cell) == "tested" and "::" in cell for cell in row[1:]):
                continue
            for i, cell in enumerate(row):
                if state_of(cell) == "tested" and "::" in cell:
                    row[i] = CITATION_RE.sub("[evidence deleted]", cell)
                    break
        else:
            continue
        lines[row_index] = "| " + " | ".join(row) + " |"
        return "\n".join(lines) + ("\n" if doc.endswith("\n") else "")
    return None


MUTATIONS = ("fake-citation", "uncited-tested", "pin-drift", "fht-tested", "blank-cell")


def self_test(doc):
    failures = []
    for name in MUTATIONS:
        mutated = mutate(doc, name)
        if mutated is None:
            failures.append(f"{name}: mutation could not be applied")
            continue
        errors, _ = run_checks(mutated)
        if not errors:
            failures.append(f"{name}: the checker accepted a deliberately wrong matrix")
        else:
            print(f"  caught {name}: {errors[0]}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="prove the checker fails on deliberate matrix defects")
    args = parser.parse_args()
    doc_path = ROOT / DOC_REL
    if not doc_path.is_file():
        sys.exit(f"FAIL: {DOC_REL} is missing")
    doc = doc_path.read_text(encoding="utf-8")
    if args.self_test:
        print(f"self-test: {len(MUTATIONS)} deliberate defects must all be caught")
        failures = self_test(doc)
        if failures:
            for failure in failures:
                print(f"  MISSED {failure}")
            sys.exit(f"FAIL: the capability-matrix guard is not fail-tight ({len(failures)} missed)")
        print(f"PASS: every deliberate defect (fake citation, uncited tested cell, perturbed pin, FHT marked tested, blank cell) fails the check")
        return
    errors, stats = run_checks(doc)
    for error in errors:
        print(f"  {error}")
    if errors:
        sys.exit(f"FAIL: {DOC_REL} is inconsistent with the tree ({len(errors)} problems)")
    print(
        "PASS: {citations} evidence citations resolve, {m} matrix tables / {c} cells within vocabulary, "
        "{p} pins agree with the tree, {k} processes/workflows and the nf-test case counts are covered, links resolve".format(
            m=stats["matrix tables"], c=stats["matrix cells"], p=stats["pins"], k=stats["components"], **stats
        )
    )


if __name__ == "__main__":
    main()
