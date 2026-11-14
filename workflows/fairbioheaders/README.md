# FAIR-bioHeaders Nextflow workflow

A minimal Nextflow DSL2 workflow around two modules of this repository:

1. `FAIRBIOHEADERS_COMBINE` (the pinned upstream nf-core module
   `modules/nf-core/fairbioheaders/combine`; issue #29 option (a) moved this workflow off
   the repository's retired header-family compatibility module onto it directly — it names
   each output after the **input's extension**, keeping the family only in the file header,
   see [docs/module-migration.md](../../docs/module-migration.md)) adds FAIR-bioHeaders
   metadata (FHR for FASTA and GFA, FHP for protein FASTA, FHGFF3 for GFF3) to each
   sequence file and calculates its checksum;
2. `FAIRBIOHEADERS_VERIFY` (the pinned upstream nf-core module
   `modules/nf-core/fairbioheaders/verify`; issue #29 slice 4 retired the repository's own
   implementation under the same path — same tuple shapes and report names, but the toolkit
   now infers the file type and the module runs the Wave image, see
   [docs/module-migration.md](../../docs/module-migration.md)) checks the
   headed file against the schema and the checksum. The run fails if a file does not verify.

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
genome-a,genome.fhr.yaml,genome.fa.gz
graph-b,genome.fhr.json,graph.gfa
proteome-c,proteins.fhp.yaml,proteins.faa
annotation-d,annotation.fhgff3.yaml,annotation.gff3
```

Relative paths resolve against the samplesheet directory. Because the combine output is
`<id>.<input extension>`, choose an `id` whose `<id>.<extension>` is not the sequence file's
own name (the four ids above — `genome-a`, `graph-b`, `proteome-c`, `annotation-d` — keep the
output distinct from the input); when they would collide the workflow falls back to
`<id>.combined.<extension>` so the run still completes.

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
| `--id` | Output name for `--sequence` (default: its file name without the extension; if that would make the combine output equal the input, `.combined` is appended). |
| `--outdir` | Output directory (default `results`). |

The file type comes from the sequence file's extension: `.gfa` is GFA, `.gff3` or `.gff`
is GFF3, anything else (including protein `.faa`) is FASTA (`.gz`/`.bgz` ignored). The
header type comes from the metadata's `schema` URL. In a clone of the repository, run
`nextflow run workflows/fairbioheaders/main.nf ...` in the same way.

## Output

- `<outdir>/combine/<id>.<input extension>`: the sequence file with its metadata header
  (`.gz`/`.bgz` when the input was compressed) — e.g. `ID.fasta` / `ID.fa` for a FASTA
  genome, `ID.faa` for a protein FASTA, `ID.gfa` for a GFA, `ID.gff3` for a GFF3. The
  header family (FHR/FHP/FHGFF3) is recorded inside the file's header, not in the name
  (issue #29 option (a)). The upstream combine refuses to overwrite the staged input, so
  an id whose `<id>.<extension>` equals the sequence file's own name (which is exactly
  what the default id derived from a single `--sequence` produces) is given the `.combined`
  disambiguator described below;
- `<outdir>/verify/<id>.verify.txt`: the verification report.

## Profiles

| Profile | Runs `bioheaders` from |
| --- | --- |
| `docker` | the modules' Seqera Wave image, `community.wave.seqera.io/library/fair-bioheaders:0.9.0--71029206d3ce1119` |
| `singularity`, `apptainer` | the modules' matching Wave `community-cr-prod` blob URL of the same build |
| `conda` | [`environment.yml`](environment.yml): `bioconda::fair-bioheaders=0.9.0` |
| `test` | the samplesheet in [`assets/test`](assets/test): a FASTA, a GFA and a GFF3 example, the FASTA with expanded JSON-LD metadata, and the repository's FHP protein example |
| none | `bioheaders` on the `PATH` (`pip install "fair-bioheaders[jsonld]"`) |

Combine `test` with one of the others, for example `-profile test,docker`.
[`assets/test/params.json`](assets/test/params.json) is the same test as a parameter file
(`-params-file`), reading the samplesheet from GitHub; Dockstore lists it as the test
parameter file.

**Container and conda environment.** Both processes are pinned upstream nf-core modules
and run the modules' Seqera Wave image, built from the Bioconda `fair-bioheaders` 0.9.0
package (Singularity/Apptainer use the matching Wave `community-cr-prod` blob URL); since
slice 4 adopted verify, no process in this workflow pulls the BioContainers/Galaxy-depot
pair any more. The conda profile uses [`environment.yml`](environment.yml), which pins the
same Bioconda package as the modules; keep the pins equal. From 0.8.2 the Bioconda package,
and so the image, includes `pyld`, the optional dependency (the `jsonld` extra) that
reading JSON-LD metadata in other than the canonical form needs, for example expanded
JSON-LD, so the workflow no longer replaces the modules' image with the project's GHCR
image. Offline mirrors that whitelist registries must allow `community.wave.seqera.io`.

The `dockstore-workflow` job of [CI](../../.github/workflows/ci.yml) checks that the
workflow sets no container and that its Bioconda pin equals the modules', then runs
`-profile test,docker`, including the expanded JSON-LD and FHP rows of the test
samplesheet.
