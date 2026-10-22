# FHP (protein FASTA) fixtures

Synthetic inputs for the protein slice of `tests/run.py`. The structure, protein
sequences, accessions, software and parent files are invented for testing. The
taxon (*Homo sapiens*, NCBI taxonomy 9606), the author identities (Adam Wright,
ORCID 0000-0002-5719-4024; David Molik, ORCID 0000-0003-3192-6538) and the
existing example schema style are reused from `examples/metadata.json` so the
fixtures match the repository's example; they are not new assertions about a
real dataset.

The metadata cites the bundled FHP release schema
`https://w3id.org/fair-bioheaders/fhp/v0.4.0` (`schemaVersion` `1.0`) and the
FHGFF3 release schema `https://w3id.org/fair-bioheaders/fhgff3/v0.4.0`
(`schemaVersion` `1.0`); the FHR genome cites
`https://w3id.org/fair-bioheaders/fhr/v0.3.1` (`schemaVersion` 1). The combined
files were written by **fair-bioheaders 0.8.0**, whose checksum algorithm covers
the exact file bytes except the scalar root checksum line; do not hand-edit them.

| File | Purpose |
| --- | --- |
| `protein.faa` | Bare synthetic protein FASTA (two sequences) |
| `protein.faa.gz` | The same sequences, gzip input (detected by magic bytes) |
| `predicted.fhp.json` | Standalone FHP metadata, `sourceType` `predicted`, placeholder checksum |
| `database.fhp.json` | Standalone FHP metadata, `sourceType` `database`, a `source` entry |
| `mixed.fhp.json` | Standalone FHP metadata, `sourceType` `mixed`, two `source` entries |
| `malformed-missing-proteome.fhp.faa` | Combined FHP FASTA missing the required `proteome` field |
| `malformed-duplicate-checksum.fhp.faa` | Combined FHP FASTA with two root checksum lines |
| `chain/genome.fa`, `chain/genome.fhr.json` | Bare and metadata inputs for the genome |
| `chain/genome.fhr.fasta` | Combined FHR genome FASTA (checksum `IHnspOEQ7lB6QJ5S+ZoWIFgWkOekkupMTD+O8pDY9IA=`) |
| `chain/annotation.gff3`, `chain/annotation.fhgff3.json` | Bare and metadata inputs for the annotation |
| `chain/annotation.fhgff3.gff3` | Combined FHGFF3 annotation, `derivedFrom` the genome (checksum `i39XyXNn8l+EuiVfS3TaZMD6LnYXG9xVzhZByFMGe8c=`) |
| `chain/other-annotation.fhgff3.json`, `chain/other-annotation.fhgff3.gff3` | A same-type parent with a different checksum (checksum `4JrZso3R4DI/HqMwt6esZ5YgOTcqhgj1PG9qJu59Xog=`) |
| `chain/protein.fhp.json` | FHP metadata whose `derivedFrom` records the annotation (placeholder checksum) |
| `chain/protein.fhp.faa` | Combined FHP protein FASTA (checksum `vW8Ur/Nkj7a/64LAfI5Qdy2O0CudSLCBD6WL/jmdA0Y=`) |

Expected behaviour with fair-bioheaders 0.8.0:

- `fhr-fasta-validate` accepts `chain/protein.fhp.faa` and rejects both
  `malformed-*` files (missing required property; duplicate YAML key).
- `bioheaders verify-links chain/protein.fhp.faa chain/annotation.fhgff3.gff3`
  matches (exit 0); with `chain/other-annotation.fhgff3.gff3` it does not match
  (exit 3); with no parents it is "not checked" (exit 0, or exit 3 with
  `--require-all`).
- `bioheaders verify-links --type gff3 chain/annotation.fhgff3.gff3
  chain/genome.fhr.fasta` matches, completing the genome → annotation → protein
  chain. A match proves file identity by checksum, not translation correctness.

These files are licensed MPL-2.0 with the repository.
