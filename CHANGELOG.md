# Changelog

## Unreleased

### Naming decision — issue #29 option (a): adopt upstream naming (BREAKING / CHANGED, targets minor **0.3.0**)

**This is the documented external-contract change requested by issue #29 and is the
maintainer decision that #21/AGENTS.md said stood "until a maintainer decision changes it."
It is BREAKING for any consumer that reads output file names.** The suite **adopts the
upstream nf-core output-naming convention and retires the header-family filename contract**
(`ID.fhr.fa`, `ID.fhp.faa`, `ID.fhgff3.gff3`, `ID.fhr.<format>`, …). The header family stays
in each file's header and is carried on `meta`; it no longer appears in any output file name.
Per the maintainers' ruling-interpretation this drops **all** file-name family markers for
consistency — including the `.fhr.`/`.fhp.` infix on module-emitted **metadata** files
(`ID.fhr.json` → `ID.json`) — not just the sequence/convert outputs. Because this repo is
pre-1.0, a breaking change increments the **minor**: this lands as the next minor (e.g.
**0.3.0**); the last *published* release stays v0.2.0 and tagging/publishing remains a
maintainer action. The compatibility modules `modules/combine` (`FHR_COMBINE`) and
`modules/convert` (`FHR_CONVERT`) are **deleted** after every caller, test and doc was
migrated.

Output-name migration lines (old → new):

