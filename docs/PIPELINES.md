# Building FHR pipelines

See [README](../README.md) for setup and complete module contracts. These modules preserve caller-supplied metadata and use the converter's schema; they do not infer biological provenance or query external services.

## Construct metadata, attach it, and validate

A record has two separate maps: `meta` carries the pipeline ID and any routing information; `fields` contains the FHR document. Pipeline IDs do not automatically become FHR identifiers. Load fields from JSON as in the example workflow or construct a map from upstream results. Supply every required field and any known optional fields.

The following composition consumes an existing `records` channel of `(meta, fields)` tuples and a single sequence file supplied as `params.sequence`:

```nextflow
include { FHR_CREATE_JSON } from '/path/to/FAIR-bioHeaders-Nextflow/modules/create_json/main'
include { FHR_ATTACH } from '/path/to/FAIR-bioHeaders-Nextflow/subworkflows/attach/main'

workflow {
    // Define records upstream: tuple([id: 'assembly1'], fields).
    FHR_CREATE_JSON(records)
    FHR_ATTACH(FHR_CREATE_JSON.out.json.map { meta, json ->
        tuple(meta, json, file(params.sequence, checkIfExists: true), 'fasta')
    })
    // FHR_ATTACH.out.sequence contains checksum-verified FASTA files (ID.fasta).
    // FHR_ATTACH.out.json contains JSON with each attached file's checksum (ID.json).
}
```

This is a composition fragment: define `records` in the consuming workflow before using it. Set `nextflow.enable.dsl = 2` in that project's config. For several assemblies, pair each validated JSON with its corresponding sequence by a stable sample ID rather than relying on channel arrival order. Use `gfa` instead of `fasta` for GFA files.

