# Module migration: upstream nf-core `fairbioheaders` modules (issue #29)

This document tracks the migration of this repository's Nextflow workflows to the
upstream [nf-core/modules](https://github.com/nf-core/modules) `fairbioheaders`
module set, the pinned revisions, the per-module contract comparison against the
local implementations, and the remaining adoption steps. It exists because the
upstream modules and the repository modules intentionally diverged during
development (#21 consolidation, then the upstream submissions) and must be
reconciled without silently dropping documented behavior.

Status date: **2026-11-14** (slice 4 adopts **verify** at its merged revision `6fb4f8f1`
and retires the local repository module — the last non-pinned `fairbioheaders` module; slice 3
records the maintainer naming decision; upstream state was re-verified against the GitHub API
on 2026-11-13/14; re-check before acting on it — checkouts and PRs move).
**#29 is closed** (all four modules are upstream-pinned and byte-identical: combine 7/7,
validate 7/7, convert 8/8, verify 7/7). Its two routine remainders — the `modules/local/`
layout migration and the container-pin re-evaluation at the next toolkit bump — are
**scoped on [#7](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Nextflow/issues/7)** as
of 2026-11-14 (maintainer decision 6A), and the snapshot-baseline question #7 inherited is
decided as a **dual matrix** (decision 6B), implemented in `.github/workflows/ci.yml`.

## Naming decision (2026-11-13) — Option (a): adopt upstream naming, retire the family contract

On 2026-11-13 the maintainers decided issue #29's open naming question as **option (a)**:
the suite **adopts the upstream nf-core output-naming convention and retires the
family-signifying filename contract**. This **supersedes the earlier #21 consolidation
decision** ("protein FASTA as `.fhp.faa`", header-family output names), which AGENTS.md
itself said stands "until a maintainer decision changes it" — this is that decision. The
`modules/combine` (`FHR_COMBINE`) and `modules/convert` (`FHR_CONVERT`) compatibility
modules are **deleted**; every caller now composes the pinned upstream
`FAIRBIOHEADERS_COMBINE` / `FAIRBIOHEADERS_CONVERT` directly.

Concretely, the observable output-naming contract is now the upstream one (input/`--to`
faithful, family marker dropped everywhere, including the `.fhr.` infix on metadata files,
for consistency):

| Producer | Old (family contract) | New (upstream, `ext.prefix`/default = plain `meta.id`) |
| --- | --- | --- |
| combine — FASTA genome | `ID.fhr.fa` | `ID.fasta` / `ID.fa` (input's extension) |
| combine — GFA | `ID.fhr.gfa` | `ID.gfa` |
| combine — protein FASTA | `ID.fhp.faa` | `ID.faa` (input's extension) |
| combine — GFF3 | `ID.fhgff3.gff3` | `ID.gff3` |
| combine — compressed | `ID.fhr.fa.gz` … | `ID.<ext>.gz` (BGZF preserved) |
| convert — JSON | `ID.fhr.json` | `ID.json` |
| convert — YAML / HTML | `ID.fhr.yaml` / `ID.fhr.html` | `ID.yaml` / `ID.html` |
| convert — header-only protein | `ID.fhr.faa` | `ID.fasta` (no `--to faa`; kind on `meta`) |
| convert — header-only genome FASTA / GFA | `ID.fhr.fasta` / `ID.fhr.gfa` | `ID.fasta` / `ID.gfa` |
| create_json standalone JSON | `ID.fhr.json` | `ID.json` |
| reports | `ID.verify.txt`, `ID.validate.txt`, `ID.verify-links.txt`, `ID.gff3-validate.*`, `ID.stripped.<kind>` | **unchanged** (never carried a family marker) |

Verified empirically in the slice-3 container (this corrects two prose assumptions carried
in the pre-decision tables below): the pinned upstream combine/convert stage inputs by
their **original name** (they do **not** use `stageAs: 'input/*'` — that was the retired
compat module), so the collision is structural: upstream combine fails with the toolkit
message `FHR: Output must differ from the input files`, and upstream convert has an explicit
`error "Input and output names are the same, set prefix in module configuration to
disambiguate!"`. Both are the documented mechanism to respect. `ext.prefix = { meta.id }`
set in the consuming project's config reaches the upstream convert even when it is invoked
aliased inside `FHR_ATTACH` (verified).

The blockers recorded in the combine/convert contract tables are therefore **RESOLVED by
maintainer decision 2026-11-13: (a) capitulate**; the tables are kept verbatim as the
pre-decision record and are annotated in place below. The family-signifying-filename
"Open questions" entry is closed for this repository (it can be reopened upstream — see the
staged follow-up request at the end of this document).

## Upstream state (verified 2026-11-13/14)

| Upstream module | PR | State | Revision |
| --- | --- | --- | --- |
| `fairbioheaders/combine` | [nf-core/modules#13492](https://github.com/nf-core/modules/pull/13492) | merged 2026-11-09 | `8faff34023b16ecdc41b02bac42989834075e3f1` |
| `fairbioheaders/validate` | [nf-core/modules#13509](https://github.com/nf-core/modules/pull/13509) | merged 2026-11-09 | `86e852ef429e021d16f7279aaddb9b81eb067f8a` (contained in `8faff340…`) |
| `fairbioheaders/verify` | [nf-core/modules#13635](https://github.com/nf-core/modules/pull/13635) | **merged 2026-11-13T15:26:20Z** | `6fb4f8f1f3f70a34a1f0efdc84729c5dacbc33e5` (merge commit; PR head at merge `154ca9f02b73f4c1c3ab8dc0e4b23ca9e0b0616f` — the review heads this document had recorded (`bb6c492`/`bc5a8640`) are superseded; the merged tree differs from them, see the contract table) |
| `fairbioheaders/convert` | [nf-core/modules#13636](https://github.com/nf-core/modules/pull/13636) | merged 2026-11-11T23:01Z | `4dc3bc54779d6caf3a47d49f37811e651fa2700a` (merge commit; PR head at merge `35dc28bd72563db7fb7192d9fcee7068b65984c4`, review head `639dd3cc…` was superseded — see the contract table) |

Shared test fixtures landed in [nf-core/test-datasets#2363](https://github.com/nf-core/test-datasets/pull/2363);
they resolve under `modules_testdata_base_path` at
`genomics/sarscov2/genome/fairbioheaders/` and
`genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/fairbioheaders/`
(verified present on the `modules` branch 2026-11-10; the convert suite fetched the
same paths again on 2026-11-12).

Slice 1 (merged as #30) adopted **combine** and **validate**. Slice 2a (merged as #31)
installed the newly merged **convert** module and ran its parity check; slice 3 (merged as
#32) executed the maintainer naming decision (option (a)) and migrated every caller.
**Slice 4 (2026-11-14) adopts verify:** nf-core/modules#13635 merged 2026-11-13T15:26:20Z
and the module is now pinned at its merge commit `6fb4f8f1`, with the local repository
implementation retired by the byte-for-byte overlay at the same canonical path (no import
rewritten; the tuple shapes and default report names are preserved). Adoption stayed gated
on merge **plus** local parity checks throughout (section "Adopting verify and convert
after their merge").

## How the upstream modules are pinned

- `modules/nf-core/fairbioheaders/combine/`, `modules/nf-core/fairbioheaders/validate/`,
  `modules/nf-core/fairbioheaders/convert/` and `modules/nf-core/fairbioheaders/verify/`
  (including `.conda-lock/`, `meta.yml`,
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
  under `modules/*` (and `subworkflows/*`) beside the pinned `modules/nf-core/` tree —
  since slice 4 the whole `modules/nf-core/fairbioheaders` set is upstream-pinned. nf-core
  4.2.2 rejects those untracked directories. A valid manifest alone does **not**
  make `nf-core modules update`, `list local` or `lint` usable here. Use the
  CLI-less procedure below until a separate layout migration moves local modules
  to `modules/local/` and updates every importer. **That migration is [#7
  work](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Nextflow/issues/7), not #29 work**
  (maintainer decision 6A, 2026-11-14), and it pairs with the next toolkit bump: that bump is
  when the container pins are re-evaluated anyway (step 6 of the adoption list), so one reviewed
  cycle moves the layout, the importers and the pins together instead of two.
- CI runs `python3 scripts/check_upstream_modules.py`. It iterates **every entry of
  `modules.json`**, retrieves the complete recursive GitHub tree at each pin with
  `curl --retry 3`, rejects truncated responses, and compares all module-relative
  paths, blob hashes and file modes. Hidden lock files, missing files and extra local
  files are included. Any drift fails the job before nf-test runs. Because the guard is
  manifest-driven, installing a module adds it to the drift check automatically: it now
  covers combine (7 files), validate (7), convert (8 — convert also ships
  `tests/nextflow.config` for its `ext.args`/`ext.prefix` cases) and verify (7 — installed
  2026-11-14 at `6fb4f8f1`; verify ships no `tests/nextflow.config`).

Provenance of the runtime/test files (the complete directory for each pinned module
also includes the two `.conda-lock/` platform locks, verified by CI; combine, validate
and verify hold seven files each, convert eight because it also ships
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
| verify @ `6fb4f8f1f3…` | main.nf | `69ea8fba319e498ce3e71cb6fe120529b5920abb` |
| verify @ `6fb4f8f1f3…` | meta.yml | `f420baaccf215c1530b595a8b5b0c4fe25d9b698` |
| verify @ `6fb4f8f1f3…` | environment.yml | `d0c0735cb08e0a193ca197dc24ca046d2e6c2cc8` |
| verify @ `6fb4f8f1f3…` | tests/main.nf.test | `62b1e97997550e2e6b6646c49b36d7f2ca7b4d16` |
| verify @ `6fb4f8f1f3…` | tests/main.nf.test.snap | `e83cd3cdb6bce2c8280c91792b051154bd1a9a06` |
| verify @ `6fb4f8f1f3…` | `.conda-lock/linux_amd64-bd-71029206d3ce1119_1.txt` | `614f61ced8ebef6dc1a6e78742a2f0672b805031` |
| verify @ `6fb4f8f1f3…` | `.conda-lock/linux_arm64-bd-1ff11621d7e9a7c8_1.txt` | `8cc63c8d8b1d37b467b2074e22af63c10a61a6fa` |

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

> **RESOLVED by maintainer decision 2026-11-13 — (a) capitulate.** All three blockers are
> settled by adopting the upstream names: the family naming is dropped (blocker 1), the
> quoting/hardening caveat moves to a documented caller obligation to constrain `meta.id`/
> `ext.prefix` (blocker 2; `FHR_ATTACH`/the example still use `isSampleId`, and the
> Dockstore workflow now constrains ids and applies the collision disambiguator), and every
> caller sets `ext.prefix`/ids that cannot collide with the staged input (blocker 3).
> `modules/combine` is deleted in the same change.

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

### `fairbioheaders/verify` (upstream `6fb4f8f1`, merged 2026-11-13) vs local `FAIRBIOHEADERS_VERIFY` (retired in slice 4)

Adopted at the merge commit, not at a review head. **The re-diff mattered again:** the
merged tree differs from both review heads this section had recorded (`bb6c492` /
`bc5a8640`). The merged revision (1) drops the review head's double-quoted prefix redirect
— `${prefix}.verify.txt` is unquoted in `script` and `stub`, exactly as in the merged
convert; (2) replaces the spaced-names test with the changed-after-combine failure test, so
the merged suite is **4 cases** (plain FHR FASTA via upstream combine, changed-after-combine
fails with `Checksum verification failed`, no-header fails with `No ;~ FHR metadata header
found`, stub), not the 10 recorded at review head; and (3) ships the Wave container pair
plus `.conda-lock/` (7 files, no `tests/nextflow.config`). Contract comparison at the
merged revision against the retired local module:

| Aspect | Upstream @ `6fb4f8f1` | Local (retired) | Verdict |
| --- | --- | --- | --- |
| Input | `tuple val(meta), path(sequence)` | same | matches — every caller keeps its wiring |
| Output | `tuple val(meta), path("${prefix}.verify.txt")`, emit `report` + versions | `path("*.verify.txt")` (glob) | matches for every caller: `ext.prefix` is set nowhere for verify, so the prefixed name equals the globbed one (`ID.verify.txt`) |
| `--type` | **not passed**; the toolkit infers from the extension (`.fa/.fasta/.fna/.fas/.faa/.ffn/.frn/.fsa/.mpfa/.gfa/.gff/.gff3`, `.gz`/`.bgz` handled) | explicit whitelist: `.gfa→gfa`, `.gff3?→gff3`, **anything else forced to `fasta`** | **differs — the parity item.** Odd extensions change side: the local module verified a FHR/FHP-headed `sample.txt` (forced FASTA); the pinned module fails it in the task with `FHR: Unsupported file extension: sample.txt` (toolkit 0.9.0, probe-verified). All this repository's callers stage combine outputs or fixture names, which infer correctly; the new surface is pinned by a `tests/run.py` case |
| Compression | same `.gz/.bgz` verification (toolkit side) | same | matches (covered through the `FHR_ATTACH` BGZF harness run) |
| Quoting | report redirect and prefix unquoted; staged path interpolated (Nextflow escapes staged paths) | full single-quote closure on path, prefix, `meta.id` | differs (same caller-discipline caveat as combine/validate/convert: constrain `meta.id`/`ext.prefix`; `FHR_ATTACH` and the example gate IDs with `isSampleId`). Probe: a staged `protein with space.faa` verifies cleanly with a single-line `file:` report — pinned by a new `tests/run.py` case. The mirror case is **not** clean and is now pinned too: `ext.prefix = { 'spaced prefix' }` interpolates into the redirect unquoted and the task dies with `.command.sh: line 8: syntax error near unexpected token `prefix.verify.txt'` (exit 1, recorded verbatim 2026-11-14, F8) — the message names only the redirect tail, never the prefix. `tests/run.py` asserts that exact failure so the asymmetry is documented behavior, and an upstream quoting fix would surface as a failing assertion rather than a silent contract move |
| Failure semantics | schema/checksum failure fails the task; report keeps the `file: <path>` header | identical | matches; the harness failure substrings (`checksum`, `after sequence data`, `duplicate key`, `proteome`) are toolkit messages and still fire — all five rejection cases pass unchanged |
| Report content | `file: <staged path>` + `bioheaders verify` stdout | same (quoted interpolation) | matches for space-free paths |
| Conda | `"bioconda::fair-bioheaders=0.9.0"` (quoted line) | same pin, unquoted line | matches (content) |
| Container | Wave `community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119` (+ `community-cr-prod` blob URL for Singularity) | BioContainers `quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0` + Galaxy depot pair | **differs — same Wave/quay split as the other three pinned modules** (see "Containers and conda"); CI's verify pin check moved to the Wave family |
| Version reporting | `(task.process, 'fair-bioheaders', bioheaders --version)` on topic `versions` + named emit | identical | matches |
| Stub | `touch ${prefix}.verify.txt` | same (quoted) | matches |
| nf-tests | 4 cases, fixtures from nf-core/test-datasets (the merged #2363 set), snapshots recorded under Nextflow 26.10.4 / nf-test 0.9.5 | 5 cases (fasta.gz, faa-fhp, gff3, no-header-fails, stub), inline metadata fixtures | upstream lacks the **direct FHGFF3**, **compressed** and **spaced-name** cases the local suite carried. Not dropped: the compressed case stays covered through the `FHR_ATTACH` gzip harness run (its `ATTACHED … .faa.gz` marker only appears after verify joined a passing report); direct FHGFF3, odd-extension rejection and the spaced-name report shape were **ported into `tests/run.py`** per the slice-1 validate precedent |

**Verdict: parity confirmed; migrated in place; local module retired.** The retirement has
no import-rewrite step because the local module and the pinned module share the canonical
path `modules/nf-core/fairbioheaders/verify/main.nf`: installing the byte-identical upstream
tree overlays (retires) the local implementation, and every existing import — `FHR_ATTACH`
(`FAIRBIOHEADERS_VERIFY as CHECK_COMBINED`), the Dockstore workflow, the three harness
scripts in `tests/run.py` and the README/PIPELINES examples — resolves to the pinned module
unchanged. The zero-dangling proof is the drift checker (4/4 manifest entries byte-identical,
so no local-only file survives) plus a repository grep: no reference to the local module's
unique surfaces (`--type` whitelist, quay/depot pin at the verify path) remains outside the
pinned tree. `subworkflows/attach` and the Dockstore workflow consume the pinned module;
`FHR_VERIFY_LINKS` (parent links, `bioheaders verify-links`) stays repository-owned —
upstream has no parent-link module.

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

> **RESOLVED by maintainer decision 2026-11-13 — (a) capitulate.** Blocker 1: the family
> name goes — the suite adopts `<id>.<format>` and rewrites every documented marker in this
> change. Blocker 2 (protein `faa`): resolved as capitulation dictates — header-only protein
> conversions become `.fasta`, and the protein/genome distinction moves off the extension
> onto `meta` (a staged follow-up asks upstream for an `faa` alias, "not filed, maintainer's
> call"). Blocker 3 (two-row input): adopted; the example, `FHR_ATTACH` and the harness are
> rewired and the break is documented for direct importers. Blocker 4 (quoting/rejection
> surface): documented as a caller obligation. `modules/convert` is deleted in the same
> change.

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
| Attach metadata + exact-byte checksum (`bioheaders combine`) | `FAIRBIOHEADERS_COMBINE` (pinned upstream; family-name compat module `FHR_COMBINE` retired 2026-11-13) | upstream |
| Verify a **headed sequence file** (schema + checksum of the file) | `FAIRBIOHEADERS_VERIFY` (pinned upstream; local repository module retired 2026-11-14) | upstream |
| Validate **standalone metadata** (schema only, no checksum/sequence) | `FAIRBIOHEADERS_VALIDATE` (pinned upstream) | upstream |
| Verify **parent links** (`derivedFrom`/`genomeReference` against candidate parents, `bioheaders verify-links`) | `FHR_VERIFY_LINKS` | repo-owned, no upstream counterpart |
| GFF3 syntax/SO/biology rules | `GFF3_VALIDATE` (gff3-validator 0.1.0) | repo-owned, no upstream counterpart |
| Metadata conversion / header extraction (`bioheaders convert --to`) | `FAIRBIOHEADERS_CONVERT` (pinned upstream; family-name compat module `FHR_CONVERT` retired 2026-11-13) | upstream |
| Native JSON creation, stripping, converter pytest gating | `FHR_CREATE_JSON`, `FHR_STRIP`, `FHR_CONVERTER_TESTS` | repo-owned |

## Caller migration status

| Caller | Uses | Status |
| --- | --- | --- |
| Standalone example `main.nf` | `FHR_ATTACH` → pinned `FAIRBIOHEADERS_COMBINE` + pinned `FAIRBIOHEADERS_VERIFY`; `FHR_CREATE_JSON` → pinned `FAIRBIOHEADERS_VALIDATE`; pinned `FAIRBIOHEADERS_CONVERT` for the published YAML | **fully migrated (2026-11-13 option (a) + 2026-11-14 slice 4)**; every fairbioheaders module it reaches is pinned upstream |
| `subworkflows/attach` (`FHR_ATTACH`) | pinned `FAIRBIOHEADERS_COMBINE` + pinned `FAIRBIOHEADERS_VERIFY` + pinned `FAIRBIOHEADERS_CONVERT` | **migrated**; external channel tuple unchanged, `sequence` is `<id>.<ext>` and `json` is `<id>.json`; the verify include path did not change in slice 4 (the pinned tree overlays the retired local module) and the report join is unchanged |
| Dockstore workflow `workflows/fairbioheaders` | pinned `FAIRBIOHEADERS_COMBINE` + pinned `FAIRBIOHEADERS_VERIFY` | **fully migrated**; outputs are `combine/<id>.<ext>` (`<id>.faa` for protein) and `verify/<id>.verify.txt`; since slice 4 both processes run the Wave container family (the `-profile test,docker` outputs and reports are unchanged); descriptor `.dockstore.yml` paths unchanged and still resolve; the test samplesheet protein row id is `proteins` so its output cannot collide with the staged `protein.faa`; the workflow still does not call convert |
| `modules/create_json` | pinned `FAIRBIOHEADERS_VALIDATE` | migrated in place; its own output renamed `ID.fhr.json` → `ID.json` |
| External direct importers | `modules/nf-core/fairbioheaders/{combine,convert,validate,verify}` | **all four paths are the pinned upstream modules**; the family compat modules are deleted, and the local verify implementation is retired under the same path — see the migration notes below and the verify contract table for the `--type`/container deltas |

**Migration note for importers of the retired `modules/combine` (`FHR_COMBINE`)** — the
compatibility module no longer exists. Import `modules/nf-core/fairbioheaders/combine`
(`FAIRBIOHEADERS_COMBINE`) instead. Its `sequence` output is named
`<prefix>.<input extension>` (e.g. `sample.fasta`, `sample.faa`, `sample.gff3.gz`) instead
of the retired header-family names (`sample.fhr.fa`, `sample.fhp.faa`, …), it does not pass
`--type`, and it fails when the derived output name would overwrite a staged input
(`FHR: Output must differ from the input files`). Migration line, old → new:
`ID.fhr.fa` → `ID.fasta`/`ID.fa`; `ID.fhr.gfa` → `ID.gfa`; `ID.fhp.faa` → `ID.faa`;
`ID.fhgff3.gff3` → `ID.gff3`; the `.gz` suffix behaviour is unchanged. Importers that
require the family names in the filename must wrap the upstream module and rename from
their own contract — this suite no longer does.

**Migration note for importers of the retired `modules/convert` (`FHR_CONVERT`)** — the
compatibility module no longer exists. Import `modules/nf-core/fairbioheaders/convert`
(`FAIRBIOHEADERS_CONVERT`) instead: it takes **two input rows** (`(meta, file)` plus a
separate format-value channel), names its output `<meta.id>_converted.<format>` unless
`ext.prefix` says otherwise, and offers the toolkit's `--to` set (`json`, `yaml`, `jsonld`,
`html`, plus `fasta`/`gfa`/`gff3`) with **no `faa` token** and **no pre-launch format
whitelist** (an unusable `--to` fails inside the task with `invalid choice`). This repository
publishes the plain id, so the documented migration line is
`ID.fhr.<format>` → `ID.<format>` (`ID.fhr.json` → `ID.json`, `ID.fhr.faa` → `ID.fasta`, …);
achieving the plain name is a configuration step:

```nextflow
process {
    withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { meta.id } }
}
```

A header-only protein file loses its distinct extension (`faa` is not a `--to` choice); the
protein/genome distinction must travel on `meta` and in the file's own header. Callers that
need the `.faa` name or the pre-launch rejection wrap the upstream module and rename from
their own contract; this suite no longer ships either.

**Migration note for importers of the retired local `FAIRBIOHEADERS_VERIFY`** — the include
path is unchanged (`modules/nf-core/fairbioheaders/verify/main`); the file behind it is now
the pinned upstream module at `6fb4f8f1`. The input/output tuples and the default report name
`ID.verify.txt` are preserved, so call sites keep working. Three observable changes: (1) the
module no longer passes `--type` — the toolkit infers the format from the extension and
**rejects unknown extensions** (`FHR: Unsupported file extension: <name>`) where the local
module forced anything non-GFA/GFF3 to FASTA; (2) the container is the Seqera Wave image (plus
the `community-cr-prod` blob for Singularity) instead of the BioContainers/Galaxy-depot pair —
offline registry allowlists must include `community.wave.seqera.io` (already true since slice 1
for combine/validate/convert); (3) the prefix is not shell-quoted, so callers that set
`ext.prefix` or pass unvalidated `meta.id` values must constrain them, as for the other three
pinned modules.

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

## Testing status for slice 3 — naming decision, option (a) (2026-11-13)

Same host and method as slices 1/2a (Docker 29.9.3 on an arm64 host; no host `nextflow`,
`nf-test` or Java): a reproducible verification container `fhr-nf29-verify:slice3`
(`FROM nextflow/nextflow:26.04.6`, Amazon Linux 2023 / Java 21 CI baseline, python3.11 venv
with `fair-bioheaders[jsonld]==0.9.0`, `gff3-validator==0.1.0`, `pytest`, `pyld`, nf-test
0.9.5 from askimed/nf-test v0.9.5), linux/amd64 emulation, repository processes executing
**natively**. The Dockerfile is a verification artifact, not repository content. As in
earlier slices this exercises scripts, channel wiring, snapshots and toolkit semantics, not
the container-image pulls (CI's `--profile docker` jobs).

Empirical probes run **before** finalizing the design (correcting prose assumptions in the
pre-decision tables):

- **combine collision/staging probe.** With the pinned upstream `FAIRBIOHEADERS_COMBINE`
  on a `.faa` input: `meta.id=protein` (output would equal the staged input) fails with the
  toolkit message `FHR: Output must differ from the input files`; `meta.id=proteins` emits
  `proteins.faa` cleanly. Inputs are staged by their **original name** (no `input/*` staging).
- **convert prefix-scope probe.** A top-level `config:` block inside a subworkflow is a
  Nextflow compilation error ("out-of-order section labels"), and a top-level `process {}`
  scope in a `.nf` script is rejected ("Invalid process definition"). But
  `process { withName: '<name>' { ext.prefix = { meta.id } } }` in the consuming project's
  `nextflow.config` **does** reach an upstream convert nested in a subworkflow — matching
  either the real process name or the alias. The example therefore publishes plain
  `<id>.yaml`/`<id>.json` via alias-scoped config entries (`FHR_YAML`, `EXTRACT_JSON`),
  deliberately **not** matching the bare `FAIRBIOHEADERS_CONVERT` so the pinned module's
  own nf-test keeps its `test_converted.<format>` default (this was caught: a bare-name
  `withName` leaked into the upstream tests and flipped their snapshot file names — bytes
  identical, `md5` unchanged).

Executed on the final tree (compat modules deleted):

- `nf-test test --ci` — **31/31 passed** in 607 s: pinned upstream combine 8, convert 11,
  validate 7, repository `FAIRBIOHEADERS_VERIFY` 5. The `FHR_COMBINE` compatibility suite
  (9 tests + snapshot) is gone with `modules/combine`. The verify suite's setups were
  retargeted to the pinned upstream combine; its **snapshots were re-recorded** and the diff
  is proven to change only the report `file:` path line (report `test.verify.txt` name,
  `versions` (0.9.0) and structure unchanged — the report body is `file: <name>\nChecksum
  verified.\n` and recomputing the md5 of exactly that string with `<name>` = `test.faa` /
  `test.gff` / `test.fasta.gz` reproduces each new digest). All three pinned module trees
  still match `modules.json` (`scripts/check_upstream_modules.py`: combine 7/7, validate 7/7,
  convert 8/8).
- `python tests/run.py --converter-source <v0.9.0 checkout c6d7454>` — **62/62 passed**
  (58 positive/rejection cases + 4 converter-gate cases; the old FHR_CONVERT parity probe is
  replaced by upstream-only cases: the plain-`<id>.<format>` convert run, the `--to faa` /
  `--to exe` in-task rejections, the input==output collision refusal, and the retained
  spaced/quoted-name case), including the migrated combine/convert/create_json markers
  (`rich.json`, `attached-fasta.fasta`, `example/{sequence.gfa,json,yaml}`,
  `ATTACHED/EXTRACTED/CONVERTED` protein markers with `.faa`/`.fasta`/`.json`, `cvt-*`),
  plus the toolkit's own **2410** pytest tests through the converter gate and the
  injected-failure / `-resume` / version-mismatch rejections. `python -m py_compile
  tests/run.py` and `git diff --check` clean.
- `nextflow run workflows/fairbioheaders/main.nf -profile test` (native) — passed: five
  samplesheet rows produce `combine/{fasta.fa,gfa.gfa,gff3.gff3,jsonld.fa,proteins.faa}` and
  five `verify/<id>.verify.txt` reports (`Checksum verified.`); the expanded-JSON-LD row
  combines correctly through the upstream module (no pre-conversion needed). The protein
  row's id is `proteins` so its output cannot collide with the staged `protein.faa`.

Commands still required from a maintainer/CI machine with Docker (native runs cannot exercise
image pulls; unchanged in kind from slice 2a, now covering only upstream combine + repo verify
in the Dockstore job):

```sh
nf-test test --profile docker --ci            # pulls the Wave image for combine/validate/convert
python tests/run.py --converter-source <fair-bioheaders-0.9.0-checkout>
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results   # renamed combine outputs (…/proteins.faa) + verify reports
nextflow run main.nf -profile docker --sequence examples/assembly.gfa --sequence_format gfa   # example.fhr.gfa → example.gfa; plus the FASTA/GFF3/protein examples as in ci.yml
docker build -t fhr-nextflow:0.1.0 environment
git diff --check
```


## Testing status for slice 4 — verify adoption (2026-11-14)

Same host and method as slices 1–3 (Docker 29.9.3 on an arm64 host; no host `nextflow`,
`nf-test`, `nf-core` or Java — `java -version` on the macOS host is the Apple stub and
fails): the repository's processes executed **natively** inside the reproducible
verification image `fhr-nf29-verify:slice4` (`FROM nextflow/nextflow:26.04.6`, Amazon
Linux 2023 / Java 21 CI baseline, python3.11 venv with `fair-bioheaders[jsonld]==0.9.0`,
`gff3-validator==0.1.0`, pytest, pyld, nf-test 0.9.5), linux/amd64 emulation. The image
is a verification artifact, not repository content. As in earlier slices this exercises
scripts, channel wiring, snapshots and toolkit semantics, not the container-image pulls
(CI's `--profile docker` jobs).

- **Merged-revision fetch:** all seven upstream verify files were downloaded at
  `6fb4f8f1f3f70a34a1f0efdc84729c5dacbc33e5` with the recorded procedure script; each
  `git hash-object` matched the blob sha in the untruncated recursive GitHub tree.
  `python3 scripts/check_upstream_modules.py` (host, network) reported `combine: all 7
  files match 8faff340…`, `validate: all 7 files match 86e852ef…`, `convert: all 8 files
  match 4dc3bc54…` and **`verify: all 7 files match 6fb4f8f1…`** — the manifest-driven
  guard included the new module automatically. `python3 -m unittest discover -s tests -p
  test_upstream_modules.py` stays green (2 tests).
- **CI pin steps re-run locally:** the nf-test job's Wave loop is now `for module in
  combine validate convert verify` and the BioContainers/depot loop `modules/strip
  modules/verify_links`; the dockstore job's verify check moved to the Wave family. All
  greps, the converter-environment checks and the `.dockstore.yml` path existence loop
  pass against the tree.
- **Behaviour probes before wiring the ported cases** (native toolkit 0.9.0):
  `bioheaders verify --type fasta sample.txt` succeeds (the retired local module's
  forced-FASTA surface) while `bioheaders verify sample.txt` fails with
  `FHR: Unsupported file extension: sample.txt` (the pinned module's inference surface);
  `.gff3` and a `protein with space.faa` name verify cleanly. These are the parity items
  step 3 asked to re-check, now pinned as `tests/run.py` cases.
- **`nf-test test --ci` — 30/30 passed** in 895 s: pinned upstream combine 8, convert 11,
  validate 7 and the **merged upstream verify suite 4** (`sarscov2 - fasta - fhr` asserting
  the exact report `['file: test.fasta', 'Checksum verified.']`, `changed after combine -
  fails` with `Checksum verification failed`, `no header - fails` with `No ;~ FHR metadata
  header found`, stub). The count moves 31 → 30 because the retired local 5-case suite is
  replaced by upstream's 4 cases; the lost coverage went to `tests/run.py`, not to the
  bin. Committed upstream snapshots (recorded under Nextflow 26.10.4 / nf-test 0.9.5)
  matched in CI mode under Nextflow 26.04.6 / nf-test 0.9.5, as for the other modules.
- **`python tests/run.py --converter-source <Tools v0.9.0 @ c6d7454>` — 65/65 passed** in
  4584 s (slice 3's 62 plus the three ported verify runs: direct FHGFF3 verification of
  `chain/annotation.fhgff3.gff3`, the `Unsupported file extension` odd-extension
  rejection, and the spaced-name two-line report case). Every pre-existing verify-driven
  rejection fired identically through the pinned module (`checksum`, `after sequence
  data` ×2, `duplicate key`, `proteome`), and `FHR_ATTACH`'s report join, the protein
  `ATTACHED … .faa`/`.faa.gz` markers and the converter gate (the toolkit's own **2410**
  pytest tests) behaved as documented; the injected-failure, `-resume` and
  version-mismatch rejections passed.
- **`nextflow run workflows/fairbioheaders/main.nf -profile test` (native) — passed:**
  five samplesheet rows produce `combine/{fasta.fa,gfa.gfa,gff3.gff3,jsonld.fa,proteins.faa}`
  and five `verify/<id>.verify.txt` reports each carrying `Checksum verified.` — the
  identical observable result slice 3 recorded, now from the pinned module (only the
  container family changes, which the native run does not exercise).
- `python -m py_compile tests/run.py` and `git diff --check` clean.

Commands still required from a maintainer/CI machine with Docker (native runs cannot
exercise image pulls; unchanged in kind, but the Dockstore job now pulls **only** the
Wave family since verify joined it):

```sh
nf-test test --profile docker --ci            # Wave images for all four pinned modules
python tests/run.py --converter-source <fair-bioheaders-0.9.0-checkout>
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results   # combine + pinned-verify reports in Wave
nextflow run main.nf -profile docker --sequence examples/assembly.gfa --sequence_format gfa   # plus the FASTA/GFF3/protein examples as in ci.yml
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
   spaced-names tests replaced by name-collision tests). **Verify: done 2026-11-14**
   at merge commit `6fb4f8f1f3f70a34a1f0efdc84729c5dacbc33e5` (merged
   2026-11-13T15:26:20Z) — the re-diff mattered again: the merged module drops the
   review head's quoted prefix, ships **4** tests rather than the 10 recorded at
   review head (the spaced-names case became the changed-after-combine case), and
   replaces the container pins with the Wave pair (see the verify contract table).
2. Install combine-style: byte-identical files at recorded SHAs in `modules.json`;
   run the drift step; run the upstream nf-tests (`nf-test test --profile docker`).
   **Convert: done** — 8 files verified, drift step green, 11/11 upstream convert
   tests passing (see "Testing status for slice 2a"). **Verify: done** — 7 files
   fetched with per-blob `git hash-object` verification against the untruncated tree,
   `modules.json` entry added, drift step green 7/7/8/7, upstream verify tests run
   natively with `--ci` (see "Testing status for slice 4").
3. **verify parity: done 2026-11-14.** `FHR_ATTACH`'s join and the Dockstore test
   profile behave identically without `--type` (all combine outputs and fixture names
   infer correctly; the native `test` profile produced the five `verify/<id>.verify.txt`
   reports with `Checksum verified.`); the report keeps its `file: <path>` header under
   the prefix-named output; the harness failure substrings (`checksum`, `after sequence
   data`, `duplicate key`, `proteome`) still appear because they are toolkit messages.
   The extension-inference delta was pinned as an observable change: a header-carrying
   `sample.txt` now fails in the task with `FHR: Unsupported file extension` where the
   local module forced `--type fasta` (new `tests/run.py` case). Callers stay on the
   unchanged include paths — the pinned tree overlays the local module at the canonical
   path, so the switch is the install itself (documented in the verify contract table).
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
   **Done 2026-11-13 (option (a)):** `modules/convert` and `modules/combine` were deleted in
   the same change once every caller, test and doc was migrated (migration preceded the
   deletion — see the slice-3 "Testing status"). The local `verify` main.nf was **not** part
   of that deletion: it stayed repository-owned with its nf-test setups retargeted from the
   retired `FHR_COMBINE` to the pinned upstream `FAIRBIOHEADERS_COMBINE` (reports recorded
   `file: <id>.<ext>`), pending step 3.
   **Done 2026-11-14 (slice 4):** step 3 passed, and the local verify implementation was
   retired by installing the byte-identical upstream tree over the same canonical path
   (no separate deletion step exists for it: the retired files survive only in git history
   and the drift checker proves no local bytes remain). Its 5-case nf-test suite and inline
   fixtures were replaced by the merged upstream 4-case suite; the coverage the upstream
   suite does not carry was ported to `tests/run.py` (verify contract table).
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
  **Answered for this repository 2026-11-13: input-faithful names (option (a)).** The
  compat modules are retired here; the shared-standard question still stands for #7 but no
  longer blocks this suite.
- The upstream convert output extension is the `--to` token, so the standard above has
  a second consequence: whether **protein FASTA keeps a distinct extension** in the
  shared modules (`faa` is a valid FASTA extension here and in the toolkit's own
  naming, but not a `--to` choice). If the family wants `.faa`, upstream
  `fairbioheaders/convert` needs either a `faa` alias or a way to set the extension
  separately from `--to` (convert blocker 2).
  **Resolved for this repository 2026-11-13 by capitulation:** header-only protein
  conversions land on `.fasta` and the protein/genome distinction moves to `meta`. The
  upstream enhancement that would let the family keep a distinct `.faa` is drafted below
  ("Staged upstream follow-up") — **not filed, maintainer's call.**

## Staged upstream follow-up (NOT filed — maintainer's call)

The following is a *draft* request to nf-core/modules for `fairbioheaders/convert`, kept
here so the family can benefit if upstream ever accepts it. It is **not** filed against
nf-core/modules and does **not** gate this repository, which has already capitulated to the
current upstream naming (option (a)). Filing it is a maintainer action.

> **Title:** `fairbioheaders/convert`: decouple the output extension from `--to`, or accept
> `faa` as a FASTA alias
>
> **Body:** The merged `fairbioheaders/convert` module uses the `--to` token as both the
> conversion target *and* the output file extension (`${prefix}.${format}`), and the toolkit
> `bioheaders convert --to` set is `json yaml jsonld html fasta gfa gff3` — there is no `faa`
> choice (`--to faa` exits 2 with `invalid choice: 'faa'`). This makes it impossible for the
> module to emit a header-only **protein** output named `*.faa`, which is the conventional
> protein-FASTA extension (the toolkit itself and the `fairbioheaders` fixture data both use
> `.faa`; the toolkit's own combine keeps `.faa` because it preserves the input extension).
> Two small, backwards-compatible options, either of which would let downstream family
> conventions (e.g. FAIR-bioHeaders-Nextflow) keep a distinct protein header extension:
>
> 1. Accept `faa` as an alias of `--to fasta` (produce the same FASTA bytes, use `.faa` as
>    the extension), or
> 2. Add an `ext.outputExtension` (or rename the emit to a full `${prefix}.${ext}` hook) so
>    the importing project can set the extension independently of `--to`, mirroring how
>    `combine` already keeps the input's extension.
>
> This is a naming/ergonomics request only; the conversion semantics are unaffected. FAIR-
> bioHeaders-Nextflow #29 (option (a)) adopted the current behavior in the meantime.
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
  **Decided 2026-11-14 (maintainer decision 6B): dual-test.** The `nf-test` CI job is a
  matrix over both (`nxf_version: ['26.04.6', '26.10.4']`, `fail-fast: false`), so
  snapshot-baseline drift is a named CI result instead of a host property. The baseline
  itself is **not** bumped: 26.04.6 stays the suite's supported version (README,
  `nextflow.config`, the `test` and `dockstore-workflow` jobs); 26.10.4 is exercised only as
  the baseline the pinned upstream snapshots were recorded under. Bumping the supported
  baseline remains a #7 compatibility-matrix decision with its own pin review.
  **First-run result (PR #34 CI, run `43617282873`, head `1cc979f`, 2026-11-14).** The two
  legs resolved genuinely different engines — the Record step printed `nextflow 26.04.6
  build 12646` and `nextflow 26.10.4 build 14435`, both under nf-test 0.9.5 — and reported
  `SUCCESS: Executed 30 tests in 216.39s` on 26.04.6 versus `FAILURE: Executed 30 tests in
  151.763s (2 failed)` on 26.10.4. **All 22 committed snapshots matched on both engines —
  the drift this matrix was built to catch did not appear.** The two red assertions are not
  snapshot tests: `sarscov2 - fhr yaml - yaml - same input and output names - fails` and its
  `- stub` twin in the pinned `modules/nf-core/fairbioheaders/convert/tests/main.nf.test`
  assert `process.stdout.toString().contains("Input and output names are the same")`, and
  26.10.4 writes the Nextflow log — the `ERROR ~ Error executing process` block included —
  to **stderr**, so on that leg `process.stdout` is empty (`[]`) even though the module's
  name-collision guard fires identically (`Caused by: Input and output names are the same,
  set prefix in module configuration to disambiguate! -- Check script
  '.../fairbioheaders/convert/main.nf' at line: 27`, and line 40 under `-stub`). The
  assertion therefore pins a Nextflow log-stream behavior, not the module contract, and it
  moved between the two baselines. These two are the only stdout-**alone** failure assertions
  among the eight stream-reading ones across the four pinned suites; the other six read
  `(process.stdout + process.stderr)` and passed on both legs — the asymmetry is the defect.
  A native local run of the convert file under `NXF_VER=26.10.4` in the verification
  container reproduced both failures identically (`Executed 11 tests in 677.086s (3 failed)`;
  the third failure, `sarscov2 - fasta - no header - fails`, sees empty streams on this
  host's emulated native executor — a local-environment artifact, since that case is
  stream-agnostic and passes in both CI legs). **Disposition:** the correct fix is a
  stream-tolerant assertion **upstream** (match on stdout *or* stderr, like the other six),
  adopted here by moving the convert pin through the recorded procedure — it joins the staged,
  unfiled upstream requests above (filing is a maintainer action, standing posture unchanged). Until then
  the 26.10.4 leg stays red on this PR as a named compatibility finding; it is **not** to
  be silenced by editing the pinned test, by skipping the two cases, or by making the leg
  advisory. Bumping the supported baseline to 26.10.4 would *not* fix it either — the same
  assertion fails under that engine regardless of which baseline is called supported.
- **The layout migration is #7's now** (decision 6A, 2026-11-14): moving `modules/*` →
  `modules/local/` plus every importer path is what makes `nf-core modules update`,
  `list local` and `lint` usable in this repository, and it pairs with the next toolkit bump
  because that bump is when the container pins are re-evaluated anyway. Until it lands, the
  CLI-less fetch procedure and the manifest-driven drift check above stay the only
  supported way to touch a pinned module.
- **FHT stays draft-only and opt-in here** until it has a released contract: no FHT-named
  module, output name, fixture set or README support claim takes release form (rule V7 in
  FAIR-bioHeaders-Specification). Any FHT composition in this suite must be explicitly
  labelled draft, off by default, and pinned to the draft contract, and the upstream module
  set must not be asked to claim family completeness on FHT's behalf.