- combine: `ID.fhr.fa` → `ID.fasta` / `ID.fa` (input's extension); `ID.fhr.gfa` → `ID.gfa`;
  `ID.fhp.faa` → `ID.faa`; `ID.fhgff3.gff3` → `ID.gff3`; `.gz`/`.bgz` suffix unchanged.
- convert: `ID.fhr.json` → `ID.json`; `ID.fhr.yaml` → `ID.yaml`; `ID.fhr.html` → `ID.html`;
  header-only protein `ID.fhr.faa` → `ID.fasta` (the toolkit has no `--to faa`); `ID.fhr.fasta`
  → `ID.fasta`; `ID.fhr.gfa` → `ID.gfa`.
- `FHR_CREATE_JSON` standalone JSON: `ID.fhr.json` → `ID.json`.
- Unchanged (never family-named): `ID.verify.txt`, `ID.validate.txt`, `ID.verify-links.txt`,
  `ID.gff3-validate.{json,html}`, `ID.stripped.<kind>`, `converter-tests/*`.

Behavioral notes captured from the #29 slices and re-verified for this decision: the pinned
upstream combine/convert stage inputs by their **original name** (no `input/*` staging — that
was the retired compat module) and refuse to overwrite a staged input (combine: toolkit
`FHR: Output must differ from the input files`; convert: `Input and output names are the same,
set prefix...`), so callers constrain `meta.id`/`ext.prefix` (the example and `FHR_ATTACH`
still gate IDs with `isSampleId`; the Dockstore workflow applies a `.combined` id
disambiguator). `FAIRBIOHEADERS_CONVERT` defaults its output to `<id>_converted.<format>`, so
`FHR_ATTACH` and the example publish `<id>.<format>` by setting
`ext.prefix = { meta.id }` in project config. Direct importers of the retired
`modules/combine`/`modules/convert` must move to the upstream modules and either accept the
upstream names or wrap+rename from their own contract — see the migration lines in
[docs/module-migration.md](docs/module-migration.md). The upstream `faa`-alias request is
**staged, not filed** ("maintainer's call") in that same document.

Changes in this decision:

- **Callers migrated to the pinned upstream modules.** `FHR_ATTACH` composes
  `FAIRBIOHEADERS_COMBINE` + `FAIRBIOHEADERS_VERIFY` + `FAIRBIOHEADERS_CONVERT` (two-row);
  `main.nf` uses `FAIRBIOHEADERS_CONVERT` for the published YAML; the Dockstore workflow uses
  `FAIRBIOHEADERS_COMBINE`; `modules/create_json` renames its JSON output. Sequence-kind logic
  (`sequenceKindOf`) is confirmed to read **input** files only; the protein/genome
  distinction is carried on `meta` (e.g. the harness's `-header` records and `meta.sequenceKind`).
- **Compatibility modules retired.** `modules/combine` (`FHR_COMBINE`, family names) and
  `modules/convert` (`FHR_CONVERT`) and the `FHR_COMBINE` nf-test suite are deleted; the
  `FAIRBIOHEADERS_VERIFY` nf-test setups are retargeted to the pinned upstream combine
  (reports now record `file: <id>.<ext>`; snapshots re-recorded for the changed names only).
- **Every documented marker rewritten in the same change:** README output tables and
  contract rows, `docs/PIPELINES.md` (module table + direct-importer break), the Dockstore
  workflow README and test samplesheet, `tests/run.py` markers, the `FAIRBIOHEADERS_VERIFY`
  snapshots, and the CI example/Dockstore assertions. See [docs/module-migration.md](docs/module-migration.md)
  for the full OLD → NEW table and the resolution of the recorded blockers.

### Verify adopted — final #29 slice (2026-11-14): `FAIRBIOHEADERS_VERIFY` becomes a pinned upstream module (CHANGED for direct importers, targets the same minor **0.3.0**)

nf-core/modules#13635 merged 2026-11-13T15:26:20Z. `modules/nf-core/fairbioheaders/verify`
is now the byte-identical pinned upstream module at merge commit
`6fb4f8f1f3f70a34a1f0efdc84729c5dacbc33e5` (recorded in `modules.json`; drift checker green
7/7/8/7 — the manifest-driven check covers verify automatically). The repository's own
verify implementation is retired **under the same include path**: `FHR_ATTACH`, the Dockstore
workflow and the harness keeps its import line because the pinned tree overlays the local
files, the `(meta, sequence)` input and `(meta, ID.verify.txt)` report tuple are preserved, and
no caller sets `ext.prefix` for verify — so no import was rewritten and none dangles. Three
observable changes for direct importers (CHANGED, on top of the naming BREAKING above, in the
same 0.3.0 minor): (1) **no `--type`** — the toolkit infers the file type from the extension
and rejects unknown ones in the task (`FHR: Unsupported file extension: <name>`) where the
local module forced anything non-GFA/GFF3 to FASTA; (2) the **container is the Seqera Wave
image** (+ `community-cr-prod` blob for Singularity) instead of the BioContainers/Galaxy-depot
pair, so the workflow now pulls only Wave for both of its processes and registry allowlists
must include `community.wave.seqera.io`; (3) the report redirect is **not shell-quoted** —
constrain `meta.id`/`ext.prefix` as for combine/validate/convert. The merged upstream nf-test
suite carries **4** cases (not the 10 recorded at review head: the re-diff at the merge commit
showed the spaced-name test became the changed-after-combine test); the coverage it does not
carry was ported to `tests/run.py` rather than dropped — direct FHGFF3 verification, the new
odd-extension rejection, and a spaced-name report case (compressed verification stays covered
through the `FHR_ATTACH` BGZF run). Full merged-revision contract table, provenance blobs and
the step-by-step record are in [docs/module-migration.md](docs/module-migration.md); CI's
container-family checks moved verify to the Wave loop. With this slice all four
`fairbioheaders` modules are upstream-pinned; #29's remaining checklist items are the routine
`modules/local/` layout migration and the container-pin re-evaluation at the next toolkit
bump (documented as non-blocking in that issue's final-slice comment).

### Prior #29 work (slices 1 and 2a), unchanged by the naming decision except that the
compat modules the slices preserved are now retired

Module migration toward the upstream nf-core `fairbioheaders` modules (issue #29).
Slice 1: `combine` and `validate` are now pinned upstream modules, and the
callers are aligned without dropping any documented output contract. Slice 2a (2026-11-12):
`convert` has merged upstream and is now pinned and tested here too, but its parity check
came out **partial**, so its callers stay on `FHR_CONVERT` pending a maintainer decision.
The toolkit pin stays fair-bioheaders **0.9.0**; `verify` stays repository-owned until its
upstream interface (nf-core/modules#13635, still open as of 2026-11-12) merges and
passes local parity. [docs/module-migration.md](docs/module-migration.md) records the
per-module upstream-vs-local contract tables, the pinned revisions, the update
procedure, the remaining blockers and the adoption steps for the later slices.

- **Pinned upstream modules.** `modules/nf-core/fairbioheaders/combine` is now the
  byte-identical upstream module at `8faff34023b16ecdc41b02bac42989834075e3f1`
  (nf-core/modules#13492, merged 2026-11-09) and `modules/nf-core/fairbioheaders/validate`
  at `86e852ef429e021d16f7279aaddb9b81eb067f8a` (nf-core/modules#13509), each with the
  upstream `.conda-lock/` platform locks, `meta.yml`, `environment.yml` (`bioconda::fair-bioheaders=0.9.0`, unchanged),
  nf-test tests and snapshots; the tests use the shared fixtures merged in
  nf-core/test-datasets#2363. The revisions are recorded in `modules.json`
  (`.nf-core.yml`: `repository_type: pipeline`) and CI now (a) verifies the installed
  files are byte-identical to the recorded revisions and (b) checks the upstream
  modules' Seqera Wave container
  (`community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119`, built
  from the same Bioconda package) against the toolkit pin, while the repository-owned
  modules keep the BioContainers/Galaxy-depot check. Update only via the recorded
  CLI-less complete-directory fetch procedure; the mixed local module layout
  prevents nf-core CLI updates/list/lint here until a separate layout migration.
  Never patch the pinned copies in place.
- **combine: upstream module plus a compatibility module.** The upstream process names
  its output after the **input file's extension** (`PREFIX.fasta`, `PREFIX.faa`, …),
  leaves format inference to the toolkit and can fail when the derived name would
  overwrite a staged input (`ext.prefix` resolves it), whereas the published contracts
  of the example, `FHR_ATTACH` and the Dockstore workflow name outputs by header type.
  The previous implementation therefore moved to the repository-owned
  `modules/combine` as `FHR_COMBINE` (byte-identical except the process name, plus the
  MPL-2.0 source notice and a migration note); `FHR_ATTACH`, the example, the Dockstore
  workflow and the local verify module's test setups use it, and all published names
  (`ID.fhr.fa`, `ID.fhr.gfa`, `ID.fhp.faa`, `ID.fhgff3.gff3`, `.gz` when compressed) are
  unchanged. **Breaking change for the next 0.x minor release — direct importers of
  `modules/nf-core/fairbioheaders/combine`:** that path is now the upstream module with
  the upstream naming contract; import `modules/combine` (or compose `FHR_ATTACH`) to
  keep header-family names. Retiring `FHR_COMBINE` requires resolving the recorded
  naming/quoting blockers (#29).
- **validate: migrated in place.** The pinned upstream `FAIRBIOHEADERS_VALIDATE` keeps
  input tuple, report name (`ID.validate.txt`) and content for this repository's
  constrained callers, and additionally accepts JSON-LD metadata;
  `FHR_CREATE_JSON` and the external-project harness pass unchanged. The two local
  nf-test cases the upstream revision does not carry — an FHR 2.1 record with an `x-`
  extension field validates, the same field under `"2.0"`/`v0.4.0` is rejected — moved
  into `tests/run.py`, preserving the coverage against the pinned toolkit's R15 rule.
  **Breaking change for direct validate importers:** upstream no longer shell-quotes
  staged paths or the prefix as the local copy did. Spaces or shell metacharacters
  in filenames, `meta.id` or `ext.prefix` can fail or change shell interpretation;
  constrain and sanitize these inputs before importing the pinned module. The
  full failure behavior is not identical for those direct callers.
- **Containers.** Pinned upstream modules run the Wave image above; repository modules
  keep `quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0` and the Galaxy depot
  pair. Both families carry the identical toolkit; a docker run can now pull from two
  registries, so offline mirrors must allow `community.wave.seqera.io`. Conda paths are
  unaffected (`${moduleDir}/environment.yml`).
- **Documentation.** New [docs/module-migration.md](docs/module-migration.md) with the
  per-module upstream-vs-local contract tables, the pinned revisions and file digests,
  the update procedure, the caller migration status and the verify/convert adoption
  gates; README, the pipeline guide, the Dockstore workflow README, AGENTS.md and
  CONTRIBUTING.md now state the pins (combine `8faff34023`, validate `86e852ef42`,
  upstream tests, snapshots and shared test-datasets fixtures) and the compatibility
  module.
  Verification in this slice, run inside a
  Nextflow 26.04.6 / Java 21 / Python 3.11 container with the pinned
  fair-bioheaders 0.9.0 on the PATH (native execution; container pulls stay CI's
  job): `nf-test test --ci` **29/29 passed** (8 pinned combine + 7 pinned
  validate + 5 verify + 9 `FHR_COMBINE`, committed snapshots matched);
  `python tests/run.py --converter-source <v0.9.0 checkout>` **57/57 passed**,
  including the two new FHR 2.1 `x-` validate cases and 2410 toolkit tests
  through the converter-test gate; the Dockstore workflow's `test` profile
  passed with the five family-named combine outputs and five
  `Checksum verified.` reports (FHR FASTA/GFA, expanded JSON-LD, FHGFF3, FHP,
  and the FHR → FHGFF3 → FHP chain through the harness). CI's Docker jobs
  (`nf-test --profile docker`, the `-profile docker` examples, the
  `environment/` image build) still need to run on the
  PR; `git diff --check` is clean.

- **Pinned upstream module: convert (slice 2a, 2026-11-12).**
  `modules/nf-core/fairbioheaders/convert` is now the byte-identical upstream module at
  `4dc3bc54779d6caf3a47d49f37811e651fa2700a` (nf-core/modules#13636, merged
  2026-11-11T23:01Z): all eight files (including both `.conda-lock/` platform locks and
  the new `tests/nextflow.config`) were downloaded at that revision and verified against
  the GitHub tree blob hashes, with the digests recorded in
  [docs/module-migration.md](docs/module-migration.md). `modules.json` carries the
  revision; because the drift guard is manifest-driven, CI now verifies three pinned
  modules (combine 7 files, validate 7, convert 8) and the nf-test job's Wave-image pin
  check covers convert as well. The module was read at the **merge commit**, not at the
  review head the migration document had recorded, and the re-diff mattered: the merged
  revision changed the default prefix to `<meta.id>_converted`, dropped the quoting of
  the output redirect that its review head had, added an input/output name-collision
  guard, and replaced its two spaced-name tests with two name-collision tests.
  Never patch the pinned copy; update it only through the recorded procedure.
- **convert: pinned and tested, callers not migrated (partial parity).** The upstream
  module and the repository's `FHR_CONVERT` were compared with real runs on this
  repository's fixtures, and `tests/run.py` now asserts the result instead of documenting
  it as prose: with `ext.prefix = { "${meta.id}.fhr" }` the pinned module produces
  byte-identical JSON, YAML, HTML and header-extraction output to `FHR_CONVERT`, but
  (1) the family-signifying `ID.fhr.<format>` name is only reachable by configuration and
  is not the upstream default, (2) `faa` cannot be named at all because the upstream
  output extension is the `--to` token and the toolkit has no `faa` choice (verified:
  `bioheaders convert --to faa` exits 2 with `invalid choice: 'faa'`, and the probe gets
  `parity-faa.fhr.fasta` with identical bytes where `FHR_CONVERT` writes
  `parity-faa.fhr.faa`), (3) the input is two channel rows instead of one
  `(meta, metadata, format)` tuple, and (4) an unusable format now fails **inside the
  task** rather than before submission. `main.nf`, `FHR_ATTACH` and the published names
  therefore stay on `FHR_CONVERT` (the same treatment as `FHR_COMBINE` in slice 1), and
  `fairbioheaders/convert` is published as the importer-facing module with the rename
  recipe and the exact gap recorded as blockers 1–4 for a maintainer decision.
  **No output name, no module interface and no caller changed in this slice**; the only
  new user-visible surface is the additional pinned module path plus the upstream tests.
- **Regression coverage added for the pinned convert.** Four harness cases: the
  `FHR_CONVERT`-vs-upstream byte/name parity probe (five records including header
  extraction from a combined FHP FASTA), the two upstream format-rejection cases
  (`faa`, `exe`), and the spaced-and-quoted metadata file name the merged upstream
  revision no longer tests. `verify` is untouched: nf-core/modules#13635 is still open
  (head moved `bb6c492` → `bc5a8640` on 2026-11-12) and its slice-1 notes stand.
  Verification in this slice, in the same style as slice 1 (native execution of the
  repository's processes inside a Nextflow 26.04.6 / Java 21 / Python 3.11 container
  with the pinned fair-bioheaders 0.9.0 on the `PATH`; container pulls stay CI's job):
  `nf-test test --ci` **40/40 passed** in 1261 s (the 11 upstream convert cases joined
  slice 1's 29, committed snapshots matching);
  `python tests/run.py --converter-source <v0.9.0 checkout>` **61/61 passed**, including
  the four new convert cases and 2410 toolkit tests through the gate;
  `python3 scripts/check_upstream_modules.py` green for all three pinned modules
  (7 + 7 + 8 files) and `python3 -m unittest discover -s tests -p
  test_upstream_modules.py` green; CI's container-pin step, extended to `combine validate
  convert`, passes when run locally. CI's Docker jobs (`nf-test --profile docker`, the
  `-profile docker` examples, the `environment/` image build) and the Dockstore
  workflow's test profile still need to run on the PR; `git diff --check` is clean.

## 0.2.0 — 2026-11-05

Minor release: moves the pinned toolkit from fair-bioheaders 0.8.5 to 0.9.0, which bundles FAIR-bioHeaders-Specification v0.5.0 and so supports a new schema minor version: FHR 2.1 and FHP/FHGFF3 1.1, whose records may carry top-level `x-` extension fields (spec rule R15). The modules pass these fields through `combine`, `strip`, `verify` and JSON/YAML conversion; `FHR_CONVERT` to HTML leaves them out with a warning. The toolkit's full pytest suite runs again in `FHR_RUN_CONVERTER_TESTS` (no deselection). No module interface or output name changes. Tested baseline: Nextflow 26.04.6, Java 21, Python 3.13, fair-bioheaders 0.9.0 (Bioconda/BioContainers and the hash-locked wheel) and gff3-validator 0.1.0.

- Bump the pinned toolkit to fair-bioheaders 0.9.0 (FAIR-bioHeaders-Tools tag `v0.9.0`, commit `c6d7454`; wheel `296d9b01…b246cd0d28`, the same digest as on PyPI). Every pin moves together: the modules' `conda` (`bioconda::fair-bioheaders=0.9.0`) and BioContainers/Galaxy depot `container` lines (`fair-bioheaders:0.9.0--pyhdfd78af_0`, both verified to exist), the Dockstore workflow's `environment.yml` and README, the nf-test snapshots (they capture the reported version), `environment/requirements.in`, CI's converter checkout and the docs, including the converter-checkout baseline. `requirements.txt` was regenerated with its recorded `uv pip compile` command and only the fair-bioheaders line changed (0.9.0 has the same dependency ranges as 0.8.5).
  `FHR_RUN_CONVERTER_TESTS` no longer deselects `fhr1_compat_test.py::test_old_toolkit_examples_still_validate`: since 0.8.6 (FAIR-bioHeaders-Tools#128) it skips when `git` or the `v0.3.1` tag is unavailable, so the whole toolkit suite runs again. The harness case for a mismatched converter checkout rewrote its version to `0.9.0`, which is now the installed version; it uses `0.0.0` instead.
  What 0.8.6–0.9.0 change for these modules: 0.8.6 infers `.fas`, `.ffn`, `.frn`, `.fsa` and `.mpfa` as FASTA when no `--type` is given; the modules always pass the type (or use `fhr-<type>-*` commands) and name their own outputs, so nothing changes here, and the local modules' `sequenceKindOf` still accepts only the suffixes listed in the README. 0.9.0 bundles FAIR-bioHeaders-Specification v0.5.0: FHR 2.1 and FHP/FHGFF3 1.1 (the `v0.5.0` release URLs, and the raw-main URL) accept top-level `x-` extension fields (spec rule R15); `combine`, `strip`, `verify` and JSON/YAML conversion keep them and the checksum covers them; the JSON-LD and microdata (HTML) writers leave them out with a warning, so `FHR_CONVERT` to `html` drops them; an `x-` key in a record that states `"2.0"`/`"1.0"` or cites v0.4.x is rejected. Records that cite v0.3.x or v0.4.x without `x-` keys are validated exactly as before, so no existing expected output, fixture or harness case changed (the snapshots differ only in the reported version). New nf-test cases for `FAIRBIOHEADERS_VALIDATE` check that an FHR 2.1 record with an `x-` field is valid and that the same field in an FHR 2.0 record is rejected.

## 0.1.1 — 2026-11-02

Patch release: moves the pinned toolkit from fair-bioheaders 0.8.2 to 0.8.5, which adds JSON-LD hardening (only the FHR context is read; unsafe link schemes are refused by the JSON-LD writer and reported by `validate`, `convert`, `combine` and `verify`) and reads raw-main FHR 1 records with a deprecation warning. No module interface or output name changes. Tested baseline: Nextflow 26.04.6, Java 21, Python 3.13, fair-bioheaders 0.8.5 (Bioconda/BioContainers and the hash-locked wheel) and gff3-validator 0.1.0.

- Bump the pinned toolkit to fair-bioheaders 0.8.5 (FAIR-bioHeaders-Tools tag `v0.8.5`, commit `ff20e36`; wheel `203d503b…a89fcda`, the same digest as on PyPI). Every pin moves together: the modules' `conda` (`bioconda::fair-bioheaders=0.8.5`) and BioContainers/Galaxy depot `container` lines (`fair-bioheaders:0.8.5--pyhdfd78af_0`), the Dockstore workflow's `environment.yml` and README, the nf-test snapshots (they capture the reported version), `environment/requirements.in`, CI's converter checkout and the docs, including the converter-checkout baseline. `requirements.txt` was regenerated with its recorded `uv pip compile` command and only the fair-bioheaders line changed (0.8.5 has the same dependency ranges as 0.8.2).
  What 0.8.3–0.8.5 change for these modules: 0.8.3 adds `bioheaders faidx` (not wrapped here yet). 0.8.4 reads FHR 1 records that cite the raw-main schema URL with `schemaVersion` 1 against the v0.3.1 schema, with a deprecation warning, instead of failing them as FHR 2.0. 0.8.5 is a hardening release: JSON-LD input may use only the FHR context (other, extra or nested contexts, `@import`, `@vocab` and `@nest` are refused), the toolkit's JSON-LD writer and schema.org export refuse records whose links use a scheme other than http, https, ftp, urn, doi or info (`FHR_CONVERT` offers neither; its HTML output is microdata), and `validate`, `convert`, `combine` and `verify` print a warning (spec rule R14) for such links while the record stays schema-valid. One harness case changed: `tests/run.py` expected the bundled FHR 1 example, re-pointed at the raw-main URL, to be rejected; with 0.8.4+ it now passes, is published and its task log carries the deprecation warning, and a new case checks that the same record with the string `"1"` is still rejected. `FHR_RUN_CONVERTER_TESTS` deselects the toolkit test `fhr1_compat_test.py::test_old_toolkit_examples_still_validate`: in 0.8.4–0.8.5 it calls `git` unconditionally and the `fhr` image has no `git`, so it failed with `FileNotFoundError`. FAIR-bioHeaders-Tools#128 makes it skip; remove the deselection once the pin moves past 0.8.5. The bundled examples and fixtures use no non-FHR JSON-LD context and no unsafe link scheme, so no other expected output, fixture or nf-test snapshot changed (the snapshots differ only in the reported version).

## 0.1.0 — 2026-10-28

First release, leaving demo status as decided on #21. It covers the consolidation from FAIR-bioHeaders-Tools and the rename below. Tested baseline: Nextflow 26.04.6, Java 21, Python 3.13, fair-bioheaders 0.8.2 (Bioconda/BioContainers and the hash-locked wheel) and gff3-validator 0.1.0.

- The repository is renamed FAIR-bioHeaders-Nextflow (was FHR-Nextflow; GitHub redirects the old name), as decided on #21, before the first release and the Dockstore registration. READMEs, CITATION.cff, the manifests, the Dockstore workflow's `params.json` and schema `$id`, and the include examples use the new name; changelog history keeps the old one.

- Consolidate the Nextflow modules and Dockstore workflow from FAIR-bioHeaders-Tools (#21). The nf-core-style `FAIRBIOHEADERS_COMBINE` and `FAIRBIOHEADERS_VERIFY` modules, their nf-test tests and snapshots, the minimal Dockstore workflow (`workflows/fairbioheaders`, `.dockstore.yml`) and its test assets move here from Tools `nextflow/` with their git history (extracted with `git filter-repo` up to Tools `c1b985a`, the 0.8.2 modules of FAIR-bioHeaders-Tools#107; each imported commit carries a `Migrated-from` trailer). One implementation per job:
  - **combine:** `FAIRBIOHEADERS_COMBINE` replaces `FHR_COMBINE`. It now also takes protein FASTA: `.faa` is read as FASTA, and the output is named by the header type the toolkit takes from the metadata's `schema` URL (`ID.fhp.faa` for FHP, also on `.fa`/`.fasta` input; `ID.fhr.fa`, `ID.fhr.gfa` and `ID.fhgff3.gff3` as before; `.gz` when the input was compressed). New nf-test cases cover FHP on `.faa`, FHP on gzipped protein `.fasta`, FHP on GFA (rejected) and an FHP stub.
  - **verify:** `FAIRBIOHEADERS_VERIFY` replaces the sequence-file branch of `FHR_VALIDATE` (schema plus checksum of a headed FASTA, protein FASTA, GFA or GFF3 file).
  - **validate:** new `FAIRBIOHEADERS_VALIDATE`, an nf-core-style conversion of the standalone-metadata branch of `FHR_VALIDATE`, for JSON/YAML FHR, FHP and FHGFF3 metadata, kept separate from verify.
  - `FHR_CREATE_JSON` validates with `FAIRBIOHEADERS_VALIDATE`; `FHR_ATTACH` uses `FAIRBIOHEADERS_COMBINE` and `FAIRBIOHEADERS_VERIFY` (its `kind` must agree with the sequence extension; `fasta` and `faa` are both FASTA). `modules/combine` and `modules/validate` are removed.

  **Behaviour changes.** Attached FASTA is now `ID.fhr.fa` (was `ID.fhr.fasta`) and attached FHP protein FASTA `ID.fhp.faa` (was `ID.fhr.faa`); compressed input gives BGZF output (`.gz`). Reports are `ID.validate.txt` and `ID.verify.txt` (were `validation.txt`). The exact toolkit-version gates (`fhr-convert`, `bioheaders`, `gff3-validate`) are replaced by nf-core version reporting: each task emits `(task.process, tool, version)` on the `versions` topic and a `versions_<tool>` output (was `(meta, versions.yml)`). The converter-test checkout must declare the installed toolkit version rather than a hard-coded one.

  **Containers.** fair-bioheaders processes (`FAIRBIOHEADERS_*`, `FHR_CONVERT`, `FHR_STRIP`, `FHR_VERIFY_LINKS`) use the Bioconda/BioContainers `fair-bioheaders` 0.8.2 image (Galaxy depot for Singularity/Apptainer) and a conda `environment.yml`. The repository image (`environment/`, label `fhr`) remains only for `GFF3_VALIDATE` (gff3-validator is not on Bioconda yet, bioconda/bioconda-recipes#70098) and `FHR_RUN_CONVERTER_TESTS` (needs pytest). `environment/requirements.in` moves to the fair-bioheaders 0.8.2 release wheel (`d94b3591…ff50f00`, the same digest as on PyPI); `requirements.txt` was regenerated with its recorded `uv pip compile` command and only the fair-bioheaders line changed. CI checks out Tools v0.8.2 (`6e4dc1d`).

  **CI.** `ci.yml` gains the `nf-test` job (module container/Bioconda pin check, then nf-test with Docker) and the `dockstore-workflow` job (`-profile test,docker`), folded in from Tools' `nextflow-modules.yml` and `nextflow-workflow.yml`, plus a Docker FASTA example. The Dockstore test samplesheet uses local copies of the Tools examples it referenced and adds the FHP protein example; `params.json` points at this repository's raw URL, valid once merged.

  Toolkit 0.8.2 also converts FHP metadata to and from HTML microdata and JSON-LD (FAIR-bioHeaders-Tools#98); the harness's FHP HTML case now checks a round trip instead of a refusal.

  Verification: see the PR description (nf-test, nf-core lint, `tests/run.py --converter-source <v0.8.2 checkout>`, the Dockstore test profile and the Docker `main.nf` examples).

- Bump the pinned toolkit to fair-bioheaders 0.8.1 (FAIR-bioHeaders-Tools tag `v0.8.1`, commit `143e9c4`; wheel `3345ca71…c98f3e`, the same digest as on PyPI), a security release: GHSA-4hc8-hc87-xvc8 (the root checksum line must hold only the checksum; header YAML must read the same under YAML 1.1 and 1.2), GHSA-76mq-wm9f-pv33 (header, YAML and metadata size limits) and GHSA-626v-93xc-945f (`bioheaders assess` output escaping and `--online` address checks). `requirements.in` cites the v0.8.1 release wheel; `requirements.txt` was regenerated with its recorded `uv pip compile` command and only the fair-bioheaders line changed, since 0.8.1 has the same dependency ranges. CI checks out the v0.8.1 commit; the version gates in `modules/utils` and `modules/converter_tests`, the test harness and the docs now name 0.8.1. No example, fixture or module needed changes: the bundled examples and FHP fixtures already satisfy the stricter checks, and output file names are unchanged.

  Verification: `python tests/run.py --converter-source <v0.8.1 checkout>` (53 pipeline runs and rejection cases; 1367 toolkit tests), plus the README FASTA, GFA, GFF3, protein, `--verify_links` and `--converter_source` examples, run locally with Nextflow 26.10.3 (the manifest allows `>=26.04.6`), JDK 25 and Python 3.13 from the hash-locked requirements. CI covers Nextflow 26.04.6, Java 21 and the Docker examples.

- Add FHP protein FASTA coverage and bump the pinned toolkit to fair-bioheaders 0.8.0 (FAIR-bioHeaders-Tools tag `v0.8.0`, commit `4ffefb1`; wheel `53394b34…8d598f`, the same digest as on PyPI), resolving the protein slice of FHR-Nextflow #13 and parent FAIR-bioHeaders-Specification #7. FHP support first shipped in toolkit 0.6.0; 0.8.0 is the pinned release that also carries `bioheaders verify-links`. `faa` joins `fasta`/`gfa` as a sequence kind and convert output format, so FHP metadata flows through the existing create/convert/validate/combine/strip/attach composition while the modules keep the `.faa` extension; the toolkit's bundled FHP schema and `fhr-fasta-*` commands remain the only validator, and no FHP rule is reimplemented in Nextflow. New `FHR_VERIFY_LINKS` module wraps `bioheaders verify-links` for `derivedFrom` and `genomeReference` parent checks, with `ext.require_all` (default false) and `ext.fail_on_mismatch` (default true); `verified` is emitted only when every recorded parent was checked and matched, so an unavailable parent cannot be mistaken for a match, and a match proves file identity, not translation correctness. Fixtures cover predicted/database/mixed sets, plain and gzip `.faa`, malformed headers and an FHR genome → FHGFF3 annotation → FHP protein chain (`tests/fixtures/fhp`). The example accepts `--sequence_format faa` (`examples/protein-metadata.json`, `examples/protein.faa`). JSON-LD and HTML microdata stay unsupported for FHP until FAIR-bioHeaders-Tools #58 is released; the toolkit refuses those outputs. FHP release URLs are coordinated via FAIR-bioHeaders-Specification #107 and the release is tracked in FHP-Specification #1; FHT-File-Converter stays retired. The toolkit's separate nf-core combine/verify modules (FAIR-bioHeaders-Tools #49) are not the full family workflow suite.

  Compatibility impact: the toolkit selects a schema from the record's `schema` URL. Raw-main FHR URLs now select FHR schemaVersion **2.0**, so the bundled FHR example cites `https://w3id.org/fair-bioheaders/fhr/v0.3.1` (schemaVersion 1); FHP cites `https://w3id.org/fair-bioheaders/fhp/v0.4.0` (schemaVersion 1.0). An unsupported release URL is rejected, never checked against another schema. The `fhr-convert` version guard, the converter-checkout version check and the harness's mismatch case move to 0.8.0/0.9.0, and CI's converter commit is `4ffefb1`. Only the `fair-bioheaders` wheel line changes in the regenerated `environment/requirements.txt` (`uv pip compile environment/requirements.in --universal --python-version 3.13 --generate-hashes -o environment/requirements.txt`); no other dependency changes. The suite version, toolkit version, validator version and per-type schema contract remain separate.

  Verification: `python tests/run.py --converter-source <v0.8.0 checkout>` (Nextflow 26.04.6, Python 3.13; 52 pipeline runs and rejection cases, 1233 toolkit tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:1225ed1f…bb860243`), and the Docker GFA (with `--converter_source`; 1233 toolkit tests), GFF3 and protein examples. The local host JDK was 17 (the only JDK in the harness tree); CI still uses Java 21 and Nextflow 26.04.6.

- Update current maintainer contacts to `molik@fhref.org` and `wright@fhref.org`. Citation/package metadata and private reporting routes are checked; runtime behavior and historical notices are unchanged.

- Move to fair-bioheaders 0.5.0 (FAIR-bioHeaders-Tools tag `v0.5.0`, commit `60cb2e7`). The wheel URL and sha256 in `environment/requirements.in` and the hash-locked `requirements.txt` change (`7c2123a1…4823d9`, the same digest as on PyPI). No other dependency changes, and the optional `jsonld` extra is not installed. The `fhr-convert` version gate, the converter-checkout check (now expects 0.5.0; the harness's mismatch case uses 0.6.0), the CI checkout commit and the documented baseline follow. The modules still call the unchanged `fhr-*` commands. Verification: `tests/run.py --converter-source` (v0.5.0 worktree `60cb2e7`; 31 runs, 1062 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:4c947240…30cffc45f`) and the Docker GFA and GFF3 examples.

- Add the `GFF3_VALIDATE` module (FHR-Specification #71, Nextflow part), which runs the pinned gff3-validator 0.1.0 on plain, gzip or BGZF GFF3 with an optional genome FASTA (`[]` for none) and emits JSON and HTML reports, `valid` for files without errors and versions. `task.ext` sets the header mode, translation table, findings cap and `fail_on_errors` (default `true`: a file with errors fails the task; `false` emits its reports and omits it from `valid`); unreadable input (validator exit status 2) always fails. The example accepts `--gff3` (with `--gff3_genome` and `--gff3_*` options) and publishes reports under `ID/gff3/` behind the existing converter-test gate. `gff3-validator==0.1.0` joins `environment/requirements.in` and the hash-locked `requirements.txt` (its PyYAML requirement is satisfied by the existing 6.0.3 pin); the tested combination now includes it. Fixtures are byte-exact copies of gff3-validator conformance cases (commit `70f93a4`, MPL-2.0). CI runs a Docker GFF3 example. Verification: `tests/run.py --converter-source` (v0.4.0 worktree `6a71377`; 31 runs, 133 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:524c6ac6…9bf64b`), and the Docker GFA and GFF3 examples.
- Clarify the existing MPL-2.0 policy in the README, contribution guidance and agent instructions, and add a README license badge. No runtime behavior changes.

## 0.1.0-dev

Initial local DSL2 suite for FHR-Specification #15: native JSON creation plus converter validation; generic conversion, metadata/checksum validation, FASTA/GFA combine/strip and converter pytest modules. Validated attach/extract subworkflow and runnable examples. Targets converter 0.3.0 and schemaVersion 1. No release has been published. The dedicated repository is https://github.com/FAIR-bioHeaders/FHR-Nextflow.

Verification uses Nextflow 26.04.6 / Java 21: all five metadata formats round-trip, FASTA and GFA payloads survive attach/strip byte-for-byte, and invalid metadata, IDs, formats and checksums stop execution. The pinned Docker environment also runs the example and converter pytest wrapper.

Added project documentation aligned with the companion repositories: contributing, conduct and security policies, shared private reporting contacts, citation metadata, license notice, expanded agent guidance and a pipeline composition guide. No release or DOI has been assigned. Documentation links and module contracts checked; executable module behavior unchanged.

Replaced the copied USDA government-work notice with Mozilla Public License 2.0, added source notices and MPL-2.0 citation metadata, and removed David Molik's outdated USDA affiliation and government email from this suite's citation record. Companion repositories and dependency licenses are unchanged.

Completed the issue #15 documentation review: explicit SHA-512/256 and padded-base64 checksum contract, supported compatibility baseline, patch/minor/major and pre-1.0 release policies, and current repository links. Documentation links and citation metadata checked; module behavior unchanged.

Correctness review fixes (behavior changes for the example and two modules):

- The example derives one ID per metadata file (file name without `.fhr.json`/`.json`; `example` for the bundled file), rejects duplicate or unsafe IDs, and rejects `--id` with several files; previously all files shared `--id` and overwrote each other's outputs.
- Publication uses workflow outputs (copy mode) instead of asynchronous `subscribe` copies. With `--converter_source`, metadata and sequence results are published only after converter tests pass; JUnit XML and log are always published. With `--sequence`, only attached-file outputs (whose checksum is computed) are published; the YAML now derives from the attached JSON.
- `FHR_CONVERTER_TESTS` is now a workflow: it copies the checkout into the task directory (no `__pycache__` in the input), requires the checkout to declare version 0.3.0, runs tests against the installed converter, always emits `reports`, adds a `passed` output and fails afterwards when tests fail. A content digest of the checkout keeps `-resume` from reusing stale results after nested edits.
- JSON serialization writes UTF-8 without `\u` escapes, omits `null` map entries and rejects Date, NaN/Infinity, `null` list items and non-string keys with the field location.
- The example metadata no longer contains a placeholder `seqcol_id`.
- `environment/requirements.txt` is a hash-locked file generated from `requirements.in` and installed by the Dockerfile, CI and local environments. Added GitHub Actions CI pinned by action digest. The Docker profile runs containers as the invoking user. Version-guard failures now explain the mismatch.
- `tests/run.py` uses explicit checks that survive `python -O` and covers each change.

Verification: `python -O tests/run.py --converter-source` (converter v0.3.0 worktree), `docker build -t fhr-nextflow:0.1.0 environment`, and the Docker GFA example with `--converter_source`, using Nextflow 26.04.6 / Java 21 / Python 3.13.

Moved to FHR-File-Converter 0.3.1, which fixes GHSA-pvq5-772j-fq72 and requires FHR lines to form the leading header block. The hash-locked environment, version guards, CI converter commit and docs now name 0.3.1; pytest in the environment moves to 9.1.1. New rejection cases cover an FHR line after sequence data and concatenated FHR files. Verification: `tests/run.py --converter-source` (converter v0.3.1 worktree; 21 runs, 77 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:e43b5d59…41bf1`) and the Docker GFA example with `--converter_source`.

Moved to FHR-File-Converter 0.3.2, which streams FASTA/GFA files with bounded memory (about 35 MB peak instead of about five times the file size); checksums and outputs are unchanged. The hash-locked environment, version guards, CI converter commit and docs now name 0.3.2. Verification: `tests/run.py --converter-source` (converter v0.3.2 worktree; 21 runs, 102 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:1b0ffe39…fda47`) and the Docker GFA example with `--converter_source`.

Moved to FHR-File-Converter 0.3.3, which adds gzip/bgzip input and output and stdin/stdout pipes; plain-file checksums are unchanged. Verification: `tests/run.py --converter-source` (converter v0.3.3 worktree; 21 runs, 116 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `sha256:7a9bd9b3…f5053f`) and the Docker GFA example.

Moved to the converter's new name, fair-bioheaders 0.4.0, from the renamed FAIR-bioHeaders-Tools repository (formerly FHR-File-Converter). The modules still call the unchanged `fhr-*` commands. Verification: `tests/run.py --converter-source` (v0.4.0 worktree; 21 runs, 133 converter tests), `docker build -t fhr-nextflow:0.1.0 environment` (image `0a566862…`) and the Docker GFA example.

### PR #30 review follow-up — 2026-11-11

- Corrected `modules.json` to the nf-core per-module `git_sha` schema and recorded
  why the mixed local module layout still requires CLI-less updates.
- Restored both platforms' upstream `.conda-lock/` files for each pinned module.
  The new CI guard checks the complete tree (paths, blob hashes and modes),
  including extra local files, with retried GitHub requests.
- Added a collision-safe `ext.prefix` to the importer example and labelled the
  direct-importer combine naming and validate quoting changes as breaking.
- Verification: both complete seven-file upstream trees match their recorded
  revisions; drift-guard regression tests pass; manifest/YAML/Bash checks,
  Ruff, Black, isort and `git diff --check` pass. No process implementation or
  workflow wiring changed in this follow-up. Docker's daemon is unavailable
  locally, so nf-test/container/integration reruns remain CI verification.