`FHR_ATTACH` composes the pinned upstream `FAIRBIOHEADERS_CONVERT` for its extraction step, which defaults its output to `<id>_converted.json`. To get the documented `ID.json`, the consuming project must set `ext.prefix`: `process { withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { meta.id } } }` (the upstream module's own mechanism; `FAIRBIOHEADERS_COMBINE` already defaults its prefix to `meta.id`). The attached file is named `<id>.<input extension>` (`genome.fasta` → `ID.fasta`, `protein.faa` → `ID.faa`, …); the sequence kind is carried on `meta`, not the file name.

Standalone JSON requires an explicit schema-valid checksum. Attachment replaces that value with the final file checksum; downstream consumers should use `FHR_ATTACH.out.json` when referring to the attached sequence. The algorithm is **SHA-512/256**, not a manually truncated SHA-512 digest. Encode its 32-byte digest using standard padded base64 (44 characters), without a prefix. It covers the exact file bytes except the scalar root checksum line and its terminator; preserve line endings, whitespace, comments and all other metadata. See the [specification checksum contract](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.3.0/docs/FORMAT.md#checksum-decision-for-v03). It is not a checksum of sequence letters alone. A supplied `seqcol_id` is preserved, not computed or verified against sequence content.

## Run converter tests as part of a pipeline

```nextflow
include { FHR_CONVERTER_TESTS } from '/path/to/FAIR-bioHeaders-Nextflow/modules/converter_tests/main'

workflow {
    FHR_CONVERTER_TESTS(Channel.value(tuple(
        [id: 'converter-tests'],
        file(params.converter_source, checkIfExists: true)
    )))
    // reports emits tuple(meta, junit_xml, test_log) whether or not tests pass.
    // passed emits meta only after every test passes.
}
```

Provide a toolkit source directory containing `pyproject.toml`, `tests/` and `pytest.ini` that declares the installed toolkit's version (0.9.0 in the supported baseline), preferably the matching release checkout; other versions are rejected. The workflow copies the checkout into its task directory (the input is never modified and no bytecode is written), runs its tests against the installed converter (tests that invoke the checkout's own scripts use the copy), and always emits JUnit XML plus a log so that they can be published. A separate check task then fails the run if pytest failed. An independent test branch does not gate other workflow outputs automatically: combine release or publication channels with `FHR_CONVERTER_TESTS.out.passed` if those steps must wait for passing tests, as the example `main.nf` does:

```nextflow
gate = FHR_CONVERTER_TESTS.out.passed.first()
gated = FHR_ATTACH.out.json.combine(gate).map { meta, json, _passed -> tuple(meta, json) }
```

## Validate GFF3 annotations

```nextflow
include { GFF3_VALIDATE } from '/path/to/FAIR-bioHeaders-Nextflow/modules/gff3_validate/main'

workflow {
    GFF3_VALIDATE(Channel.of(
        tuple([id: 'annotation1'], file(params.gff3, checkIfExists: true), []),
        tuple([id: 'annotation2'], file(params.gff3_with_genome, checkIfExists: true), file(params.genome, checkIfExists: true))
    ))
    // reports emits tuple(meta, json, html) whenever validation completes.
    // valid emits tuple(meta, gff3) only for files with no errors.
}
```

| Input | Meaning |
| --- | --- |
| `meta` | Map with a safe `id`; reports are named `ID.gff3-validate.json` and `ID.gff3-validate.html` |
| `gff3_path` | GFF3 file, plain, gzip or BGZF |
| genome | `[]` for none, or one FASTA (plain or gzip) for the BIO-* sequence checks |

| `task.ext` option | Default | Effect |
| --- | --- | --- |
| `header` | `auto` | `require` or `skip` the FAIR-bioHeaders GFF3 header checks |
| `translation_table` | validator default (1) | NCBI table for codon checks; needs a genome |
| `max_findings` | validator default (10000) | Cap on reported findings; counts stay complete |
| `fail_on_errors` | `true` | `false` emits reports for files with errors and continues, omitting them from `valid` |

The default stops the pipeline on a file with errors, because downstream steps should not consume an invalid annotation silently; the task error shows the first findings and the reports remain in the task work directory. Set `fail_on_errors = false` to survey a batch and decide later, then route only `GFF3_VALIDATE.out.valid` downstream. Warnings and notes (such as BIO-008, an in-frame stop codon) never fail. An unreadable GFF3 or genome, or an invalid option, makes the validation incomplete (exit status 2) and always fails. Configure options per process, or per record with a closure such as `ext.translation_table = { meta.translation_table }`:

```groovy
process {
    withName: GFF3_VALIDATE {
        ext.header = 'skip'
        ext.fail_on_errors = false
    }
}
```

The validator checks only the rules its catalogue marks as implemented; the JSON report lists the layers it skipped. Each file is validated twice (JSON, then HTML), so allow for twice the validator runtime on large files.

## Compose protein FASTA and verify parent links

Protein FASTA uses the same composition with `kind` `faa`. The FHP metadata map must cite an FHP `schema` URL and carry the required FHP fields; the toolkit's bundled FHP schema validates it, so no FHP rule is repeated here.

```nextflow
include { FHR_CREATE_JSON } from '/path/to/FAIR-bioHeaders-Nextflow/modules/create_json/main'
include { FHR_ATTACH } from '/path/to/FAIR-bioHeaders-Nextflow/subworkflows/attach/main'
include { FHR_VERIFY_LINKS } from '/path/to/FAIR-bioHeaders-Nextflow/modules/verify_links/main'

workflow {
    FHR_CREATE_JSON(records)  // records: tuple([id: 'proteome1'], fhp_fields)
    FHR_ATTACH(FHR_CREATE_JSON.out.json.map { meta, json ->
        tuple(meta, json, file(params.protein, checkIfExists: true), 'faa')
    })
    FHR_VERIFY_LINKS(FHR_ATTACH.out.sequence.map { meta, sequence ->
        tuple(meta, sequence, params.parents ? params.parents.collect { file(it) } : [])
    })
    // FHR_VERIFY_LINKS.out.report emits tuple(meta, report) when verification completes successfully.
    // FHR_VERIFY_LINKS.out.verified emits tuple(meta, sequence) only when every recorded parent was checked and matched.
}
```

| `FHR_VERIFY_LINKS` input | Meaning |
| --- | --- |
| `meta` | Map with a safe `id`; the report is named `ID.verify-links.txt` |
| `sequence_path` | A FASTA/FAA/GFA/GFF3 file whose header records `derivedFrom` (plain, gzip or BGZ) |
| parents | `[]` for none, or a list of candidate parent files |

| `task.ext` option | Default | Effect |
| --- | --- | --- |
| `require_all` | `false` | `true` also fails when a recorded parent could not be checked |
| `fail_on_mismatch` | `true` | `false` emits the report for a mismatch and continues, omitting the input from `verified` |

A match confirms **file identity only**, never biological translation or annotation correctness. Exit status 1 (unreadable or invalid input, or an invalid parent) always fails; exit status 3 is a mismatch (or, with `require_all`, an unchecked parent). An exit-0 run whose report contains `not checked` (an unavailable or unsupported candidate) emits the report but omits the input from `verified`; supply the recorded parents, or set `require_all = true` to fail instead. Only a run with every recorded parent checked and matched (or none recorded) emits `verified`. The FHP fixtures under `tests/fixtures/fhp/chain/` demonstrate an FHR genome FASTA, an FHGFF3 annotation GFF3 recording the genome, and an FHP protein FASTA recording the annotation; each link is verified by checksum. FHP JSON-LD and HTML microdata are not supported until FAIR-bioHeaders-Tools#58 is released.

## Execution and publication

Processes that run fair-bioheaders declare their BioContainers image (`quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0`, or the Galaxy depot Singularity image) and a conda `environment.yml`, so a consumer only enables Docker, Singularity, Apptainer or conda. `GFF3_VALIDATE` (gff3-validator is not on Bioconda yet) and `FHR_RUN_CONVERTER_TESTS` (needs pytest) have the label `fhr` instead. Configuration from this repository does not accompany imports into another project. With the supplied image built locally, a consumer can configure:

```groovy
nextflow.enable.dsl = 2
docker.enabled = true
process {
    withLabel: fhr {
        container = 'fhr-nextflow:0.1.0'
        cpus = 1
        memory = '1 GB'
        time = '30m'
    }
}
```

The native JSON writer executes in Nextflow's JVM. Command wrappers use the consumer's executor. Remote executors need access to the converter environment or an available container image; a locally built Docker tag is not automatically accessible on a cluster.

Modules leave files in their task work directories. The example workflow publishes with Nextflow workflow outputs (`publish:` and `output {}`), copying results into `params.outdir` per sample ID, and withholds them until converter tests pass when `--converter_source` is given; production consumers should define their own publication rules and retain logs and version reports appropriate to their provenance needs. Use unique sample IDs and keep Nextflow work directories while downstream tasks still require them. The supplied Docker profile runs containers as the invoking user, so work files are not root-owned.

## nf-core-style modules

`modules/nf-core/fairbioheaders/` holds the FAIR-bioHeaders modules in nf-core/modules layout (`main.nf`, `meta.yml` with EDAM formats, `environment.yml`, `tests/main.nf.test` and snapshots). `combine`, `validate` and `convert` are **pinned copies of the upstream nf-core/modules revisions** recorded in `modules.json` (combine `8faff340`, validate `86e852e`, convert `4dc3bc54`); never patch them locally — repository behavior belongs in repository-owned modules. `verify` remains the repository's own module, pending its upstream review (nf-core/modules#13635). The full comparison and the update procedure live in [docs/module-migration.md](module-migration.md).

| Module | Input | Output |
| --- | --- | --- |
| `FAIRBIOHEADERS_COMBINE` (upstream, pinned; used by `FHR_ATTACH`, the example and the Dockstore workflow) | `(meta, metadata, sequence)` | `sequence`: the headed file, **named after the input's extension**: `ID.<ext>` (`ID.fasta`, `ID.fa`, `ID.faa`, `ID.gfa`, `ID.gff3`), with `.gz` when the input was compressed; the header family lives in the file, not the name. Fails when the output name would overwrite a staged input — set `ext.prefix` or use a non-colliding id |
| `FAIRBIOHEADERS_CONVERT` (upstream, pinned; the suite's convert) | **two rows**: `(meta, input)` and `format` | `metadata`: `ID.<format>` when the project sets `ext.prefix = { meta.id }` (otherwise the default `ID_converted.<format>`). Reads a standalone metadata file or extracts the header of a combined FASTA/GFA/GFF3; `<format>` is a toolkit `--to` token and also the output extension (`json`, `yaml`, `jsonld`, `html`, `fasta`, `gfa`, `gff3`; **no `faa`** — a header-only protein becomes `.fasta`). Fails when the output name would equal the input — set `ext.prefix` |
| `FAIRBIOHEADERS_VERIFY` (repository module, pending upstream) | `(meta, sequence)` | `report`: `PREFIX.verify.txt`; the task fails when the header is invalid or the checksum does not match |
| `FAIRBIOHEADERS_VALIDATE` (upstream, pinned) | `(meta, metadata)` | `report`: `PREFIX.validate.txt`; the task fails when standalone JSON/YAML/JSON-LD metadata does not validate |

`PREFIX` is `task.ext.prefix` or `meta.id`; `task.ext.args` is passed to `bioheaders`.
Issue #29 option (a) (2026-11-13) retired the repository's header-family compatibility
modules `FHR_COMBINE` (`modules/combine`) and `FHR_CONVERT` (`modules/convert`): every
caller now composes the pinned upstream `FAIRBIOHEADERS_COMBINE`/`FAIRBIOHEADERS_CONVERT`
directly and publishes their input-faithful names, so **no output file name carries an
`fhr`/`fhp`/`fhgff3` marker any more**. Two consequences for direct importers: (1) the
upstream modules do not shell-quote `ext.prefix`/`meta.id`, so **you must constrain
`meta.id` to safe filenames yourself** (`FHR_ATTACH`/the example already do via
`isSampleId`); (2) `bioheaders combine`/`convert` refuse to overwrite a staged input
(`FHR: Output must differ from the input files` / `Input and output names are the same,
set prefix...`), so pick ids where `<id>.<extension>` cannot equal the sequence file's
own name, or set `ext.prefix`. The upstream COMBINE leaves format inference to the
toolkit and keeps the input extension; `FHR_STRIP`/`FHR_VERIFY_LINKS` (repository
modules) still read the kind from a supplied **input** file's extension via
`sequenceKindOf`. Versions go to the `versions` topic. Run their tests with
`nf-test test --profile docker` from the repository root (`nf-test.config`,
`tests/config/nf-test.config`).

```nextflow
include { FAIRBIOHEADERS_COMBINE } from '/path/to/FAIR-bioHeaders-Nextflow/modules/nf-core/fairbioheaders/combine/main'
include { FAIRBIOHEADERS_VERIFY } from '/path/to/FAIR-bioHeaders-Nextflow/modules/nf-core/fairbioheaders/verify/main'

workflow {
    FAIRBIOHEADERS_COMBINE(channel.of(tuple([id: 'proteins'], file(params.metadata), file(params.protein))))
    FAIRBIOHEADERS_VERIFY(FAIRBIOHEADERS_COMBINE.out.sequence)  // proteins.headed.faa with the config below
}
```

The combine output is `proteins.faa` (prefix `meta.id`, extension from the input). If a
sequence file could be named exactly `<id>.<extension>` — e.g. an input `proteins.faa` with
id `proteins` — the toolkit refuses to overwrite it; set the documented `ext.prefix`
disambiguator:

```nextflow
process {
    withName: FAIRBIOHEADERS_COMBINE {
        ext.prefix = { "${meta.id}.headed" }
    }
}
```

The example's headed output is then `proteins.headed.faa`; keep the chosen prefix
distinct from every staged input basename and constrain IDs to safe filenames. There is
**no header-family option any more**: the retired `modules/combine` (`FHR_COMBINE`) used to
emit `proteins.fhp.faa`; the family now lives in the file header and on `meta`, and
`FHR_ATTACH` composes the upstream module directly.

The pinned CONVERT is called with **two rows** — the file channel and a channel of
format values — and names its output after the format it is given (`ID_converted.<format>`
by default). The suite publishes the plain id by setting `ext.prefix = { meta.id }`:

```nextflow
include { FAIRBIOHEADERS_CONVERT } from '/path/to/FAIR-bioHeaders-Nextflow/modules/nf-core/fairbioheaders/convert/main'

workflow {
    def headed = Channel.of(tuple([id: 'proteins'], file(params.protein)))
    FAIRBIOHEADERS_CONVERT(headed, Channel.value('json'))
    // Without config: proteins_converted.json (the header of params.protein as JSON).
    // Add
    //   process { withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { meta.id } } }
    // to get proteins.json — the name FHR_ATTACH and the example publish (issue #29 (a)).
}
```

`faa` is not one of its formats: the toolkit's `--to` accepts
`json yaml jsonld html fasta gfa gff3`, and the module uses that token as the output
extension, so a header-only protein file becomes `proteins.fasta`. The retired
`modules/convert` (`FHR_CONVERT`) used to offer `.faa` and a pre-launch format whitelist;
callers that need those can wrap the upstream module and rename from their own contract,
but this suite no longer ships them.

The minimal Dockstore workflow [workflows/fairbioheaders](../workflows/fairbioheaders/README.md) runs COMBINE then VERIFY over a samplesheet.

## Diagnosing failures

- **Invalid metadata:** inspect the validator error and compare the map with the pinned specification. JSON serialization succeeds independently of schema validation; only validated JSON is emitted by `FHR_CREATE_JSON`.
- **Toolkit version:** the modules no longer stop on a version mismatch; each task reports the version it ran on the `versions` topic. Use the modules' BioContainers images (or the pinned environment) for the supported baseline, and upgrade the compatibility contract and tests together before claiming another version.
- **Checksum mismatch:** verify that no program changed the header, whitespace, line endings or sequence bytes after attachment. Reattach when changing metadata.
- **Unsafe ID or unsupported format:** use IDs and format values from the README contract. The repository modules quote staged paths and explicitly restrict command formats; the pinned upstream modules rely on Nextflow's interpolation of staged paths, so supply only ID-constrained names and controlled `ext.prefix` values to them.
- **GFF3 validation failed:** read the findings in the task error or the JSON/HTML report in the task work directory; with `fail_on_errors = false` the reports are emitted instead. An "incomplete" failure means the GFF3 or genome could not be read.
- **Failed converter tests:** inspect the published `converter-tests/converter-tests.log` and JUnit XML. A checkout whose declared version differs from the installed toolkit is rejected before tests run.
- **Parent-link verification failed:** read the report (and the task error) for the `derivedFrom` entry that did not match; supply the parent file the header records, recombine the parent if it changed, or set `ext.fail_on_mismatch = false` to survey a batch. An "incomplete" failure means the input or a parent could not be read or validated. A match proves file identity, not translation correctness.
- **JSON serialization errors:** the message names the field location, for example `$.dateCreated`; convert dates to ISO 8601 strings and remove NaN, Infinity and `null` list items.

See [SECURITY.md](../SECURITY.md) for sensitive findings and [CONTRIBUTING.md](../CONTRIBUTING.md) for changes to modules or their contracts.
