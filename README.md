**This is a demo repository**, do not deploy. 

# FHR-Nextflow

Reusable Nextflow DSL2 modules for creating, converting, validating and attaching [FAIR bioHeaders](https://doi.org/10.1093/bib/bbae122), plus GFF3 validation, the nf-core-style `FAIRBIOHEADERS_COMBINE`, `FAIRBIOHEADERS_VERIFY` and `FAIRBIOHEADERS_VALIDATE` modules and a minimal Dockstore workflow ([workflows/fairbioheaders](workflows/fairbioheaders/README.md)), which moved here from FAIR-bioHeaders-Tools (#21). This development prototype implements [FAIR-bioHeaders-Specification issue #15](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/15). The dedicated repository is [FHR-Nextflow](https://github.com/FAIR-bioHeaders/FHR-Nextflow); it has no published release.

Compatibility: Nextflow **26.04.6**, Java **21**, [FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools) **0.8.2**, [gff3-validator](https://github.com/FAIR-bioHeaders/gff3-validator) **0.1.0**, FHR schemaVersion **1** (cited through the `fhr/v0.3.1` release URL) and FHP schemaVersion **1.0** (the `fhp/v0.4.0` release URL). The suite version is **0.1.0-dev**. JSON creation and channel composition are native DSL2/Groovy; the toolkit owns schema selection and validation, format conversion, exact-byte checksums and parent-link verification.

Toolkit version, validator version, the per-type schema contract and the suite version are separate. The toolkit selects a schema from the record's `schema` URL (FHR-Specification `docs/SCHEMA-VERSIONS.md`): a raw-main URL selects the bundled current schema, and a release's raw tag or `https://w3id.org/fair-bioheaders/<type>/vX.Y.Z` URL selects that release. Since toolkit **0.7.0** the raw-main FHR URL selects FHR schemaVersion **2.0**, so the bundled FHR example cites `https://w3id.org/fair-bioheaders/fhr/v0.3.1` to stay on schemaVersion 1; cite a v0.4.0 URL and `"2.0"` to move it. An unsupported release URL is rejected, never checked against another schema.

## Run the example

Install Nextflow and Java using the [official instructions](https://docs.seqera.io/nextflow/install). Then install the converter environment in an isolated Python 3.13 environment:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r environment/requirements.txt
nextflow run main.nf --metadata examples/metadata.json \
  --sequence examples/genome.fasta --sequence_format fasta
```

Alternatively, build the supplied container and enable Docker:

```sh
docker build -t fhr-nextflow:0.1.0 environment
nextflow run main.nf -profile docker \
  --sequence examples/assembly.gfa --sequence_format gfa
```

Outputs are copied to `--outdir` (default `results`) under one directory per ID. Without `--sequence`, the validated standalone JSON and YAML appear in `results/ID/metadata/`. With `--sequence`, only the attached sequence and JSON/YAML extracted from it appear in `results/ID/sequence/`: their checksum is computed from the attached file, so the caller-supplied standalone checksum is not published.

`--metadata` accepts one JSON file or a quoted glob. Each file's ID is its name without `.fhr.json` or `.json` (the bundled example uses `example`); duplicate or unsafe IDs stop the run before anything is published. `--id SAMPLE` overrides the ID for a single file and is rejected when several files match.

Add `--converter_source ../FAIR-bioHeaders-Tools` (a v0.8.2 checkout, matching the installed toolkit) to run the toolkit's pytest suite. Its JUnit XML and log are always published under `results/converter-tests/`. The metadata and sequence results of that run are **published only after every converter test passes**; if a test fails, the run exits non-zero and publishes only the test reports.

Add `--gff3 FILE` (one GFF3 file or a quoted glob; plain, gzip or BGZF) to validate GFF3 annotations with gff3-validate. Each file's ID is its name without `.gff3`/`.gff` and `.gz`; JSON and HTML reports appear in `results/ID/gff3/`. `--gff3_genome genome.fa` enables the sequence (BIO-*) checks for every file, so use it only when all files annotate that genome. `--gff3_header auto|require|skip`, `--gff3_translation_table N` (needs a genome) and `--gff3_max_findings N` are passed to the validator. A file with errors **fails the run** and nothing is published for it; `--gff3_fail_on_errors false` publishes its reports and continues. Unreadable or incomplete input always fails. The reports follow the same converter-test publication gate as other results. For example:

```sh
nextflow run main.nf --gff3 'tests/fixtures/gff3/*.gff3' \
  --gff3_genome tests/fixtures/gff3/genome.fa --gff3_fail_on_errors false
```

Protein FASTA (`.faa`) uses the same composition with `--sequence_format faa`; the FHP metadata is validated against the toolkit's bundled FHP schema, and the attached file is named by its header type, `ID.fhp.faa`:

```sh
nextflow run main.nf --metadata examples/protein-metadata.json \
  --sequence examples/protein.faa --sequence_format faa
```

Parent links recorded in an FHP `derivedFrom` are checked with `--verify_links FILE` (a sequence file or quoted glob) against `--verify_parents PARENTS` (a quoted glob; optional). Reports appear in `results/ID/verify-links/`; a recorded parent that does not match fails the run, and the reports follow the converter-test publication gate. For example:

```sh
nextflow run main.nf --verify_links tests/fixtures/fhp/chain/protein.fhp.faa \
  --verify_parents tests/fixtures/fhp/chain/annotation.fhgff3.gff3
```

See [Protein FASTA and parent links](#protein-fasta-and-parent-links-fhp) for the module contract.

**Example metadata is synthetic.** Its standalone checksum is an explicit placeholder and it has no SeqCol digest. Replace all provenance and identifiers with your own inputs. Attaching a sequence replaces the checksum with its actual FHR checksum; it does not calculate or verify SeqCol identity.

## Create JSON inside your pipeline

Import the module using its path in your local checkout:

```nextflow
include { FHR_CREATE_JSON } from '/path/to/FHR-Nextflow/modules/create_json/main'

workflow {
    records = Channel.of(tuple([id: 'assembly1'], [
        schema: 'https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/v0.3.0/fhr.json',
        schemaVersion: 1,
        genome: 'My assembly',
        taxon: [name: 'Homo sapiens', uri: 'https://identifiers.org/taxonomy:9606'],
        version: '1.0',
        metadataAuthor: [[name: 'Metadata author']],
        assemblyAuthor: [[name: 'Assembly author']],
        dateCreated: '2026-10-07',
        masking: 'not-masked',
        checksum: params.checksum
    ]))
    FHR_CREATE_JSON(records)
    // FHR_CREATE_JSON.out.json: tuple(meta, validated_json_path)
}
```

The input map accepts **all FHR schema fields**, including nested maps/lists, rather than a restricted set of CLI flags. Required fields are `schema`, `schemaVersion`, `genome`, `taxon`, `version`, `metadataAuthor`, `assemblyAuthor`, `dateCreated`, `masking`, and `checksum`. Optional fields include `genomeSynonym`, `voucherSpecimen`, `accessionID`, `instrument`, `scholarlyArticle`, `documentation`, `identifier`, `relatedLink`, `funding`, `reuseConditions`, `vitalStats`, `assemblySoftware`, `assemblyProtocol`, and `seqcol_id`. See [examples/metadata.json](examples/metadata.json) for a full map and the [specification](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/tree/v0.3.1) for field constraints.

No field values are inferred or silently supplied. Provide a valid checksum for standalone metadata. For sequence construction, provide the metadata checksum explicitly, then use `FHR_ATTACH` to compute the attached file's final checksum and extract JSON matching that file. No sequence statistics or SeqCol digest are inferred. The converter rejects fields outside the schema. The same workflow creates FHP metadata when the map cites an FHP `schema` URL and carries the FHP fields; see [Protein FASTA and parent links](#protein-fasta-and-parent-links-fhp).

## Module contracts

Every input/output preserves `meta`, a map containing an `id`. IDs must start with a letter/digit and contain only letters, digits, dots, underscores or hyphens. Use unique IDs within a pipeline: output file names derive from the ID. File outputs remain in Nextflow task work directories; consumers control publication.

| Component | Input tuple | Named outputs |
| --- | --- | --- |
| `FHR_CREATE_JSON` workflow | `(meta, fields_map)` | `json`: `(meta, json)` after validation; `reports`: `(meta, ID.validate.txt)`; `versions` |
| `FHR_CONVERT` process | `(meta, metadata_path, output_format)` | `converted`: `(meta, output)`; `versions_fairbioheaders` |
| `FAIRBIOHEADERS_VALIDATE` process (nf-core style) | `(meta, metadata_path)` | `report`: `(meta, ID.validate.txt)`, emitted only when the standalone JSON/YAML metadata validates; `versions_fairbioheaders` |
| `FAIRBIOHEADERS_COMBINE` process (nf-core style) | `(meta, metadata_path, sequence_path)` | `sequence`: `(meta, ID.fhr.fa \| ID.fhr.gfa \| ID.fhp.faa \| ID.fhgff3.gff3)`, `.gz` when the input was compressed; `versions_fairbioheaders` |
| `FAIRBIOHEADERS_VERIFY` process (nf-core style) | `(meta, sequence_path)` | `report`: `(meta, ID.verify.txt)`, emitted only when the header validates and its checksum matches; `versions_fairbioheaders` |
| `FHR_STRIP` process | `(meta, sequence_path, kind)` | `stripped`: `(meta, sequence_without_header)`; `versions_fairbioheaders` |
| `FHR_CONVERTER_TESTS` workflow | `(meta, converter_source_directory)` | `reports`: `(meta, junit_xml, log)`, emitted whether or not tests pass; `passed`: `meta` after all tests pass; `versions` |
| `FHR_ATTACH` workflow | `(meta, metadata_path, sequence_path, kind)` | `sequence`: verified attached sequence; `json`: matching extracted metadata; `reports`: verification reports; mixed `versions` |
| `FHR_VERIFY_LINKS` process | `(meta, sequence_path, parent_paths_or_[])` | `report`: `(meta, verify-links.txt)`, emitted when verification completes successfully; `verified`: `(meta, sequence_path)` only when every recorded parent was checked and matched (or none was recorded); `versions_fairbioheaders` |
| `GFF3_VALIDATE` process | `(meta, gff3_path, genome_fasta_or_[])` | `reports`: `(meta, json, html)`, emitted whenever validation completes; `valid`: `(meta, gff3_path)` only when the file has no errors; `versions_gff3validator` |

The nf-core-style modules live in `modules/nf-core/fairbioheaders/{combine,verify,validate}` with `meta.yml`, `environment.yml` and nf-test tests; see [docs/PIPELINES.md](docs/PIPELINES.md#nf-core-style-modules). They replace the former `FHR_COMBINE` and `FHR_VALIDATE` processes: use `FAIRBIOHEADERS_VALIDATE` for standalone metadata and `FAIRBIOHEADERS_VERIFY` for headed sequence files.

`output_format`: `json`, `yaml`, `html`, `fasta`, `faa`, `gfa`. Input format is inferred by the toolkit from extension (`.faa` is protein FASTA); YAML `.yml` is also accepted. Converting metadata to FASTA/FAA/GFA produces **only a header**, not sequence content. Use `FAIRBIOHEADERS_COMBINE` or preferably `FHR_ATTACH` to construct a complete file.

`kind` (`FHR_STRIP`, `FHR_ATTACH`): `fasta`, `faa` or `gfa`. `faa` is protein FASTA: it selects the same `fhr-fasta-*` command as `fasta` (the toolkit keys sequence commands by type) but keeps the `.faa` extension in `FHR_STRIP`'s output name. `FAIRBIOHEADERS_COMBINE` takes the sequence type from the file extension (`.faa` is FASTA) and the header type from the metadata's `schema` URL, so `FHR_ATTACH` checks that `kind` agrees with the extension (`fasta` and `faa` are both FASTA). Metadata schema validation cannot establish that a supplied checksum matches any sequence. Validation failures stop the task and gate downstream validated outputs. `FHR_CONVERTER_TESTS` emits its reports even when tests fail, then fails the run; gate dependent steps on its `passed` output.

`GFF3_VALIDATE` runs gff3-validate 0.1.0 on a plain, gzip or BGZF GFF3 file. Pass `[]` as the genome when there is none; a FASTA (plain or gzip) adds the BIO-* sequence checks. Options come from `task.ext`, configured with `withName: GFF3_VALIDATE`: `header` (`auto` default, `require` or `skip` for the FAIR-bioHeaders GFF3 header), `translation_table` (an NCBI table; needs a genome), `max_findings` (report cap; counts stay complete) and `fail_on_errors` (default `true`). With `fail_on_errors = true`, a file with errors fails the task and its reports stay in the work directory, with the first findings in the task error; with `false`, the task succeeds, emits the reports and omits the file from `valid`. Warnings and notes never fail. Validator exit status 2 (unreadable GFF3 or genome, incomplete validation) always fails the task.

Each command task reports the version it ran on the nf-core `versions` topic, as `(task.process, 'fair-bioheaders', bioheaders --version)` (or `gff3-validator`, `gff3-validate --version`), and on a named `versions_<tool>` output; there is no exact-version gate. Collect them with `channel.topic('versions')`. Containers: the fair-bioheaders processes use the BioContainers image `quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0` (Galaxy depot image for Singularity/Apptainer) and their `environment.yml` with the conda profile; `GFF3_VALIDATE` (gff3-validator is not on Bioconda yet, [bioconda-recipes#70098](https://github.com/bioconda/bioconda-recipes/pull/70098)) and `FHR_RUN_CONVERTER_TESTS` (needs pytest) use `label 'fhr'`, which this project's config maps to the image built from `environment/`. The consuming pipeline must enable DSL2 (`nextflow.enable.dsl = 2` in its config). Importing modules does not inherit this project's config: an external project installs the pinned environment (`pip install --require-hashes -r environment/requirements.txt`, or `pip install fair-bioheaders` for the `bioheaders`/`fhr-*` commands), or enables a container engine and configures the consuming pipeline's `withLabel: fhr` container for the two processes above. No network access is required for validation after installation. The JSON serialization task uses native `exec` and runs in Nextflow's JVM. It writes UTF-8 without `\u` escapes and omits map entries whose value is `null`. Values with no unambiguous JSON form (for example `Date`/`LocalDate`, NaN, Infinity, `null` list items or non-string keys) are rejected with the field location; supply dates as ISO 8601 strings. Sets are written as arrays. Converter tasks use the configured executor and request defaults from the consumer.

## Protein FASTA and parent links (FHP)

FHP metadata for protein FASTA is validated, converted, attached, verified and stripped by the same `FHR_CREATE_JSON`/`FHR_CONVERT`/`FAIRBIOHEADERS_VALIDATE`/`FAIRBIOHEADERS_COMBINE`/`FAIRBIOHEADERS_VERIFY`/`FHR_STRIP`/`FHR_ATTACH` composition, using `kind`/`output_format` `faa`; the attached file is `ID.fhp.faa`. The required FHP fields are `schema`, `schemaVersion`, `proteome`, `sourceType`, `taxon`, `version`, `metadataAuthor`, `dateCreated` and `checksum`; `sourceType` is `predicted`, `database` or `mixed`; optional fields include `source`, `predictionSoftware`, `predictionProtocol`, `isoformPolicy`, `geneticCode`, `completeness`, `sequenceStats`, `accessionID`, `identifier` and `derivedFrom`. The toolkit's bundled FHP schema is the source of truth; the suite does not restate its rules. Fixtures cover predicted, database and mixed sets, plain and gzip `.faa`, malformed headers and parent links under [tests/fixtures/fhp](tests/fixtures/fhp/README.md).

`FHR_VERIFY_LINKS` wraps the toolkit's `bioheaders verify-links` command. It checks each `derivedFrom` entry against the candidate parent files by their FAIR-bioHeaders checksum, and any `genomeReference` against the supplied genomes. A match proves **file identity only**, never that a translation or annotation is biologically correct. It emits `report` when the task succeeds; on a hard failure the report stays in the task work directory and is not published. `verified` is emitted only when every recorded parent was checked and matched (or no parents were recorded): a successful run with an unavailable or unsupported parent reports `not checked` and omits the input from `verified`, so downstream steps cannot mistake an unchecked file for a verified one. Pass `[]` as `parents` when none are available. Exit status 1 (unreadable or invalid input, or an invalid parent) always fails. Exit status 3 (a recorded parent did not match, or with `ext.require_all` could not be checked) fails unless `ext.fail_on_mismatch` is `false`, which emits the report and omits the input from `verified`. Options come from `task.ext`, configured with `withName: FHR_VERIFY_LINKS`: `require_all` (default `false`) and `fail_on_mismatch` (default `true`).

```nextflow
include { FHR_VERIFY_LINKS } from '/path/to/FHR-Nextflow/modules/verify_links/main'

workflow {
    FHR_VERIFY_LINKS(Channel.of(
        tuple([id: 'protein'], file(params.protein), [file(params.genome), file(params.annotation)])
    ))
    // report emits tuple(meta, verify_links_report) whenever verification completes.
    // verified emits tuple(meta, sequence) only when the recorded parents matched.
}
```

The test chain uses actual supported parent formats: an FHR genome FASTA, an FHGFF3 annotation GFF3 whose `derivedFrom` records the genome, and an FHP protein FASTA whose `derivedFrom` records the annotation. `bioheaders verify-links` proves each recorded link by checksum; it does not translate the sequences. FHGFF3 parents are produced by the pinned toolkit's GFF3 commands in the fixtures; this suite's own modules compose protein FASTA.

**Toolkit provenance and scope.** The toolkit version is pinned in the modules' Bioconda/BioContainers references and in `environment/requirements.in` (regenerated `environment/requirements.txt`), reported on the `versions` topic and recorded in the CHANGELOG; each record carries its own schema release in its `schema` URL and `schemaVersion`. FHP release URLs are coordinated in [FAIR-bioHeaders-Specification#107](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/107); the FHP release is tracked in [FHP-Specification#1](https://github.com/FAIR-bioHeaders/FHP-Specification/issues/1). From toolkit 0.8.2, FHP metadata also converts to and from JSON-LD and HTML microdata ([FAIR-bioHeaders-Tools#98](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/pull/98), closing #58); `FHR_CONVERT` offers HTML, and the harness checks an FHP HTML round trip. FHT-File-Converter stays retired. This repository composes the toolkit's family workflows and now also holds the nf-core-style `combine`/`verify` modules first written in the toolkit ([FAIR-bioHeaders-Tools#49](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/49)), with their history; they are not by themselves the full family workflow suite.

Compatibility and versioning rules are documented in [the release policy](CONTRIBUTING.md#compatibility-and-release-policy).

## Verify

```sh
python tests/run.py --converter-source ../FAIR-bioHeaders-Tools
nf-test test --profile docker                       # modules/nf-core/fairbioheaders
nextflow run workflows/fairbioheaders/main.nf -profile test,docker --outdir results-dockstore
```

The stdlib Python harness runs native DSL2 integration tests from an external project: five metadata format round trips; FASTA/GFA attach, checksum validation and exact-byte stripping; Unicode and shell metacharacters; JSON serialization edge cases; per-file IDs for several metadata files and duplicate-ID rejection; publication without placeholder checksums; invalid fields, malformed JSON, unsafe IDs, unsupported formats and tampered file checksums; GFF3 validation of valid, gzip, invalid and genome-checked (BIO-008) files from the [gff3-validator conformance suite](tests/fixtures/gff3/README.md), with `fail_on_errors` on and off, an unreadable genome and duplicate GFF3 IDs. It also exercises protein FASTA end to end: predicted/database/mixed FHP metadata through create/convert/attach/strip, plain and gzip `.faa`, malformed FHP headers, invalid FHP metadata (missing fields, bad `sourceType`, unsupported schema URL) and `FHR_VERIFY_LINKS` for matching, unavailable and mismatching parents, `require_all`, `fail_on_mismatch` and the FHR genome → FHGFF3 annotation → FHP protein chain. With a converter checkout it also runs the toolkit's pytest suite and checks that failing tests (including after `-resume`) and mismatched checkout versions withhold results while publishing reports. The checkout must declare the installed toolkit's version (**0.8.2** in the supported baseline); it is copied into the task directory, so it is never modified, and its library tests import the installed distribution (tests that run the checkout's own scripts use the copied checkout, which the version check ties to the installed version). [CI](.github/workflows/ci.yml) runs the harness, the Docker examples, nf-test for the nf-core-style modules and the Dockstore workflow's test profile.

`environment/requirements.txt` is the single, hash-locked source of Python dependencies for the container, CI and local environments; edit `environment/requirements.in` and regenerate it with the command at its top. The container also pins its Python base image digest. Preserve the resulting image digest when sharing a reproducible pipeline. No network access is required for FHR validation after installation.

## Reference

Wright, Adam, Mark D. Wilkinson, Christopher Mungall, Scott Cain, Stephen Richards, Paul Sternberg, Ellen Provin, et al. 2024. “FAIR Header Reference Genome: A TRUSTworthy Standard.” *Briefings in Bioinformatics* 25 (3): bbae122. https://doi.org/10.1093/bib/bbae122.

## Project documentation

- [Pipeline guide](docs/PIPELINES.md): module composition, test integration, execution and troubleshooting.
- [Contributing](CONTRIBUTING.md): development checks, metadata coordination and release preparation.
- [Code of conduct](CODE_OF_CONDUCT.md) and [security policy](SECURITY.md): private reporting and independent conflict/appeal routing.
- [Agent instructions](AGENTS.md): repository layout and implementation strategy inferred from the FHR paper.
- [Citation metadata](CITATION.cff), [license notice](LICENSE) and [changelog](CHANGELOG.md).

This repository is licensed under the [Mozilla Public License 2.0](LICENSE) (`MPL-2.0`). External dependencies retain their own licenses. The suite has no published DOI; the paper citation describes the FHR standard. Schema governance rests with the maintainers, David and Adam ([GOVERNANCE](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/GOVERNANCE.md)).

## Licensing

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

This repository uses [MPL-2.0](LICENSE). It does not use the companion repositories’ historical USDA public-domain notice. External dependencies retain their own licenses. If a release is published, its release notes should state the applicable terms.
