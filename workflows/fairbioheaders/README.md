# FAIR-bioHeaders Nextflow workflow

A minimal Nextflow DSL2 workflow around two of the
[nf-core-style modules](../../modules/nf-core/fairbioheaders) of this repository:

1. `FAIRBIOHEADERS_COMBINE` adds FAIR-bioHeaders metadata (FHR for FASTA and GFA, FHP for
   protein FASTA, FHGFF3 for GFF3) to each sequence file and calculates its checksum;
2. `FAIRBIOHEADERS_VERIFY` checks the headed file against the schema and the checksum.
   The run fails if a file does not verify.

It moved here from FAIR-bioHeaders-Tools (`nextflow/workflows/fairbioheaders`, FAIR-bioHeaders-Nextflow
#21) and is described for [Dockstore](https://dockstore.org) by
[`.dockstore.yml`](../../.dockstore.yml) at the repository root. Until this repository is
registered on Dockstore, the registered entry is the one in FAIR-bioHeaders-Tools.

For metadata creation, conversion, stripping, GFF3 validation and parent-link checks, see
the example pipeline [`main.nf`](../../main.nf) at the repository root and
[docs/PIPELINES.md](../../docs/PIPELINES.md).

## Input

Either a samplesheet, a CSV file with the columns `id,metadata,sequence`:

```csv
id,metadata,sequence
genome,genome.fhr.yaml,genome.fa.gz
graph,genome.fhr.json,graph.gfa
proteins,proteins.fhp.yaml,proteins.faa
annotation,annotation.fhgff3.yaml,annotation.gff3
```

```bash
nextflow run FAIR-bioHeaders/FAIR-bioHeaders-Nextflow \
    -main-script workflows/fairbioheaders/main.nf \
    -profile docker --input samplesheet.csv --outdir results
```

or one file:

```bash
nextflow run FAIR-bioHeaders/FAIR-bioHeaders-Nextflow \
    -main-script workflows/fairbioheaders/main.nf \
    -profile docker --metadata genome.fhr.yaml --sequence genome.fa.gz --outdir results
```

| Parameter | Description |
| --- | --- |
| `--input` | Samplesheet (CSV: `id,metadata,sequence`). Relative paths are relative to the samplesheet, which may be a URL. |
| `--metadata`, `--sequence` | Metadata (JSON, YAML, JSON-LD or HTML microdata) and one FASTA, protein FASTA, GFA or GFF3 file, plain or gzip/BGZF, in place of `--input`. |
| `--id` | Output name for `--sequence` (default: its file name without the extension). |
| `--outdir` | Output directory (default `results`). |

The file type comes from the sequence file's extension: `.gfa` is GFA, `.gff3` or `.gff`
is GFF3, anything else (including protein `.faa`) is FASTA (`.gz`/`.bgz` ignored). The
header type comes from the metadata's `schema` URL. In a clone of the repository, run
`nextflow run workflows/fairbioheaders/main.nf ...` in the same way.

## Output

- `<outdir>/combine/<id>.fhr.fa` or `<id>.fhr.gfa` for FHR, `<id>.fhp.faa` for FHP, or
  `<id>.fhgff3.gff3` for FHGFF3: the sequence file with its metadata header (`.gz` when
  the input was compressed);
- `<outdir>/verify/<id>.verify.txt`: the verification report.

## Profiles

| Profile | Runs `bioheaders` from |
| --- | --- |
| `docker` | the modules' BioContainers image, `quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0` |
| `singularity`, `apptainer` | the modules' Galaxy depot Singularity image of the same build |
| `conda` | [`environment.yml`](environment.yml): `bioconda::fair-bioheaders=0.8.2` |
| `test` | the samplesheet in [`assets/test`](assets/test): a FASTA, a GFA and a GFF3 example, the FASTA with expanded JSON-LD metadata, and the repository's FHP protein example |
| none | `bioheaders` on the `PATH` (`pip install "fair-bioheaders[jsonld]"`) |

Combine `test` with one of the others, for example `-profile test,docker`.
[`assets/test/params.json`](assets/test/params.json) is the same test as a parameter file
(`-params-file`), reading the samplesheet from GitHub; Dockstore lists it as the test
parameter file.

**Container and conda environment.** Both processes run the modules' container, the
BioContainers image of `fair-bioheaders` 0.8.2 (or the Galaxy depot's Singularity image of
it). The conda profile uses [`environment.yml`](environment.yml), which pins the same
Bioconda package as the modules; keep the two pins equal. From 0.8.2 the Bioconda package,
and so the image, includes `pyld`, the optional dependency (the `jsonld` extra) that
reading JSON-LD metadata in other than the canonical form needs, for example expanded
JSON-LD, so the workflow no longer replaces the modules' image with the project's GHCR
image.

The `dockstore-workflow` job of [CI](../../.github/workflows/ci.yml) checks that the
workflow sets no container and that its Bioconda pin equals the modules', then runs
`-profile test,docker`, including the expanded JSON-LD and FHP rows of the test
samplesheet.
