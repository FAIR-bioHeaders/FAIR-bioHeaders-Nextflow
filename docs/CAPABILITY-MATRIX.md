# Capability matrix: module × operation × type × serialization × version

**Approved exact-pin exception — 2026-11-19.** David Molik explicitly approved
using the complete convert module from [upstream PR #13819](https://github.com/nf-core/modules/pull/13819)
at immutable review head `32d7eadd1f53d15cc203e2a52c4b7b83fb7a1d50` to repair
PR #38 CI, including its safe-prefix restriction. This source was unmerged at
approval; it must not be described as a merged revision. The exception covers
only this convert pin, not future review heads or other modules. The normal
merged-source procedure in `docs/module-migration.md` remains unchanged. Combine, validate and verify,
toolkit 0.9.0 and all container/environment pins are unchanged.

Convert now rejects prefixes outside `[A-Za-z0-9._+][A-Za-z0-9._+ -]*`, and the
exact prefix `..`, in both script and stub. This excludes non-ASCII characters,
path separators, shell metacharacters and leading spaces/hyphens; ordinary safe
names and internal spaces remain supported. Both collision tests still require
process failure and now accept the diagnostic on either stdout or stderr.

Local validation: all 13 convert tests passed on each of Nextflow 26.04.6 and
26.10.4 with nf-test 0.9.5 and toolkit 0.9.0, using native tasks inside the
verification container. This is separate from the full 32-case Docker-profile
CI matrix, which must pass before merge. All 29 installed files match their
recorded immutable upstream blobs.


Status date: **2026-11-20**. The primary tables retain the named toolkit **0.9.0 pinned baseline**. The separate [five-type native handoff](FIVE-TYPE-HANDOFF.md) records new specification artifacts and explicitly named runtime evidence. This is the honest capability statement of
FAIR-bioHeaders-Nextflow (the DSL2 suite, repository version **0.3.0**, last published
release 0.2.0). It exists so that a gap is a named row rather than an inference, and so
that no summary of "covers FHR, FHP, FHGFF3, FHT and FHGM" can be read into this suite:
**a five-type claim requires its named runtime.** FHT contract 1.0 is published in shared v0.7.0 and native FHGM0.1 in shared v0.8.0; the pinned 0.9.0 runtime does not acquire their support from those publications ([publication authority](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification)).

Published per FAIR-bioHeaders-Specification#211 item 5 ("Publish per-library and
toolkit/Nextflow type × operation × serialization × version matrices. Track unsupported
operations/formats explicitly"). It is the current-matrix half of
[issue #35](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Nextflow/issues/35)
first acceptance item. #35 was historically closed; actual runtime, pin and five-type acceptance remains tracked in #7, and is not inferred from that historical state.

## How to read this matrix

Cell vocabulary (nothing outside this list is a legal first word of a matrix cell):

| mark | meaning |
| --- | --- |
| `tested` | the cell is exercised by a named test in this repository or by a CI command with an assertion — the citation in the cell must resolve |
| `partial` | tested for a stated subset; the remainder is named in the cell |
| `not tested` | no test or CI case exercises it; the reason follows. Never blank, never assumed |
| `unsupported` | the suite refuses this by contract (whitelist, naming rule); the refusal itself is cited where it is pinned by a test |
| `n/a` | the cell is not a thing this surface could do for that type; the reason follows |
| `not tested` for the pinned baseline | published FHT/native-FHGM contracts exist, but toolkit 0.9.0 lacks their final bundles and cannot earn support from those publications |

Every `tested` and `partial` cell carries an evidence citation in backticks: a
repository-relative file path, the separator ` :: `, and verbatim text (whitespace
collapsed) that file actually contains. The citation grammar exists so it
can be checked mechanically; `scripts/check_capability_matrix.py` verifies that every
citation resolves against the working tree, that no tested/partial cell is cited by
nothing, that the FHT and FHGM columns cannot claim execution on the unpromoted0.9.0 baseline, that the pin values below agree byte-wise with the environment files, and that
every process and named workflow in `modules/`, `modules/nf-core/` and `subworkflows/`
has a row here. CI runs the check plus `--self-test`, which mutates a copy of this file
(a fake citation, a citation-free `tested` cell, a perturbed pin, an FHT cell marked
`tested`, a blanked cell) and fails unless **every** mutation is caught — so this guard
cannot rot into a no-op.

This table is hand-authored (the axes are judgment calls about semantics) but
**mechanically drift-checked**: run `python3 scripts/check_capability_matrix.py` from the
repository root after touching any module, pin, test or this file. A cell that loses its
evidence turns CI red rather than quietly lying.

Test lanes referenced below (all run in [CI](../.github/workflows/ci.yml)):

- **nf-test** — `nf-test test --profile docker --ci` over the four pinned upstream
  suites, matrix over Nextflow 26.04.6 and 26.10.4 (`.github/workflows/ci.yml ::
  nxf_version: ['26.04.6', '26.10.4']`). 32 tests total.
- **harness** — `python tests/run.py` (job `test`): positive and rejection pipeline runs
  from an external project against the hash-locked native environment.
- **example** — `nextflow run main.nf -profile docker` steps
  (`.github/workflows/ci.yml :: Docker GFF3 example` and siblings).
- **dockstore** — `nextflow run workflows/fairbioheaders/main.nf -profile test,docker`
  (`.github/workflows/ci.yml :: test -s results/combine/proteins.faa`).
- **guard** — pin-consistency greps and `python3 scripts/check_upstream_modules.py`
  (byte identity of the pinned trees against `modules.json`).

## 1. Component inventory (the module axis, enumerated from the tree)

| component | path | processes / workflows | provenance | tested by |
| --- | --- | --- | --- | --- |
| `FAIRBIOHEADERS_COMBINE` | `modules/nf-core/fairbioheaders/combine` | `FAIRBIOHEADERS_COMBINE` | **pinned upstream** nf-core/modules `def10bc21ae4952973f9e07952fc899aa060dfc5` (`modules.json :: def10bc21ae4952973f9e07952fc899aa060dfc5`); never patch locally | nf-test (8 cases), harness, example, dockstore, guard |
| `FAIRBIOHEADERS_CONVERT` | `modules/nf-core/fairbioheaders/convert` | `FAIRBIOHEADERS_CONVERT` | **pinned upstream (approved unmerged exception)** `32d7eadd1f53d15cc203e2a52c4b7b83fb7a1d50` (`modules.json :: 32d7eadd1f53d15cc203e2a52c4b7b83fb7a1d50`) | nf-test (13 cases), harness, example (as the aliased `FHR_YAML` publish) |
| `FAIRBIOHEADERS_VALIDATE` | `modules/nf-core/fairbioheaders/validate` | `FAIRBIOHEADERS_VALIDATE` | **pinned upstream** `def10bc21ae4952973f9e07952fc899aa060dfc5` (`modules.json :: def10bc21ae4952973f9e07952fc899aa060dfc5`) | nf-test (7 cases), harness |
| `FAIRBIOHEADERS_VERIFY` | `modules/nf-core/fairbioheaders/verify` | `FAIRBIOHEADERS_VERIFY` | **pinned upstream** `def10bc21ae4952973f9e07952fc899aa060dfc5` (`modules.json :: def10bc21ae4952973f9e07952fc899aa060dfc5`), adopted 2026-11-14 by issue #29 slice 4 (`docs/module-migration.md :: verify parity: done 2026-11-14`) | nf-test (4 cases), harness, example, dockstore, guard |
| `FHR_CREATE_JSON` | `modules/local/create_json` | `FHR_CREATE_JSON` (wraps `FHR_WRITE_JSON`, then the pinned `FAIRBIOHEADERS_VALIDATE` as `VALIDATE_CREATED_JSON`) | repository-owned | harness (integration, FHP compose, FHR/FHP rejections), example |
| `FHR_STRIP` | `modules/local/strip` | `FHR_STRIP` | repository-owned | harness (integration bytes, FHP bytes) |
| `FHR_VERIFY_LINKS` | `modules/local/verify_links` | `FHR_VERIFY_LINKS` | repository-owned (wraps `bioheaders verify-links`) | harness (match/mismatch/unchecked/chain), example |
| `GFF3_VALIDATE` | `modules/local/gff3_validate` | `GFF3_VALIDATE` | repository-owned (wraps gff3-validator 0.1.0, which is not on Bioconda yet — bioconda/bioconda-recipes#70098) | harness (plain/gzip/BIO/STR/incomplete/lenient), example |
| `FHR_CONVERTER_TESTS` | `modules/local/converter_tests` | `FHR_CONVERTER_TESTS` (wraps `FHR_RUN_CONVERTER_TESTS`, `FHR_CHECK_CONVERTER_TESTS`) | repository-owned (runs the toolkit's own pytest) | harness (`--converter-source` gate, failure and version-mismatch cases), example |
| `modules/local/utils/main.nf` | `modules/local/utils` | none (Groovy helpers: serialization, quoting, ID/format whitelists) | repository-owned; not a schema validator | harness (JSON edge-case script, rejection messages) |
| `FHR_ATTACH` | `subworkflows/attach` | `FHR_ATTACH` | repository-owned; composes the pinned combine, verify (`CHECK_COMBINED`) and convert (`EXTRACT_JSON`) | harness, example |
| example pipeline | `main.nf` | anonymous workflow | repository-owned | harness, example lane |
| Dockstore workflow | `workflows/fairbioheaders` | anonymous workflow composing combine + verify over a samplesheet | repository-owned (`.dockstore.yml`) | dockstore lane |

**Local modules versus pinned upstream modules (the duplication question).** There are no
remaining duplicates. The repository's header-family compatibility modules `FHR_COMBINE`
(`modules/combine`) and `FHR_CONVERT` (`modules/convert`) were deleted on 2026-11-13 when
issue #29 option (a) migrated every caller to the pinned upstream modules
(`docs/module-migration.md :: were deleted in the same change`), and the repository's own
verify implementation was retired under the same canonical path by the pinned upstream
module on 2026-11-14 (`docs/module-migration.md :: verify parity: done 2026-11-14`). Every
repository-owned component left in the table does a job no upstream module has
(`create_json`, `strip`, `verify_links`, `gff3_validate`, `converter_tests`, `utils`,
`FHR_ATTACH`); upstream submissions for the missing `verify-links` module and the
GFF3-rule packaging gap are staged as questions for #7, not filed
(`docs/module-migration.md :: has no upstream module; if #7 wants`).

**nf-test lane scope.** nf-test exists **only** for the four pinned upstream modules
(`modules/nf-core/fairbioheaders/*/tests/main.nf.test`). `verify_links` and
`gff3_validate` have **no nf-test**; they are exercised by the harness and the Docker
example in the `test` job instead. This is a named gap, not parity between lanes: see
item 4 of the open items.

## 2. Matrix A — operation × type

Operations are the suite's jobs; columns are the header families. FHT/FHGM columns may
never read `tested`/`partial` (rule V7; enforced by the checker).

| operation | FHR | FHP | FHGFF3 | FHT | FHGM |
| --- | --- | --- | --- | --- | --- |
| build standalone metadata JSON from a field map (`FHR_CREATE_JSON`) | tested — full map round trip and rejection cases `tests/run.py :: expected seven round-trip markers`; `tests/run.py :: unsupported type java.util.Date` | tested — predicted/database/mixed `tests/run.py :: CREATED {sample}` | not tested — no harness case sends an FHGFF3 field map through `FHR_CREATE_JSON`; standalone FHGFF3 metadata validation is covered one layer down, on the pinned module (next row) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| validate standalone metadata (`FAIRBIOHEADERS_VALIDATE`) | tested — JSON and YAML, plus FHR 2.1 `x-` acceptance and its FHR 2.0 rejection `tests/run.py :: x-example-pipeline` | tested — `modules/nf-core/fairbioheaders/validate/tests/main.nf.test :: test("sarscov2 - fhp - yaml")`; required-field and bad-sourceType rejections `tests/run.py :: FHP metadata was not validated` | tested — `modules/nf-core/fairbioheaders/validate/tests/main.nf.test :: test("candidatus_portiera_aleyrodidarum - fhgff3 - yaml")`; JSON input n/a for this suite because the only case is YAML (see Matrix B, JSON/FHGFF3) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| attach a header to a sequence file (`FAIRBIOHEADERS_COMBINE`; composed by `FHR_ATTACH`) | tested — FASTA, gzip FASTA and GFA `modules/nf-core/fairbioheaders/combine/tests/main.nf.test :: test("sarscov2 - fasta.gz - fhr")`; exact-byte strip round trip after attach `tests/integration.nf :: ASSERT_BYTES` | tested — `modules/nf-core/fairbioheaders/combine/tests/main.nf.test :: test("sarscov2 - faa - fhp")`; gzip `.faa` attach `tests/run.py :: ATTACHED predicted predicted.faa.gz` | tested via the pinned module — `modules/nf-core/fairbioheaders/combine/tests/main.nf.test :: test("candidatus_portiera_aleyrodidarum - gff3 - fhgff3")` and the dockstore gff3 row; GFF3 through `FHR_ATTACH` is additionally exercised in the separate named native lane `tests/family_integration.nf :: FHR_ATTACH(FHR_CREATE_JSON.out.json.map` | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| verify checksum + schema of a headed file (`FAIRBIOHEADERS_VERIFY`) | tested — `modules/nf-core/fairbioheaders/verify/tests/main.nf.test :: test("sarscov2 - fasta - fhr")`; tamper, late-header and concatenation rejections `tests/run.py :: after sequence data`. GFA verified by the dockstore row. Unknown extensions fail in-task `tests/run.py :: Unsupported file extension` | tested — `tests/run.py :: FHP FASTA was not verified`; malformed headers `tests/run.py :: malformed-missing-proteome` and `tests/run.py :: malformed-duplicate-checksum` | tested — `tests/run.py :: FHGFF3 was not verified` (the `.gff3` extension infers the GFF3 reader) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| extract / convert a header or metadata record (`FAIRBIOHEADERS_CONVERT`) | tested — `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("sarscov2 - gfa - fhr - json")`; extracted-JSON sidecars of attached files `tests/run.py :: example/sequence/example.gfa` | tested — header extraction `tests/run.py :: header extraction lost FHP metadata`; JSON-LD serialization `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("sarscov2 - faa - fhp - jsonld")` | partial — header extraction from a headed `.gff3` file is **not tested** by any case in this suite (the upstream convert cases take standalone metadata or FASTA/GFA inputs); YAML-from-metadata conversion is tested `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("candidatus_portiera_aleyrodidarum - gff3 - fhgff3 - yaml")` | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| strip a header (`FHR_STRIP`) | tested — FASTA and GFA byte-exact `tests/integration.nf :: ASSERT_BYTES` | tested — `tests/run.py :: STRIPPED {sample}`; byte equality gate `tests/run.py :: protein strip byte checks did not run` | unsupported — `kind` whitelist `modules/local/strip/main.nf :: fhrFormat(kind,`; no GFF3 strip path exists in this suite | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| verify parent links by checksum (`FHR_VERIFY_LINKS`) | not tested — no FHR fixture records `derivedFrom`; the command surface is shared with FHP (`modules/local/verify_links/main.nf :: 'fasta', 'faa', 'gfa', 'gff3'`) but only cited paths below are exercised | tested — match, mismatch, unchecked, `require_all` and `fail_on_mismatch` `tests/run.py :: matching parent was not verified`; `tests/run.py :: ext.require_all = true` | tested — genome→annotation link `tests/run.py :: genome-annotation link did not match` (asserted as the emitted `VERIFIED annotation` pass case) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| validate GFF3 syntax/SO/biology rules (`GFF3_VALIDATE`, gff3-validator 0.1.0) | n/a — FHR records are FASTA/GFA, never GFF3 | n/a — FHP records are protein FASTA, never GFF3 | partial — rule validation is tested on plain and gzip GFF3 with and without a genome `tests/run.py :: canonical-gene-gzip.gff3.gz`, `tests/run.py :: BIO-008`, `tests/run.py :: GFF-STR-001`, incomplete-input and lenient/strict gates `tests/run.py :: validation incomplete`; the **FHGFF3 header hook** (`ext.header require/skip`) is not tested — no harness fixture combines a `#~` block with this module | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted — an FHGM-carrying file is validated as its enclosing FHGFF3 file; the model layer is #35's open lane | n/a for a standalone lane here — see the FHGM column reason |
| run the toolkit's own pytest suite (`FHR_CONVERTER_TESTS`) | partial — the gate, failure and version-mismatch surfaces are tested (`tests/run.py :: Converter wrapper:`, `tests/run.py :: converter source version is '0.0.0'`); the suite's internal coverage belongs to FAIR-bioHeaders-Tools, not this matrix | partial — the run is type-agnostic; same harness evidence, `tests/run.py :: Converter tests failed` gates publication | partial — the toolkit 0.9.0 suite the pinned checkout runs is whatever that release contains (`tests/run.py :: Converter wrapper:`); this lane claims no per-type coverage of its own | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| example pipeline end to end (`main.nf`) | tested — FASTA and GFA attach, batch metadata with per-ID JSON+YAML `tests/run.py :: alpha/metadata/alpha.yaml` | tested — `tests/run.py :: protein example is not an FHP header`; `.faa` publish `tests/run.py :: ATTACHED {sample} {sample}.faa` | partial — GFF3 validation and verify-links paths run through `main.nf` (`tests/run.py :: Duplicate meta.id from GFF3 files`), but attaching FHGFF3 metadata to a GFF3 sequence is not exposed by `main.nf` (the `--sequence_format` value would be rejected by `FHR_ATTACH`'s kind whitelist) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| Dockstore workflow end to end (`workflows/fairbioheaders`) | tested — FASTA, GFA and expanded-JSON-LD metadata rows all verify `workflows/fairbioheaders/assets/test/samplesheet.csv :: jsonld,minimal.fhr.expanded.jsonld,genome.fa` | tested — `workflows/fairbioheaders/assets/test/samplesheet.csv :: proteins,../../../../examples/protein-metadata.json,../../../../examples/protein.faa` | tested — `workflows/fairbioheaders/assets/test/samplesheet.csv :: gff3,annotation.fhgff3.yaml,no-header.gff3` with `Checksum verified.` asserted in CI | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |

## 3. Matrix B — metadata serialization × type

The toolkit's `bioheaders convert --to` token set is `json yaml jsonld html fasta gfa
gff3` — there is **no `faa` token**, and the pinned upstream convert uses the token as the
output extension, so a header-only protein file lands on `.fasta`
(`tests/run.py :: invalid choice: 'faa'` pins the rejection in-task). Cells below cover
**both directions** (read and write) for that serializer; a one-directional gap is named.

| serialization | FHR | FHP | FHGFF3 | FHT | FHGM |
| --- | --- | --- | --- | --- | --- |
| JSON | tested both ways — input to create/combine/validate; extracted-JSON sidecar on publish `tests/run.py :: alpha/metadata/alpha.json` | tested both ways — standalone input `tests/run.py :: FHP metadata was not validated`; header extraction `tests/run.py :: cvt-extract` | not tested — no JSON FHGFF3 case exists in any lane; the only FHGFF3 metadata inputs are YAML (next row) | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| YAML | tested both ways — input and output `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("sarscov2 - fhr yaml - json")`; the example publishes `ID.yaml` via the pinned convert `tests/run.py :: alpha/metadata/alpha.yaml` | tested — validate input `modules/nf-core/fairbioheaders/validate/tests/main.nf.test :: test("sarscov2 - fhp - yaml")`; convert output exercised by the harness format sweep `tests/integration.nf :: def formats = ['json', 'yaml', 'html', 'fasta', 'gfa']` | tested as input — standalone validate and combine both take the YAML sidecar `workflows/fairbioheaders/assets/test/samplesheet.csv :: gff3,annotation.fhgff3.yaml,no-header.gff3`, `modules/nf-core/fairbioheaders/validate/tests/main.nf.test :: test("candidatus_portiera_aleyrodidarum - fhgff3 - yaml")`; YAML **output** of an FHGFF3 header extraction is not tested | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| JSON-LD | partial — **input** (expanded form) is tested through the dockstore lane only (`workflows/fairbioheaders/assets/test/samplesheet.csv :: jsonld,minimal.fhr.expanded.jsonld,genome.fa`); **output** (`--to jsonld`) has no FHR case in any lane | tested — output `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("sarscov2 - faa - fhp - jsonld")`; JSON-LD **input** is not tested (the toolkit reads it from 0.8.2 on, but no case here feeds it) | not tested — no JSON-LD FHGFF3 case exists | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| HTML microdata | tested both ways — FHR metadata round-trips through HTML in the harness sweep `tests/integration.nf :: def formats = ['json', 'yaml', 'html', 'fasta', 'gfa']` | tested both ways — `tests/run.py :: FHP metadata did not round-trip through HTML`; plain-name publish `tests/run.py :: cvt-html` | not tested — no HTML FHGFF3 case exists | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |
| sequence containers (FASTA `.fa/.fasta/.faa`, GFA, GFF3) | tested — FASTA and GFA through attach/verify/strip; `--to fasta` and `--to gfa` header-only outputs `tests/integration.nf :: def formats = ['json', 'yaml', 'html', 'fasta', 'gfa']`; `--to gff3` is **not tested** by any lane | tested — `.faa` attach/verify/strip; header-only output lands on `.fasta` by contract `tests/run.py :: invalid choice: 'faa'` | tested — combine input `modules/nf-core/fairbioheaders/combine/tests/main.nf.test :: test("candidatus_portiera_aleyrodidarum - gff3 - fhgff3")` and verify `tests/run.py :: FHGFF3 was not verified`; `--to gff3` output not tested | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted |

## 4. Matrix C — compression and byte-preservation transport

| transport | coverage in this suite |
| --- | --- |
| plain files | tested — every lane; the harness additionally pins spaced/quoted staged file names `tests/run.py :: SPACED spaced.json` |
| gzip FASTA input (combine, convert) | tested — `modules/nf-core/fairbioheaders/combine/tests/main.nf.test :: test("sarscov2 - fasta.gz - fhr")`, `modules/nf-core/fairbioheaders/convert/tests/main.nf.test :: test("sarscov2 - fasta.gz - fhr - yaml")` |
| gzip `.faa` through the full `FHR_ATTACH` (combine → verify → extract) | tested — `tests/run.py :: ATTACHED predicted predicted.faa.gz`; the emitted attached file is BGZF and verifies `tests/run.py :: attached file is BGZF` |
| gzip GFF3 into `GFF3_VALIDATE` | tested — `tests/run.py :: canonical-gene-gzip.gff3.gz` |
| BGZF as a distinct input fixture | not tested — no `.bgz` fixture exists in `tests/fixtures/`; the BGZF row above covers toolkit-written output, not a supplied `.bgz` input |
| gzip into `FAIRBIOHEADERS_VERIFY` standalone, `FHR_STRIP` or `FHR_VERIFY_LINKS` | not tested — the only compressed verify case is the FHP attach row above (which covers verify inside the sub-workflow); strip and verify-links run only on plain files |
| gzip GFA or gzip GFF3 into combine/verify | not tested — no such case in any lane |

## 5. Matrix D — version axes (what is actually exercised, not what exists)

The suite pins deliberately; this table records the pins as the matrix's version axis.
Machine-checkable copy (the checker diffs these against `modules.json`, the module
`environment.yml`/`main.nf` container refs, `environment/requirements.in`,
`nextflow.config` and `ci.yml`):

```matrix-pins
toolkit = 0.9.0
toolkit_wheel_sha256 = 296d9b01eb9949a19a845a77fbbe0bd53ad17405c5a87913204c48b246cd0d28
converter_checkout_commit = c6d74540416548597ad6305c1ad3731fc92ed6a2
wave_build = 71029206d3ce1119
biocontainers_build = pyhdfd78af_0
gff3_validator = 0.1.0
suite_version = 0.3.0
nextflow_supported = 26.04.6
nextflow_nextflow_version_directive = >=26.04.6
nextflow_dual_leg = 26.10.4
nextflow_dist_sha256 = 182a63c74074e2dc7956ffa3c8cd59de952ed2c44394e21faf5e1736b945444c
nf_test = 0.9.5
upstream_pin(combine) = def10bc21ae4952973f9e07952fc899aa060dfc5
upstream_pin(validate) = def10bc21ae4952973f9e07952fc899aa060dfc5
upstream_pin(convert) = 32d7eadd1f53d15cc203e2a52c4b7b83fb7a1d50
upstream_pin(verify) = def10bc21ae4952973f9e07952fc899aa060dfc5
```

| axis | pinned / exercised value | evidence |
| --- | --- | --- |
| toolkit (fair-bioheaders) | **0.9.0** — the Wave image of all four pinned modules (`modules/nf-core/fairbioheaders/combine/main.nf :: community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119`), the BioContainers/Galaxy-depot pair of the repository modules (`modules/local/strip/main.nf :: quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0`), every `environment.yml`, the hash-locked wheel (`environment/requirements.in :: fair_bioheaders-0.9.0-py3-none-any.whl`) and the CI checkout of tag v0.9.0 | guard job greps all of these agree |
| gff3-validator | **0.1.0** (`environment/requirements.in :: gff3-validator==0.1.0`) | harness asserts the report's `tool.version` `tests/run.py :: unexpected genome report` |
| Nextflow baseline | **26.04.6** supported (`nextflow.config :: nextflowVersion = '>=26.04.6'`); **26.10.4** dual-tested as the snapshot-recording baseline | nf-test matrix `nxf_version: ['26.04.6', '26.10.4']` |
| nf-test | 0.9.5 on both legs | `.github/workflows/ci.yml :: version: 0.9.5` |
| contract releases exercised in tests | FHR v0.3.1 (FHR 1 legacy + deprecation warning `tests/run.py :: is read as FHR 1 (v0.3.1)`), FHR v0.4.0 / schemaVersion 2.0 (`workflows/fairbioheaders/assets/test/minimal.fhr.json :: https://w3id.org/fair-bioheaders/fhr/v0.4.0`), FHR v0.5.0 / schemaVersion 2.1 x- extensions (`tests/run.py :: /fair-bioheaders/fhr/v0.5.0`), FHP v0.4.0 / schemaVersion 1.0 (`tests/fixtures/fhp/chain/protein.fhp.faa :: https://w3id.org/fair-bioheaders/fhp/v0.4.0`), FHGFF3 v0.4.0 / schemaVersion 1.0 (`workflows/fairbioheaders/assets/test/annotation.fhgff3.yaml :: https://w3id.org/fair-bioheaders/fhgff3/v0.4.0`) | each cited case asserts accept or reject on that exact URL |
| FHT / FHGM | not tested — published contract exists; pinned 0.9.0 runtime is unpromoted — native model selection is outside the header registry; the named native handoff is separate. Historical FHGM workflow scope was recorded by [#35](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Nextflow/issues/35); FHT adoption by [#7](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Nextflow/issues/7); the generic modules are reused by the new native lane rather than duplicated per type `tests/family_integration.nf :: include { FHR_CREATE_JSON }` | — |

## 6. Explicit open items and tracked gaps

These are the holes the matrix exists to make visible. None of them is fixed by this
document; each names its owner.

1. **Deliberate runtime promotion.** The default pins remain0.9.0. Actual PyPI latest was independently read as0.12.0 on 2026-11-20 during this preparation; corrected 0.13.1 publication and native installed acceptance are separate. See [the handoff](FIVE-TYPE-HANDOFF.md); neither a new specification tag nor a candidate version string updates conda/container support.
2. **Upstream module bump (`def10bc2`): done 2026-11-18.** Upstream nf-core/modules commit
   `def10bc21a` ("fairbioheaders: quote prefix-derived output paths", nf-core/modules#13771,
   merged 2026-11-14T19:06:18Z) double-quotes the prefix-derived output paths of
   combine/convert/validate/verify and adds one convert test. All four pins moved through the
   recorded procedure in [docs/module-migration.md](module-migration.md), and the harness's
   spaced-`ext.prefix` case (`tests/run.py :: ext.prefix = { 'spaced prefix' }`) now asserts
   success instead of the old shell parse error.
3. **Historical red CI leg, repaired by the approved 2026-11-19 pin exception.** The `nf-test (Nextflow
   26.10.4)` job fails on `main` (`44b5b2c`) on two stdout-only assertions in the pinned
   upstream convert suite, because 26.10.4 writes the Nextflow log to stderr; the remedy
   is upstream (item 2's pin move did not touch those assertions). The 26.04.6 leg passed with all 30 tests before item 2 added a 31st.
   Full receipt: `docs/module-migration.md :: FAILURE: Executed 30 tests in 151.763s (2
   failed)`; the assertion inventory is in the same section
   (`docs/module-migration.md :: The two red assertions are not snapshot tests`). This
   historical matrix described the original failure. PR #38 now updates only the
   complete convert pin through David’s exact-source exception; the two
   stream-tolerant assertions and new unsafe-prefix test bring the inventory to 32.
   Full two-engine Docker-profile CI remains required before merge.
4. **Test-lane asymmetry.** The four pinned upstream modules carry nf-test; the
   repository-owned modules (`verify_links`, `gff3_validate`, `strip`, `create_json`,
   `converter_tests`, `utils`) carry **no nf-test** and are covered only by the
   harness/example lanes. Migration of the local layout to `modules/local/` with
   nf-test suites is #7 scope (maintainer decision 6A, 2026-11-14), paired with the next
   toolkit bump.
5. **Untested serialization/transport cells** (each named above so it cannot read as
   parity): FHGFF3 JSON (both directions), FHGFF3 and FHR JSON-LD output and FHP JSON-LD
   input, FHGFF3 HTML, FHGFF3 header extraction, `--to gff3`, `--to jsonld` for FHR,
   FHGFF3 standalone validation from a JSON file, `FHR_CREATE_JSON` with an FHGFF3 map,
   the `GFF3_VALIDATE` FHGFF3 header hook (`ext.header`), supplied-`.bgz` inputs,
   standalone verify/strip/verify-links on compressed files, gzip GFA/GFF3 into
   combine/verify, and FHR `derivedFrom` links.
6. **FHGFF3 workflow depth.** #35's own acceptance says it plainly: existing FHGFF3
   parent fixtures and GFF3 validation **do not establish complete FHGFF3 workflow
   coverage**; the lenient/strict header-hook option pair and a headed-GFF3 fixture are
   missing even though the combine/verify round trip works.
7. **Runtime lanes stay separate.** Published FHT/native-FHGM contracts do not upgrade the0.9.0 baseline. New native-host composition and the actual release handoff are recorded separately; conda/container/upstream-module promotion waits for verified artifacts and reviewed revisions.

## 7. Related documentation

- [README](../README.md) — user-facing module contracts.
- [Pipeline guide](PIPELINES.md) — composition, troubleshooting, execution.
- [Module migration](module-migration.md) — pinning procedure, upstream contract tables.
- [CHANGELOG](../CHANGELOG.md) — dated behavior and verification record.
