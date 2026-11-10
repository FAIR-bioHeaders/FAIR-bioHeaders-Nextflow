# Module migration: upstream nf-core `fairbioheaders` modules (issue #29)

This document tracks the migration of this repository's Nextflow workflows to the
upstream [nf-core/modules](https://github.com/nf-core/modules) `fairbioheaders`
module set, the pinned revisions, the per-module contract comparison against the
local implementations, and the remaining adoption steps. It exists because the
upstream modules and the repository modules intentionally diverged during
development (#21 consolidation, then the upstream submissions) and must be
reconciled without silently dropping documented behavior.

Status date: **2026-11-10** (all upstream state below was re-verified against the
GitHub API on this date; re-check before acting on it — checkouts and PRs move).

## Upstream state (verified 2026-11-10)

| Upstream module | PR | State | Revision |
| --- | --- | --- | --- |
| `fairbioheaders/combine` | [nf-core/modules#13492](https://github.com/nf-core/modules/pull/13492) | merged 2026-11-09 | `8faff34023b16ecdc41b02bac42989834075e3f1` |
| `fairbioheaders/validate` | [nf-core/modules#13509](https://github.com/nf-core/modules/pull/13509) | merged 2026-11-09 | `86e852ef429e021d16f7279aaddb9b81eb067f8a` (contained in `8faff340…`) |
| `fairbioheaders/verify` | [nf-core/modules#13635](https://github.com/nf-core/modules/pull/13635) | **open, in review** | head at review time `bb6c49233b2f4ce467b7e332dcfc2c1608e35067` (a moving PR branch, not a merge revision) |
| `fairbioheaders/convert` | [nf-core/modules#13636](https://github.com/nf-core/modules/pull/13636) | **open, in review** | head at review time `639dd3cc9944998ced3bb69efac57f8f99438ee5` (a moving PR branch, not a merge revision) |

Shared test fixtures landed in [nf-core/test-datasets#2363](https://github.com/nf-core/test-datasets/pull/2363);
they resolve under `modules_testdata_base_path` at
`genomics/sarscov2/genome/fairbioheaders/` and
`genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/fairbioheaders/`
(verified present on the `modules` branch 2026-11-10).

Per the issue, this slice adopts **combine** and **validate** only. **verify** and
**convert** are documented here but NOT adopted: their interfaces are still
reviewed upstream, and adoption is gated on merge **plus** local parity checks
(section "Adopting verify and convert after their merge").

## How the upstream modules are pinned

- `modules/nf-core/fairbioheaders/combine/` and `modules/nf-core/fairbioheaders/validate/`
  (with `meta.yml`, `environment.yml`, `tests/main.nf.test` and the snapshot) are
  **byte-identical copies** of the upstream files at the recorded revisions.
  They must stay unpatched: repository behavior goes into repository-owned
  modules (`modules/*`) or subworkflows (`subworkflows/*`), never into the pinned
  copies.
- `modules.json` records the nf-core/modules remote, the per-module
  `git.commit_sha` and the branch, in the standard pipeline layout, so the
  `nf-core` CLI can manage updates. `.nf-core.yml` declares
  `repository_type: pipeline`.
- CI (`nf-test` job) verifies byte-identity against `modules.json` by hashing the
  files fetched from `raw.githubusercontent.com/nf-core/modules/<sha>/…`
  (`git hash-object`); any local edit or stale pin fails the drift step.

Provenance of the installed files (git blob digests of every installed file at its
recorded revision, matching `git hash-object` of the checked-in copies):

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

### Updating a pinned module (recorded procedure)

Preferred, with the `nf-core` CLI (>= 2.x / 3.x) from the repository root:

```sh
# 1. See what changed upstream since the recorded revision, and review it:
#    https://github.com/nf-core/modules/compare/<recorded-sha>..<new-sha>
#    restricted to modules/nf-core/fairbioheaders/<name>/
nf-core modules info fairbioheaders/combine        # current pin and available version
nf-core modules update fairbioheaders/combine --git_sha <new-sha>
nf-core modules update fairbioheaders/validate --git_sha <new-sha>
# 2. Re-run the suites listed in the "Testing status" section below.
# 3. Keep the pins coherent: the module's environment.yml (bioconda) and its
#    container tag must match the toolkit release this repository pins
#    (currently fair-bioheaders 0.9.0). CI checks both directions.
# 4. Commit the module files and the modules.json sha change together and
#    reference #29; update this document's revision table.
```

Without the CLI (offline mirror — reproduces exactly what this slice did):

```sh
sha=<new-sha>; mod=<combine|validate>
for f in main.nf meta.yml environment.yml tests/main.nf.test tests/main.nf.test.snap; do
  gh api "repos/nf-core/modules/contents/modules/nf-core/fairbioheaders/$mod/$f?ref=$sha" \
    --jq .content | base64 -d > "modules/nf-core/fairbioheaders/$mod/$f"
done
# then update modules.json (per-module and repo-level git.commit_sha) and verify:
git hash-object modules/nf-core/fairbioheaders/$mod/main.nf   # must equal the upstream blob sha
```

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

Not adopted (gated on the open PR). Contract differences between the local module
and the PR head reviewed on 2026-11-10 (`bb6c492`, a moving branch — re-diff at
merge time):

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

### `fairbioheaders/convert` — upstream PR #13636 (open) vs local `FHR_CONVERT` (kept)

Not adopted. Differences between local `modules/convert/` and the PR head
(`639dd3c`, moving branch — re-diff at merge time):

| Aspect | Upstream PR head | Local | Notes |
| --- | --- | --- | --- |
| Input | two-row: `tuple val(meta), path(input)` **and** `val(format)` (pair with `Channel.combine`/`fromZip` style wiring) | single tuple `(meta, metadata, format)`, `stageAs: 'input/*'` | **channel-contract break** for external importers of `FHR_CONVERT` |
| Output | `(meta, ${prefix}.${format})` | `(meta, ${meta.id}.fhr.${format})` — the `.fhr.` infix is part of the documented harness markers (`{sample}-header.fhr.faa`, `EXTRACTED {sample} {sample}.fhr.json`) | differs; adoption needs rename or contract change |
| Command | `bioheaders convert --to <format>` with `--to` placed after `ext.args` so the input format wins | `fhr-convert` (the toolkit's legacy entry point) with a native format whitelist (`fhrFormat`) | upstream guards `ext.args` conflicts; local rejects unknown formats before launch (`Unsupported format 'exe'` harness case) |
| Formats | json/yaml/html/jsonld (+ extract from FASTA/GFA/GFF3 — tests extract headers) | json/yaml/html/fasta/faa/gfa | overlapping but not equal sets |
| Containers/quoting/version reporting | Wave; prefix double-quoted; same versions tuple | quay/depot; full quoting; same versions tuple | same pattern as above |
| nf-tests | 11 cases incl. jsonld emit, `--to overridden`, spaced names, header extraction from FASTA | n/a (covered by `tests/run.py` round-trips) | adoption gate |

`FHR_CONVERT` (used by the example and as `FHR_ATTACH`'s JSON-extraction step)
stays in place and is **migration-pending**.

## Role separation (kept explicit)

| Job | Module | Owner |
| --- | --- | --- |
| Attach metadata + exact-byte checksum (`bioheaders combine`) | `FAIRBIOHEADERS_COMBINE` (pinned upstream), `FHR_COMBINE` (compat, family names) | upstream + repo |
| Verify a **headed sequence file** (schema + checksum of the file) | `FAIRBIOHEADERS_VERIFY` | repo, migration-pending |
| Validate **standalone metadata** (schema only, no checksum/sequence) | `FAIRBIOHEADERS_VALIDATE` (pinned upstream) | upstream |
| Verify **parent links** (`derivedFrom`/`genomeReference` against candidate parents, `bioheaders verify-links`) | `FHR_VERIFY_LINKS` | repo-owned, no upstream counterpart |
| GFF3 syntax/SO/biology rules | `GFF3_VALIDATE` (gff3-validator 0.1.0) | repo-owned, no upstream counterpart |
| Metadata conversion / header extraction (`fhr-convert`) | `FHR_CONVERT` | repo, migration-pending |
| Native JSON creation, stripping, converter pytest gating | `FHR_CREATE_JSON`, `FHR_STRIP`, `FHR_CONVERTER_TESTS` | repo-owned |

## Caller migration status

| Caller | Uses | Status |
| --- | --- | --- |
| Standalone example `main.nf` | `FHR_ATTACH` → `FHR_COMBINE` + local `FAIRBIOHEADERS_VERIFY`; `FHR_CREATE_JSON` → pinned `FAIRBIOHEADERS_VALIDATE` | combine/verify held on compat (naming gap); **validate migrated** |
| `subworkflows/attach` (`FHR_ATTACH`) | `FHR_COMBINE` + `FAIRBIOHEADERS_VERIFY` + `FHR_CONVERT` | external channel contract and output names unchanged; internals retargeted to the compat combine |
| Dockstore workflow `workflows/fairbioheaders` | `FHR_COMBINE` + `FAIRBIOHEADERS_VERIFY` | outputs (`combine/<id>.fhr.fa`, `combine/<id>.fhp.faa`, `verify/<id>.verify.txt`) unchanged; descriptor `.dockstore.yml` paths unchanged and still resolve |
| `modules/create_json` | pinned `FAIRBIOHEADERS_VALIDATE` | migrated in place |
| External direct importers | `modules/nf-core/fairbioheaders/{combine,validate,verify}` | **combine's observable naming contract changes at the canonical path** — see the migration note below |

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

## Testing status for this slice (2026-11-10) and commands CI/maintainers must run

Environment on the development host: Docker 29.9.3 available; **no** host
`nextflow`, `nf-test`, `nf-core` CLI or usable Java runtime (the `/usr/bin/java`
stub reports no runtime), so Nextflow-version-gated suites could not be executed
in this slice. Upstream state, pins, blob digests, fixture availability, channel
signatures and every include/publish wiring were checked statically instead.

Commands required to close the executable test matrix (the CI jobs run exactly
these; the branch must be green there before merge):

```sh
nf-test test --profile docker --ci            # pinned upstream combine/validate tests (test-datasets fixtures) + FHR_COMBINE compat tests
python tests/run.py --converter-source <fair-bioheaders-0.9.0-checkout>   # incl. new FHR 2.1 x- validate cases; native mode, bioheaders on PATH
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results   # Dockstore entry: family-named combine outputs + verify reports
nextflow run main.nf -profile docker --sequence examples/assembly.gfa --sequence_format gfa   # and the FASTA/GFF3/protein examples as in ci.yml
nf-core modules lint fairbioheaders/combine fairbioheaders/validate       # from a nf-core modules-type checkout (pipeline lint via modules.json is the alternative)
git diff --check
```

FHR → FHGFF3 → FHP parent-chain coverage was re-checked in the form this slice
can verify locally: the chain fixtures (`tests/fixtures/fhp/chain/`), the
`FHR_VERIFY_LINKS` harness cases and the protein attach markers in
`tests/run.py` are unchanged and still exercise combine→verify→extract→verify-links
through the compat module; the chain does not depend on the pinned validate module
for parent checks.

## Adopting verify and convert after their merge

Gate (from #29): adopt only after the upstream interfaces **merge** and **pass
local parity** — no adoption on review heads.

1. Re-read the merged revisions (do not reuse the PR-head SHAs above) and re-diff
   `modules/nf-core/fairbioheaders/verify|convert` against the merged upstream
   files at those SHAs, plus this document's tables (PR branches moved since).
2. Install combine-style: byte-identical files at recorded SHAs in `modules.json`;
   run the drift step; run the upstream nf-tests (`nf-test test --profile docker`).
3. **verify parity:** confirm `FHR_ATTACH`'s join and the Dockstore test profile
   behave identically without `--type` (odd-extension rejection), that the report
   names/content keep the `file:` header, and that the harness failure substrings
   (`checksum`, `after sequence data`, `duplicate key`, `proteome`) still appear.
   Then switch `subworkflows/attach`, the Dockstore workflow and the README import
   examples from the local file to the pinned module **only if** the family-named
   combine outputs still match verify's extension inference (they do: `.fhr.fa`,
   `.fhp.faa`, `.fhr.gfa`, `.fhgff3.gff3` all infer correctly) — document the
   switch.
4. **convert parity:** decide the `.fhr.` infix question: either keep
   `FHR_CONVERT` for the example/attach (its names are documented harness
   markers) and adopt `fairbioheaders/convert` as the importer-facing module, or
   migrate callers with an explicit rename step and a contract-change CHANGELOG
   entry. The two-row input shape also needs channel rewiring at every call.
5. Only after callers are migrated, delete the duplicate local implementations
   (`modules/convert` once #4 resolves; `modules/combine` once the naming blocker
   resolves; the local `verify` main.nf once step 3 passes).
6. Re-evaluate container pins at each toolkit bump: `nf-core modules update`
   maintains the Wave side; the repo-side Bioconda/BioContainers/depot trio and
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
  (blocker 1 above).
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
