# Module migration: upstream nf-core `fairbioheaders` modules (issue #29)

This document tracks the migration of this repository's Nextflow workflows to the
upstream [nf-core/modules](https://github.com/nf-core/modules) `fairbioheaders`
module set, the pinned revisions, the per-module contract comparison against the
local implementations, and the remaining adoption steps. It exists because the
upstream modules and the repository modules intentionally diverged during
development (#21 consolidation, then the upstream submissions) and must be
reconciled without silently dropping documented behavior.

Status date: **2026-11-12** (all upstream state below was re-verified against the
GitHub API on this date; re-check before acting on it — checkouts and PRs move).

## Upstream state (verified 2026-11-12)

| Upstream module | PR | State | Revision |
| --- | --- | --- | --- |
| `fairbioheaders/combine` | [nf-core/modules#13492](https://github.com/nf-core/modules/pull/13492) | merged 2026-11-09 | `8faff34023b16ecdc41b02bac42989834075e3f1` |
| `fairbioheaders/validate` | [nf-core/modules#13509](https://github.com/nf-core/modules/pull/13509) | merged 2026-11-09 | `86e852ef429e021d16f7279aaddb9b81eb067f8a` (contained in `8faff340…`) |
| `fairbioheaders/verify` | [nf-core/modules#13635](https://github.com/nf-core/modules/pull/13635) | **open, in review** (still open 2026-11-12, branch last updated 2026-11-12) | head at review time `bb6c49233b2f4ce467b7e332dcfc2c1608e35067`; head 2026-11-12 `bc5a8640cfbca366bfe9d967ad9e43f5dc292216` (a moving PR branch, not a merge revision) |
| `fairbioheaders/convert` | [nf-core/modules#13636](https://github.com/nf-core/modules/pull/13636) | merged 2026-11-11T23:01Z | `4dc3bc54779d6caf3a47d49f37811e651fa2700a` (merge commit; PR head at merge `35dc28bd72563db7fb7192d9fcee7068b65984c4`, review head `639dd3cc…` was superseded — see the contract table) |

Shared test fixtures landed in [nf-core/test-datasets#2363](https://github.com/nf-core/test-datasets/pull/2363);
they resolve under `modules_testdata_base_path` at
`genomics/sarscov2/genome/fairbioheaders/` and
`genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/fairbioheaders/`
(verified present on the `modules` branch 2026-11-10; the convert suite fetched the
same paths again on 2026-11-12).

Slice 1 (merged as #30) adopted **combine** and **validate**. Slice 2a installs the
newly merged **convert** module and runs its parity check: convert is now **pinned and
tested**, but its callers are **not migrated** — the parity result is partial coverage
(see the convert contract table), so `FHR_CONVERT` stays the callers' module and the
naming/format questions are recorded as blockers with a maintainer decision ask.
**verify** is unchanged and still not adopted: nf-core/modules#13635 remains open as of
2026-11-12, and adoption of anything is gated on merge **plus** local parity checks
(section "Adopting verify and convert after their merge").

## How the upstream modules are pinned

- `modules/nf-core/fairbioheaders/combine/`, `modules/nf-core/fairbioheaders/validate/`
  and `modules/nf-core/fairbioheaders/convert/` (including `.conda-lock/`, `meta.yml`,
  `environment.yml`, tests and snapshots) are
  **byte-identical copies** of the upstream files at the recorded revisions.
  They must stay unpatched: repository behavior goes into repository-owned
  modules (`modules/*`) or subworkflows (`subworkflows/*`), never into the pinned
  copies.
- `modules.json` uses the nf-core/tools manifest schema: remote
  `https://github.com/nf-core/modules.git`, then `modules.nf-core`, then each
  `fairbioheaders/<name>` entry with `branch`, `git_sha` and
  `installed_by: ["modules"]`. `.nf-core.yml` declares `repository_type: pipeline`.
- The repository still has a mixed module layout: repository-owned modules live
  under `modules/*`, including local verify in the `nf-core` namespace. nf-core
  4.2.2 rejects those untracked directories. A valid manifest alone does **not**
  make `nf-core modules update`, `list local` or `lint` usable here. Use the
  CLI-less procedure below until a separate layout migration moves local modules
  to `modules/local/` and updates every importer. That migration remains #29 work.
- CI runs `python3 scripts/check_upstream_modules.py`. It iterates **every entry of
  `modules.json`**, retrieves the complete recursive GitHub tree at each pin with
  `curl --retry 3`, rejects truncated responses, and compares all module-relative
  paths, blob hashes and file modes. Hidden lock files, missing files and extra local
  files are included. Any drift fails the job before nf-test runs. Because the guard is
  manifest-driven, installing a module adds it to the drift check automatically: it now
  covers combine (7 files), validate (7) and convert (8 — convert also ships
  `tests/nextflow.config` for its `ext.args`/`ext.prefix` cases).

Provenance of the runtime/test files (the complete directory for each pinned module
also includes the two `.conda-lock/` platform locks, verified by CI; combine and
validate hold seven files each, convert eight because it also ships
`tests/nextflow.config`):

| Module @ revision | File | Upstream blob sha |
| --- | --- | --- |
| combine @ `8faff340…` | main.nf | `c0ab92a8870cb6559831b4e97b4398d86e6d94dc` |
| combine @ `8faff340…` | meta.yml | `46bc346cde2ece850d0908aecbd2018d0c26510e` |
| combine @ `8faff340…` | environment.yml | `d0c0735cb08e0a193ca197dc24ca046d2e6c2cc8` |
| combine @ `8faff340…` | tests/main.nf.test | `12929b19472353afe08c436aa6060d11603b54de` |
| combine @ `8faff340…` | tests/main.nf.test.snap | `9b5315d19c16bedd74290ae543af29077ad05661` |
| validate @ `86e852ef…` | main.nf | `95f0dc9fe3e00fa5e6f43e2b93766413820367a4` |
| validate @ `86e852ef…` | meta.yml | `00142fe21147bb05cbd7204110c36a713b398561` |
| validate @ `86e852ef…` | environment.yml | `d0c0735cb08e0a193ca197dc24ca046d2e6c2cc8` |
| validate @ `86e852ef…` | tests/main.nf.test | `10a065dfaa3e2b87951bf477a1a1a2d6a628ad82` |
| validate @ `86e852ef…` | tests/main.nf.test.snap | `00026dfbe88f2b86155ad17276d90bb92e16c8e1` |
| convert @ `4dc3bc5477…` | main.nf | `cbf0d43c8552e4ecf231f171c1117fc8251c00f0` |
| convert @ `4dc3bc5477…` | meta.yml | `357ef5e80a7ac9fd318827a8d0105b4e43c4924e` |
| convert @ `4dc3bc5477…` | environment.yml | `d0c0735cb08e0a193ca197dc24ca046d2e6c2cc8` |
| convert @ `4dc3bc5477…` | tests/main.nf.test | `708785efbfde32aa87884fd9a725dc9e0e0bb6cf` |
| convert @ `4dc3bc5477…` | tests/main.nf.test.snap | `261014efe7e2c4c95c291a78917471a968cddb5b` |
| convert @ `4dc3bc5477…` | tests/nextflow.config | `3bf6653083dee274273e4f72bbe61db2f5d4874d` |
| convert @ `4dc3bc5477…` | `.conda-lock/linux_amd64-bd-71029206d3ce1119_1.txt` | `614f61ced8ebef6dc1a6e78742a2f0672b805031` |
| convert @ `4dc3bc5477…` | `.conda-lock/linux_arm64-bd-1ff11621d7e9a7c8_1.txt` | `8cc63c8d8b1d37b467b2074e22af63c10a61a6fa` |

### Updating a pinned module (recorded procedure)

Use the CLI-less procedure from this repository root. First review the diff
between the recorded SHA and the proposed merged SHA, restricted to the module
directory. Download **every blob**, including hidden files, from that revision:

```sh
python3 - fairbioheaders/combine <reviewed-merge-sha> <<'PYUPDATE'
import json
from pathlib import Path
import subprocess
import sys

name, sha = sys.argv[1:]
prefix = f"modules/nf-core/{name}/"
tree = json.loads(subprocess.check_output([
    "gh", "api", f"repos/nf-core/modules/git/trees/{sha}?recursive=1"
]))
assert not tree.get("truncated"), "Incomplete upstream tree"
files = [entry for entry in tree["tree"]
         if entry["path"].startswith(prefix) and entry["type"] == "blob"]
assert files, "Module absent at the proposed revision"
for entry in files:
    path = Path(entry["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    content = subprocess.check_output([
        "curl", "--fail", "--silent", "--show-error", "--location", "--retry", "3",
        f"https://raw.githubusercontent.com/nf-core/modules/{sha}/{path.as_posix()}"
    ])
    assert entry["mode"] in ("100644", "100755"), "Review special file manually"
    path.write_bytes(content)
    path.chmod(0o755 if entry["mode"] == "100755" else 0o644)
    got = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    assert got == entry["sha"], str(path)
manifest = Path("modules.json")
data = json.loads(manifest.read_text())
data["repos"]["https://github.com/nf-core/modules.git"]["modules"]["nf-core"][name]["git_sha"] = sha
manifest.write_text(json.dumps(data, indent=4) + "\n")
PYUPDATE
python3 scripts/check_upstream_modules.py
```

Repeat for each module being installed or updated (`fairbioheaders/validate`,
`fairbioheaders/convert`). For a first install the same script creates the
`fairbioheaders/<name>` manifest entry (`branch`, `git_sha`, `installed_by`) shown
above. Review and remove any obsolete
tracked files reported as `extra` by the guard; never leave stale files in a
pinned directory. Keep the module's Conda/container pins coherent with this
repository's toolkit baseline (currently 0.9.0). Run the suites below and commit
the complete directory, manifest change and updated provenance table together.

After the separate local-layout migration, the nf-core CLI update procedure can
be enabled and tested with the then-supported nf-core/tools version. Until then,
run module lint in a clean upstream nf-core/modules checkout at the recorded
revision, rather than invoking it in this mixed-layout repository.

## Contract comparison, upstream vs local (pre-migration)

Legend: **matches** = same observable contract; **differs** = behavior/contract
change if callers switch; the *Verdict* line states whether the shared module
covers the repository's documented callers.

### `fairbioheaders/combine` (upstream `8faff340`) vs `FHR_COMBINE` (was `FAIRBIOHEADERS_COMBINE`, local)

| Aspect | Upstream @ `8faff340` | Local (pre-migration) | Verdict |
| --- | --- | --- | --- |
| Input | `tuple val(meta), path(metadata), path(sequence)` | same tuple shape | matches |
| `sequence` output | `tuple val(meta), path("${prefix}.${extension}")` — the output **keeps the input file's extension** (`test.fasta`, `test.faa`, `test.fasta.gz`) | `tuple val(meta), path("${prefix}.fh*")` — output **named by header type**: `ID.fhr.fa`, `ID.fhr.gfa`, `ID.fhp.faa`, `ID.fhgff3.gff3` (+`.gz` when input compressed), derived from the metadata's `schema` URL via the toolkit's own `bioheaders.header_type` inside the task | **differs — the decisive gap** |
| Header-type detection | none in the module (the toolkit still rejects a header type the file type cannot carry, e.g. FHP on GFA) | runs `bioheaders convert --to json` + `bioheaders.header_type` to pick the `fhr`/`fhp`/`fhgff3` name segment and the `faa` vs `fa` extension | differs |
| `--type` | not passed; toolkit infers the format from the extension (0.8.6+ also infers `.fas`/`.ffn`/`.frn`/`.fsa`/`.mpfa`) | explicit whitelist: `.gfa→gfa`, `.gff/.gff3→gff3`, anything else→`fasta` | differs (upstream accepts a broader FASTA set; local rejects unknown extensions earlier and deterministically) |
| Compression | `.gz`/`.bgz` inputs give BGZF output named `…ext.gz` (last two name tokens kept) | same, via `.b?gz` regex | matches |
| Overwrite collision | possible when `prefix.extension` equals a staged input name — meta.yml documents the failure ("set `ext.prefix` in that case"); a default `id` derived from the file name can hit this | impossible by construction (`ID.fhr.fa` differs from the input file) | differs |
| Shell hardening | relies on Nextflow's interpolation of staged paths; `prefix` (a raw string) is **not** quoted | single-quotes staged paths, `meta.id` and the output name (`quote` closure) | differs (hardening; see SECURITY-style guidance in AGENTS.md: "Quote staged paths") |
| Supported formats | FASTA (`.fa/.fasta/.fna/.fas/.faa/.ffn/.frn/.fsa/.mpfa`), GFA, GFF3, plain/gzip/BGZF (meta.yml) | FASTA/FAA, GFA, GFF3 (meta.yml pattern is narrower) | superset upstream |
| Checksum semantics | computed by `bioheaders combine` over the exact attached-file bytes; supplied checksum replaced | identical (same command) | matches |
| Failure semantics | task fails on invalid metadata, header/file-type mismatch, unsupported extension, output-collides-with-input | task fails on invalid metadata, header/file-type mismatch, unsupported extension (type whitelist) | matches except the collision case |
| Sample metadata | `meta` preserved on `sequence`; `meta.id` names outputs; `ext.prefix` overrides | same | matches |
| Conda | `${moduleDir}/environment.yml`, `bioconda::fair-bioheaders=0.9.0` | same pin (unquoted line) | matches (content) |
| Container | Seqera Wave `community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119` (+ `community-cr-prod` blob URL for Singularity) | BioContainers `quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0` + Galaxy depot pair | **differs — pins reconciled, registries not** (see "Containers and conda") |
| Version reporting | `(task.process, 'fair-bioheaders', bioheaders --version)` on topic `versions` + named emit | identical | matches |
| Stub | touches `${prefix}.${extension}` (gzip echo for compressed) | family-named stub outputs | differs (mirrors the output-name gap) |
| nf-tests | 8 cases (fasta, fasta.gz, gfa, faa-fhp, gff3-fhgff3, fhp-on-gfa-fails, 2 stubs), fixtures from nf-core/test-datasets, snapshots recorded under Nextflow 26.10.4 / nf-test 0.9.5 | 9 cases incl. **FHP on gzipped protein `.fasta` → `ID.fhp.faa`** (the family-naming behavior) with inline fixtures | upstream covers the tool; local covers the naming contract |

**Verdict: partial coverage.** Upstream combine performs the same toolkit
operation with the same checksum/failure semantics, but it does not reproduce the
suite's documented *header-family output naming*, changes the overwrite-collision
and quoting behavior, and widens the extension set. The three callers that publish
or assert family names therefore **cannot switch yet**; they moved to the
repository-owned compatibility module `modules/combine/main.nf` (`FHR_COMBINE`,
verbatim copy of the pre-migration implementation plus the MPL header), and the
canonical `modules/nf-core/fairbioheaders/combine/` is now purely the pinned
upstream artifact with upstream tests. Removing `modules/combine/` requires
resolving the gaps below (blockers):

1. **Naming contract (blocker).** Decide between (a) adopting the upstream
   extension-preserving names in the next minor with migration notes (touches
   `README`/`docs/PIPELINES.md`/the Dockstore README tables, the CI example
   assertions `example.fhr.fa`/`example.fhr.gfa`/`protein-metadata.fhp.faa`/
   `results/combine/protein.fhp.faa`, the `tests/run.py` markers
   `attached-fasta.fhr.fa`, `ATTACHED … .fhp.faa`, etc., and the `FHR_ATTACH`
   documented outputs), or (b) an upstream change (e.g. an `ext` hook or an
   option for family naming) in a follow-up PR to nf-core/modules. The AGENTS.md
   #21 consolidation decision ("protein FASTA as `.fhp.faa`") stays in force
   until a maintainer decision changes it.
2. **Quoting/hardening parity (blocker for direct importers).** Callers that pass
   user-supplied `ext.prefix` or unsafe `meta.id` values relied on the local
   quoting. Callers must constrain IDs before invoking the upstream module —
   `FHR_ATTACH`/the example already do (`isSampleId`), so the practical exposure
   is limited to external direct importers; documented in PIPELINES.
3. **Collision semantics (note).** Any future caller switch must set `ext.prefix`
   or use IDs that cannot collide with the staged input name (upstream meta.yml
   documents the failure).

### `fairbioheaders/validate` (upstream `86e852ef`) vs local `FAIRBIOHEADERS_VALIDATE`

| Aspect | Upstream @ `86e852ef` | Local (pre-migration) | Verdict |
| --- | --- | --- | --- |
| Input | `tuple val(meta), path(metadata)` | same | matches |
| Output | `tuple val(meta), path("${prefix}.validate.txt")`, emit `report` | `path("*.validate.txt")` (same single file) | matches |
| Role separation | standalone metadata only; no sequence, no checksum check; meta.yml explicitly redirects headed files to `fairbioheaders/verify` | same separation | matches |
| Formats | JSON, YAML, JSON-LD (`.json/.yaml/.yml/.jsonld`; `ext.args` can pass `--from`) | JSON/YAML (+`--from` via args) | superset upstream |
| Failure semantics | schema-invalid metadata or an unbundled schema version → non-zero exit fails the task; report keeps `file: <path>` + validator output | identical script structure (group redirect, not pipe) | matches |
| Report content | `file: <staged path>` + `bioheaders validate` stdout | same | matches |
| Shell hardening | prefix unquoted; staged path by Nextflow interpolation | quotes path, report name and `meta.id` | differs (same caveat as combine; this repo's callers stage validated IDs) |
| Conda | `bioconda::fair-bioheaders=0.9.0` | same | matches |
| Container | Wave `fair-bioheaders:0.9.0--71029206d3ce1119` | quay/depot `0.9.0--pyhdfd78af_0` | differs (registries only; see below) |
| Version reporting | identical | identical | matches |
| Stub | `touch ${prefix}.validate.txt` | same | matches |
| nf-tests | 7 cases (FHR yaml/json, FHP yaml, FHGFF3 yaml, missing-field fails, unsupported-schema fails, stub) | 9 cases — **plus FHR 2.1 `x-` extension-field accept and FHR 2.0 `x-` reject** | upstream lacks the 2.1 cases |

**Verdict: full coverage of callers; migrated in place.** `FHR_CREATE_JSON`
(which gates created JSON through `FAIRBIOHEADERS_VALIDATE` by a meta join) and
the external-project harness calls keep working unchanged: the input/output
tuples, the report name `ID.validate.txt`, the report content and the failure
messages are identical, and the file names those callers stage are ID-constrained
and space-free, so the quoting difference is not observable there. The two local
test cases the upstream revision does not carry (FHR 2.1 `x-` fields) were
**ported into `tests/run.py`** so the coverage is not dropped.

### `fairbioheaders/verify` — upstream PR #13635 (open) vs local `FAIRBIOHEADERS_VERIFY` (kept)

Not adopted (gated on the open PR). **Re-verified 2026-11-12: still open, and nothing
about this module changed in slice 2a** — only the table's revision column above was
refreshed (the head moved `bb6c492` → `bc5a8640`, so the comparison below still describes
the 2026-11-10 review head and must be re-diffed at merge time). Contract differences
between the local module and the PR head reviewed on 2026-11-10 (`bb6c492`, a moving
branch — re-diff at merge time):

| Aspect | Upstream PR head | Local | Notes for the later adoption |
| --- | --- | --- | --- |
| Input/output | `(meta, sequence)` → `(meta, ${prefix}.verify.txt)` + versions | same (glob vs prefix) | matches |
| `--type` | **not passed** (toolkit infers from extension) | explicit `fasta`/`gfa`/`gff3` whitelist | adoption must re-check rejection messages for odd extensions; `tests/run.py` asserts on `checksum`, `after sequence data`, `duplicate key`, `proteome` — toolkit messages, inferred `--type` does not change those, but unknown extensions now fail in the toolkit instead of being forced to `--type fasta` |
| Compression | same `.gz/.bgz` handling | same | matches |
| Quoting | prefix double-quoted at redirect; staged path by interpolation | full single-quote closure on path, prefix, `meta.id` | PR adds a *spaced names* test (`test sample.fasta` → `test sample.verify.txt`) as the upstream hardening evidence |
| Failure semantics | schema/checksum failure fails the task; report `file: …` + validator output | identical | matches |
| Containers | Wave | quay/depot | same 0.9.0 content |
| nf-tests | 10 cases incl. spaced names, changed-after-combine, combined with upstream `FAIRBIOHEADERS_COMBINE` in `setup` | 5 cases (fasta.gz, faa-fhp, gff3, no-header-fails, stub), fixtures inline | PR tests depend on the *upstream combine* outputs (extension-preserving names) — re-verify the local `FHR_ATTACH` join-based flow after adoption. The local test's combine setups were retargeted to `modules/combine` (`FHR_COMBINE`) in this slice because their assertions rely on the header-family names |
| Role separation | verifies headed sequence files (schema + checksum), never parent links; standalone JSON → validate | same | matches |

`subworkflows/attach` and the Dockstore workflow keep consuming the local module
at `modules/nf-core/fairbioheaders/verify/` **migration-pending**; `FHR_VERIFY_LINKS`
(parent links, `bioheaders verify-links`) stays repository-owned — upstream has no
parent-link module.

### `fairbioheaders/convert` (upstream `4dc3bc5477`, merged 2026-11-11) vs `FHR_CONVERT` (local)

**Installed and tested; callers NOT migrated.** Re-read at the merge commit, not at the
review head this document described on 2026-11-10 (`639dd3c`). The merged revision moved
against that head in four ways that matter here: the default prefix became
`${meta.id}_converted` (it was `${meta.id}`); the output redirect is **no longer quoted**
(`${prefix}.${format}` in both `script` and `stub`, where the head had
`"${prefix}.${format}"` and the comment "Nextflow already shell-escapes staged inputs, so
only the prefix is quoted"); an explicit `Input and output names are the same, set prefix
in module configuration to disambiguate!` guard was added; and both *spaced names* tests
were replaced by *same input and output names fails* tests (still 11 cases, 8 snapshot
entries).

| Aspect | Upstream @ `4dc3bc5477` | Local `modules/convert` | Verdict |
| --- | --- | --- | --- |
| Input | two rows: `tuple val(meta), path(input)` **and** `val(format)`; call as `FAIRBIOHEADERS_CONVERT(pathChannel, formatChannel)`. Under the syntax parser this repository pins for the harness (`NXF_SYNTAX_PARSER=v2`), passing one flattened channel is rejected instead: `Incorrect number of call arguments, expected 2 but received 1` | single tuple `(meta, metadata, format)`, `stageAs: 'input/*'` | **differs — channel-contract break** for every `FHR_CONVERT` importer and call site |
| Output name | `(meta, ${prefix}.${format})`, `prefix = task.ext.prefix ?: "${meta.id}_converted"` | `(meta, ${meta.id}.fhr.${format})` | differs by default; **closable** — with `ext.prefix = { "${meta.id}.fhr" }` the pinned module emitted `parity-json.fhr.json`, `parity-yaml.fhr.yaml`, `parity-html.fhr.html` and `parity-extract.fhr.json`, byte-identical to `FHR_CONVERT` (asserted in `tests/run.py`) |
| Format tokens | `--to <format>`: the toolkit accepts `fasta gfa gff3 html json jsonld yaml`; meta.yml documents `json yaml jsonld html` | native whitelist `json yaml html fasta faa gfa` (`fhrFormat`) | **differs — the decisive gap.** The format token **is** the output extension and `--to faa` does not exist (`bioheaders convert --to faa` exits 2 with `invalid choice: 'faa'`), so a header-only **protein** output cannot be named `.faa`: the probe produced the same bytes as `FHR_CONVERT`'s `parity-faa.fhr.faa` under the name `parity-faa.fhr.fasta`. Upstream adds `jsonld` (and, undocumented, `gff3`); local keeps `faa` and has no `jsonld` |
| Header extraction | documented use: read the sidecar header of a combined FASTA/GFA/GFF3 back to JSON/YAML | the same, as `FHR_ATTACH`'s JSON-extraction step | matches (probe `extract`: identical bytes, same name under `ext.prefix`) |
| Unknown/unsupported format | fails **inside the task**: `bioheaders convert: error: argument --to: invalid choice: 'exe' …` (probe asserts the same for `faa`) | rejected **before submission**: `Unsupported format 'exe'; expected json, yaml, html, fasta, faa, gfa` (the harness case above) | differs — the failure surface moves; a direct importer loses the pre-launch whitelist |
| Command | `bioheaders convert ${args} --to <format> <input> <output>`; `--to` last, so the format channel beats `ext.args` (upstream test `ext.args --to overridden`) | `fhr-convert <input> <output>` (legacy entry point, extension inference); no `--to`, no `ext.args` | differs (upstream is the current CLI plus `ext.args`; local relies on the output extension) |
| Overwrite collision | `error` when `${input}` equals `${prefix}.${format}` (two upstream tests) | impossible by construction (`stageAs: 'input/*'` plus the `.fhr.` infix) | differs (guard vs structure); our `ext.prefix = "${meta.id}.fhr"` naming never collides |
| Shell hardening | prefix **unquoted** in script and stub; staged path by Nextflow interpolation | single-quotes path, output name and `meta.id` (`quote`) | differs — the merged revision is weaker than the head reviewed on 2026-11-10. Probe: a `"metadata with ' quotes.json"` input reads correctly through the pinned module (Nextflow escapes staged paths), so the remaining exposure is a caller-supplied `ext.prefix`/unsafe `meta.id`, exactly the combine/validate caveat |
| `when` | `task.ext.when == null \|\| task.ext.when` | none | differs (upstream adds the standard opt-out) |
| Sample metadata | `meta` preserved, `meta.id` names outputs, `ext.prefix` overrides | same, with `sampleId(meta)` validation | matches (modulo ID validation) |
| Conda | `bioconda::fair-bioheaders=0.9.0` | same pin | matches |
| Container | Wave `community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119` (+ `community-cr-prod` blob URL for Singularity) | `quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0` + Galaxy depot pair | differs — pins reconciled, registries not (same as combine/validate; see "Containers and conda") |
| Version reporting | `(task.process, 'fair-bioheaders', bioheaders --version)` on topic `versions` + named emit | identical | matches |
| Stub | `touch ${prefix}.${format}` plus the collision guard | family-named stub outputs | differs (mirrors the naming gap) |
| nf-tests | 11 cases (fasta, fasta.gz, gfa→json, faa→jsonld, gff3→yaml, yaml→json, `--to` overridden, no-header fails, name-collision fails, 2 stubs); fixtures from nf-core/test-datasets; snapshots recorded under Nextflow 26.10.4 / nf-test 0.9.5 — all 11 passed here on 26.04.6 / 0.9.5 with `--ci` | no nf-test file; behavior is covered by the `tests/run.py` round trips and markers | upstream covers the tool, local covers the family contract; `tests/run.py` now also keeps the spaced/quoted-name case the merged revision dropped |

**Verdict: partial coverage → pinned, tested, not migrated.** The convert serialization
work itself is fully equivalent — same bytes for JSON, YAML, HTML and header extraction,
and the `.fhr.` infix is reproducible from the importing project with one `ext.prefix`
line. What is **not** reproducible inside the upstream contract is the
header-family/extension convention this suite publishes, so migrating the example's YAML
step, `FHR_ATTACH`'s extraction step and the external harness markers would be an
observable contract change, not a retarget.
`modules/convert` (`FHR_CONVERT`) therefore stays the callers' module — exactly slice 1's
`FHR_COMBINE` treatment — and `modules/nf-core/fairbioheaders/convert/` is now purely the
pinned upstream artifact with its own tests. Removing `modules/convert` requires these
(blockers):

1. **Family-name default (blocker, shared with combine blocker 1).** `ID.fhr.<format>` is
   a documented external marker (`EXTRACTED {sample} {sample}.fhr.json`,
   `example/sequence/example.fhr.json`, `{sample}-header.fhr.faa`, README's
   `output_format` list), while upstream defaults to `<id>_converted.<format>`. Either the
   suite adopts the upstream default and rewrites those markers in a documented minor
   release, or the family-standard question recorded under "Open questions" gets settled
   upstream (a family-signifying default or an `ext` hook) and both modules retire their
   compat copies together. `ext.prefix = { "${meta.id}.fhr" }` is the interim recipe and
   is now verified by the harness rather than asserted in prose.
2. **Protein extension `faa` (blocker).** Because the upstream output extension is the
   `--to` token and the toolkit has no `faa` choice, `fairbioheaders/convert` cannot name
   a header-only protein output `ID.fhr.faa`. Options: (a) an upstream follow-up that
   decouples the output extension from `--to` (or accepts `faa` as a FASTA alias), (b) the
   suite renames protein header-only outputs to `.fhr.fasta`, which costs the
   protein/genome distinction the suite's own `sequenceKindOf` reads from the extension,
   or (c) `FHR_CONVERT` stays. **Maintainer decision needed** — this is convert-specific
   and does not follow automatically from resolving combine's naming blocker.
3. **Two-row input shape (blocker for a caller switch).** Mechanical at our two workflow
   call sites (`main.nf`'s YAML step and `FHR_ATTACH`'s extraction step; the harness
   scripts that include the module directly follow the same rewrite — pair a
   `(meta, file)` channel with a channel of format values), but it breaks every external
   importer's wiring, and README's contract table documents the three-element tuple. It
   should move with blocker 1 in one documented release, not before it.
4. **Quoting and rejection surface (note).** The merged module leaves the prefix unquoted
   and reports an unusable format from inside the task instead of before submission; the
   suite's own callers stage ID-constrained names, so nothing here breaks, but direct
   importers must constrain `meta.id`/`ext.prefix` ([docs/PIPELINES.md](PIPELINES.md#nf-core-style-modules)
   already says this for combine/validate, and the harness now pins the exact upstream
   messages).


## Role separation (kept explicit)

| Job | Module | Owner |
| --- | --- | --- |
| Attach metadata + exact-byte checksum (`bioheaders combine`) | `FAIRBIOHEADERS_COMBINE` (pinned upstream), `FHR_COMBINE` (compat, family names) | upstream + repo |
| Verify a **headed sequence file** (schema + checksum of the file) | `FAIRBIOHEADERS_VERIFY` | repo, migration-pending |
| Validate **standalone metadata** (schema only, no checksum/sequence) | `FAIRBIOHEADERS_VALIDATE` (pinned upstream) | upstream |
| Verify **parent links** (`derivedFrom`/`genomeReference` against candidate parents, `bioheaders verify-links`) | `FHR_VERIFY_LINKS` | repo-owned, no upstream counterpart |
| GFF3 syntax/SO/biology rules | `GFF3_VALIDATE` (gff3-validator 0.1.0) | repo-owned, no upstream counterpart |
| Metadata conversion / header extraction (`fhr-convert`) | `FHR_CONVERT` (compat), `FAIRBIOHEADERS_CONVERT` (pinned upstream) | repo + upstream |
| Native JSON creation, stripping, converter pytest gating | `FHR_CREATE_JSON`, `FHR_STRIP`, `FHR_CONVERTER_TESTS` | repo-owned |

## Caller migration status

| Caller | Uses | Status |
| --- | --- | --- |
| Standalone example `main.nf` | `FHR_ATTACH` → `FHR_COMBINE` + local `FAIRBIOHEADERS_VERIFY`; `FHR_CREATE_JSON` → pinned `FAIRBIOHEADERS_VALIDATE`; `FHR_CONVERT` for the published YAML | combine/verify/convert held on compat (naming gaps); **validate migrated** |
| `subworkflows/attach` (`FHR_ATTACH`) | `FHR_COMBINE` + `FAIRBIOHEADERS_VERIFY` + `FHR_CONVERT` | external channel contract and output names unchanged; internals retargeted to the compat combine; the JSON-extraction step stays on `FHR_CONVERT` (blockers 1–3 above) |
| Dockstore workflow `workflows/fairbioheaders` | `FHR_COMBINE` + `FAIRBIOHEADERS_VERIFY` | outputs (`combine/<id>.fhr.fa`, `combine/<id>.fhp.faa`, `verify/<id>.verify.txt`) unchanged; descriptor `.dockstore.yml` paths unchanged and still resolve; the workflow does not call convert |
| `modules/create_json` | pinned `FAIRBIOHEADERS_VALIDATE` | migrated in place |
| External direct importers | `modules/nf-core/fairbioheaders/{combine,convert,validate,verify}` | **combine's and convert's observable naming contracts differ from the repository modules at the canonical paths** — see the two migration notes below |

**Migration note for direct importers of
`modules/nf-core/fairbioheaders/combine`:** the module at this path is now the
upstream nf-core module. Its `sequence` output is named
`<prefix>.<input extension>` (e.g. `sample.fasta`, `sample.faa`,
`sample.gff3.gz`) instead of the header-family names (`sample.fhr.fa`,
`sample.fhp.faa`, …), it does not pass `--type`, and it can fail when the derived
output name would overwrite a staged input. Importers that depend on family
names should either import `modules/combine` (`FHR_COMBINE`) or wrap the upstream
module and rename from their own contract; `FHR_ATTACH` already composes the
compat module and needs no change.

**Migration note for direct importers of
`modules/nf-core/fairbioheaders/convert`** (installed in slice 2a at
`4dc3bc5477`): this is the upstream module, so it takes **two input rows**
(`(meta, file)` plus a separate format value channel), names its output
`<meta.id>_converted.<format>` unless `ext.prefix` says otherwise, and offers the
toolkit's `--to` set (`json`, `yaml`, `jsonld`, `html`, plus `fasta`/`gfa`/`gff3`
through the toolkit) with **no `faa` token**. Emitting this repository's documented
names is a configuration step, not a code change —

```nextflow
process {
    withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { "${meta.id}.fhr" } }
}
```

which the harness verifies produces byte-identical output to `FHR_CONVERT` for
`json`/`yaml`/`html` and for header extraction. Protein header-only outputs
(`ID.fhr.faa`) and the pre-launch format whitelist stay with
`modules/convert` (`FHR_CONVERT`) until the blockers recorded in the convert
contract table are resolved.

## Containers and conda pins (reconciled)

- The toolkit pin itself is unchanged everywhere: `bioconda::fair-bioheaders=0.9.0`
  in every `environment.yml`, matching the repo baseline (#27) and the hash-locked
  `environment/requirements.txt`.
- Pinned upstream modules run the **Seqera Wave** image
  `community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119`
  (Singularity via the matching `community-cr-prod.seqera.io` blob URL), which
  nf-core generates from the same Bioconda 0.9.0 environment. The repository-owned
  modules keep the BioContainers/Galaxy-depot pair
  (`quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0`,
  `depot.galaxyproject.org/singularity/fair-bioheaders:0.9.0--pyhdfd78af_0`)
  per the #21 conventions. Both image families carry fair-bioheaders 0.9.0; the
  versions reported on the `versions` topic are identical.
- Consequence: a Docker/Singularity run now pulls two registries (quay.io and
  community.wave.seqera.io) instead of one, e.g. `main.nf -profile docker`
  validates created JSON in a Wave container and combines in a BioContainers
  container. Offline mirrors that whitelist registries must add
  `community.wave.seqera.io`. CI checks each family against the Bioconda pin
  in its own style.

## Testing status for slice 1 (2026-11-10) and commands CI/maintainers must run

Host environment: Docker 29.9.3 available; **no** host `nextflow`, `nf-test`, `nf-core`
CLI or Java runtime. All Nextflow execution in this slice therefore ran inside a
reproducible verification container (`FROM nextflow/nextflow:26.04.6`, Amazon Linux
2023 with Java 21 — the CI baseline — plus a python3.11 venv with pytest,
`fair-bioheaders==0.9.0`, `gff3-validator==0.1.0` and `pyld`, and nf-test 0.9.5),
with the repository's processes executing **natively** against the pinned toolkit
under linux/amd64 emulation. That verifies scripts, channel wiring, snapshots and
toolkit semantics; it does NOT exercise container runtime pins, which the
`-profile docker` CI jobs verify.

Executed here:

- `nf-test test --ci` — **29/29 passed** in 788 s: the pinned upstream combine
  suite (8 tests, fetching the merged nf-core/test-datasets#2363 fixtures at
  runtime), the pinned upstream validate suite (7), the local
  `FAIRBIOHEADERS_VERIFY` suite (5, setups retargeted to `FHR_COMBINE`) and the
  moved `FHR_COMBINE` compatibility suite (9). Committed snapshots matched
  (CI mode fails on any snapshot mismatch) under Nextflow 26.04.6 / nf-test 0.9.5
  even though upstream recorded theirs under 26.10.4 (snapshot content is
  version-agnostic apart from the reported toolkit version, 0.9.0).
- `python tests/run.py --converter-source <v0.9.0 checkout>` — **57/57 harness
  runs and rejection cases passed**, including the two new FHR 2.1 `x-` extension
  validate cases against the pinned upstream module and the FHR genome → FHGFF3
  annotation → FHP protein parent-chain cases; the converter-test gate ran the
  toolkit's own pytest suite (**2410 tests**) and the injected-failure, `-resume`
  and version-mismatch rejection cases behaved as documented.
- `nextflow run workflows/fairbioheaders/main.nf -profile test` — **passed**: the
  five samplesheet rows produced the family-named combine outputs
  (`fasta.fhr.fa`, `gfa.fhr.gfa`, `gff3.fhgff3.gff3`, `jsonld.fhr.fa`,
  `protein.fhp.faa`) and five `Checksum verified.` verify reports, covering FHR
  FASTA/GFA, expanded JSON-LD metadata, FHGFF3 and FHP through the migrated
  wiring.

Commands still required from a maintainer/CI machine with Docker (the branch must
be green there before merge; the native runs cannot exercise container image
pulls):

```sh
nf-test test --profile docker --ci            # same suites with the Wave/BioContainers images pulled
python tests/run.py --converter-source <fair-bioheaders-0.9.0-checkout>
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results   # family-named combine outputs + verify reports
nextflow run main.nf -profile docker --sequence examples/assembly.gfa --sequence_format gfa   # and the FASTA/GFF3/protein examples as in ci.yml
docker build -t fhr-nextflow:0.1.0 environment
git diff --check
```

Module lint requires a clean upstream nf-core/modules checkout at the recorded
revision; see the layout limitation above.

FHR → FHGFF3 → FHP parent-chain coverage was re-checked in the form this slice
can verify locally: the chain fixtures (`tests/fixtures/fhp/chain/`), the
`FHR_VERIFY_LINKS` harness cases and the protein attach markers in
`tests/run.py` are unchanged and still exercise combine→verify→extract→verify-links
through the compat module; the chain does not depend on the pinned validate module
for parent checks.

## Testing status for slice 2a (2026-11-12)

Same host and method as slice 1 (Docker 29.9.3; no host `nextflow`, `nf-test`,
`nf-core` or Java): the repository's processes ran **natively** inside a
reproducible verification container built for this slice —
`fhr-nf29-verify:26.04.6`, `FROM nextflow/nextflow:26.04.6` (Amazon Linux 2023,
Java 21, the CI baseline), `python3.11` venv with `fair-bioheaders==0.9.0`,
`gff3-validator==0.1.0`, `pytest` and `pyld`, plus nf-test 0.9.5, on the
linux/amd64 emulation of an arm64 host. Its Dockerfile is a verification artifact,
not repository content. As in slice 1 this exercises scripts, channel wiring,
snapshots and toolkit semantics, not the container-image pulls.

- **Merged-revision fetch:** all eight upstream files were downloaded at
  `4dc3bc54779d6caf3a47d49f37811e651fa2700a` and each `git hash-object` matched the
  blob sha in the (untruncated) recursive GitHub tree — the same check the recorded
  update procedure performs. `python3 scripts/check_upstream_modules.py` then
  reported `combine: all 7 files match 8faff340…`, `validate: all 7 files match
  86e852ef…` and `convert: all 8 files match 4dc3bc54…`; `python3 -m unittest
  discover -s tests -p test_upstream_modules.py` stays green (2 tests). CI's
  Wave/BioContainers pin step was extended to `for module in combine validate
  convert` and run locally: it passes.
- **`nf-test test --ci` — 40/40 passed** in 1261 s: the 11 upstream convert tests
  (5 conversion cases, `ext.args --to overridden`, no-header failure, two
  name-collision failures, 2 stubs) joined the 29 slice-1 tests. Committed
  snapshots — recorded upstream under Nextflow 26.10.4 / nf-test 0.9.5 — matched in
  CI mode under Nextflow 26.04.6 / nf-test 0.9.5, as they did for combine and
  validate.
- **Contract probe (`tests/run.py`, four new cases):** `FHR_CONVERT` and the pinned
  `FAIRBIOHEADERS_CONVERT` ran side by side over five records (JSON, YAML, HTML,
  metadata→FASTA and header extraction from the chain fixture's combined FHP
  `protein.fhp.faa`). With `ext.prefix = { "${meta.id}.fhr" }` set in the harness
  project's config, all four family-named serializations came out with the **same
  file name and identical bytes** as `FHR_CONVERT`; the protein record came out
  byte-identical but named `parity-faa.fhr.fasta` upstream versus
  `parity-faa.fhr.faa` locally, and `--to faa` fails in the task
  (`invalid choice: 'faa'`), as does `--to exe`. A metadata file named
  `metadata with ' quotes.json` converts correctly through the pinned module
  (`spaced_converted.json`, JSON equal to the input), so the unquoted prefix remains
  a caller-discipline caveat rather than a demonstrated break.
- **`python tests/run.py --converter-source <v0.9.0 checkout>` — 61/61 passed** (slice
  1's 57 plus the four cases above; the checkout is CI's `CONVERTER_COMMIT` `c6d7454`,
  exported from the local Tools clone's `v0.9.0` tag). The converter-test gate ran the
  toolkit's own **2410** pytest tests, and the injected-failure, `-resume` and
  version-mismatch rejections behaved as documented. The FHR → FHGFF3 → FHP chain cases
  and the `FHR_CONVERT`-backed example/protein runs are unchanged by this slice: no caller
  moved, so their markers still pass. This pass was repeated once against the completed
  tree (only documentation and module comments differed) and again reported
  **61/61**.
- **Not re-run here (unaffected, CI covers it):** the Dockstore workflow's `test` profile
  (`workflows/fairbioheaders` composes `FHR_COMBINE` + `FAIRBIOHEADERS_VERIFY` and never
  calls convert) and the `-profile docker` example runs.
- Commands still required from a maintainer/CI machine with Docker (unchanged from
  slice 1, now covering three pinned modules):

```sh
nf-test test --profile docker --ci            # pulls the Wave image for combine/validate/convert
python tests/run.py --converter-source <fair-bioheaders-0.9.0-checkout>
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results   # unchanged by this slice
nextflow run main.nf -profile docker --sequence examples/assembly.gfa --sequence_format gfa   # and the FASTA/GFF3/protein examples as in ci.yml
docker build -t fhr-nextflow:0.1.0 environment
git diff --check
```


## Adopting verify and convert after their merge

Gate (from #29): adopt only after the upstream interfaces **merge** and **pass
local parity** — no adoption on review heads.

1. Re-read the merged revisions (do not reuse the PR-head SHAs above) and re-diff
   `modules/nf-core/fairbioheaders/verify|convert` against the merged upstream
   files at those SHAs, plus this document's tables (PR branches moved since).
   **Convert: done 2026-11-12** at merge commit `4dc3bc5477` — the re-diff mattered:
   the merged files differ from the `639dd3c` review head this document had recorded
   (default prefix, output-redirect quoting, a new collision guard, and the two
   spaced-names tests replaced by name-collision tests). **Verify: still gated**;
   #13635 remains open and its head moved again (`bb6c492` → `bc5a8640`, 2026-11-12),
   so its table above must be re-diffed at merge time, not reused.
2. Install combine-style: byte-identical files at recorded SHAs in `modules.json`;
   run the drift step; run the upstream nf-tests (`nf-test test --profile docker`).
   **Convert: done** — 8 files verified, drift step green, 11/11 upstream convert
   tests passing (see "Testing status for slice 2a").
3. **verify parity:** confirm `FHR_ATTACH`'s join and the Dockstore test profile
   behave identically without `--type` (odd-extension rejection), that the report
   names/content keep the `file:` header, and that the harness failure substrings
   (`checksum`, `after sequence data`, `duplicate key`, `proteome`) still appear.
   Then switch `subworkflows/attach`, the Dockstore workflow and the README import
   examples from the local file to the pinned module **only if** the family-named
   combine outputs still match verify's extension inference (they do: `.fhr.fa`,
   `.fhp.faa`, `.fhr.gfa`, `.fhgff3.gff3` all infer correctly) — document the
   switch.
4. **convert parity: run 2026-11-12; result is partial coverage.** The serializations
   themselves match byte for byte (JSON, YAML, HTML, header extraction) and the
   `.fhr.` infix is reachable by configuration, but the upstream contract cannot name a
   protein header-only output `ID.fhr.faa` (`--to` has no `faa` token and the format is
   the extension), it takes two input rows, and it reports an unusable format from
   inside the task rather than before submission. The gate's either/or was therefore
   resolved as **option (a)**: `FHR_CONVERT` stays the module the example and
   `FHR_ATTACH` call, and `fairbioheaders/convert` is published as the importer-facing
   module — pinned, tested, and documented with the rename recipe, rather than adopted
   under a silent contract change. Blockers 1–3 in the convert contract table carry the
   maintainer decision asks; nothing further may be switched here unilaterally.
5. Only after callers are migrated, delete the duplicate local implementations
   (`modules/convert` once its blockers 1–3 resolve; `modules/combine` once the naming
   blocker resolves — the two naming blockers are one family decision and should close
   together; the local `verify` main.nf once step 3 passes).
6. Re-evaluate container pins at each toolkit bump: the reviewed complete-tree
   update procedure above maintains the Wave side (nf-core CLI updates require
   the separate local-layout migration first); the repo-side Bioconda/BioContainers/depot trio and
   `environment/requirements.*` move by this repository's own pin procedure
   (AGENTS.md).

## Open questions this raises for #7 (full-family coverage)

- FHT: no upstream module exists; FAIR-bioHeaders-Specification-side gating
  (FHT-Specification #8/#9) remains the prerequisite, and the upstream module set
  will eventually need an FHT contract before any `fairbioheaders/convert`-style
  tooling claims family completeness.
- Does the family want **header-family-signifying filenames** (`ID.fhp.faa`) or
  **input-faithful names** (`ID.faa`) as the shared upstream standard? #7 should
  settle this once, upstream, so this repository can retire `modules/combine`
  (blocker 1 above) and `modules/convert` (its blocker 1) together.
- The upstream convert output extension is the `--to` token, so the standard above has
  a second consequence: whether **protein FASTA keeps a distinct extension** in the
  shared modules (`faa` is a valid FASTA extension here and in the toolkit's own
  naming, but not a `--to` choice). If the family wants `.faa`, upstream
  `fairbioheaders/convert` needs either a `faa` alias or a way to set the extension
  separately from `--to` (convert blocker 2).
- Parent-link verification (`verify-links`) has no upstream module; if #7 wants
  family-wide workflows, a future `fairbioheaders/verify_links` submission should
  be considered (with the `require_all`/`fail_on_mismatch` ext semantics).
- FHGFF3 through combine works upstream (fixture + test present); the GFF3 *rule*
  checks remain with gff3-validator, which is not on Bioconda yet
  (bioconda/bioconda-recipes#70098) — a full-family upstream story still needs
  that packaging gap closed or an explicit decision that GFF3 validation stays
  repository-owned.
- Upstream snapshots were recorded against Nextflow 26.10.4 while this repo's CI
  pins 26.04.6; #7's compatibility matrix should decide whether to dual-test or
  bump the baseline.
