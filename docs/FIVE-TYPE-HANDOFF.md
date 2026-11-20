# Five-type native runtime handoff

The toolkit owns schema/model validation; this repository composes its normal
commands with native Nextflow DSL2. This handoff is separate from the immutable
0.9.0 conda/container baseline and does not silently upgrade upstream modules.

## Published authority

- FHT contract 1.0: shared v0.7.0, commit
  `623c79fe58edeb238a20fb6de518c62dd69b92bc`,
  [release](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/releases/tag/v0.7.0),
  [archive](https://doi.org/10.5281/zenodo.24385024).
- Native FHGM model 0.1: shared v0.8.0, commit
  `72cb46b98160ecc7a7f20ef579a6879d5030c40b`,
  [release](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/releases/tag/v0.8.0),
  [archive](https://doi.org/10.5281/zenodo.24385999).
  FHGM is carried by FHGFF3; it is not another header type, registry row or
  in-record schema/schemaVersion. Model and feature/biology validity are distinct.

`tests/fixtures/five-types/provenance.json` records exact selected source bytes.
The FHT/publication and preserved owning native-model cases are not a replacement
conformance corpus. No biological provenance or metadata is invented.

## Native acceptance surface

`tests/run_family_acceptance.py` drives `tests/family_integration.nf` from an
external working directory. It uses the existing create/validate, upstream
verify/convert/combine, attach, strip and parent-link modules. Native Groovy
assertions compare metadata values and exact payload bytes; no validator or
checksum implementation is duplicated here. Source checks and all round-trip
assertion branches must complete before normal results are published. Parent
identity is asserted only for the explicit supplied-parent case; other cases
record it as not requested, rather than counting an unchecked parent as a pass.

| Type | Prepared operation/serialization checks | Explicit boundaries |
| --- | --- | --- |
| FHR | create/validate/verify/attach/strip; JSON/YAML/HTML/FASTA/GFA/JSON-LD round trips | Existing named parent-chain baseline is separate |
| FHP | create/validate/verify/attach/strip; JSON/YAML/HTML/FASTA round trips | Protein identity remains in metadata, not output extension |
| FHGFF3 | create/validate/verify/attach/strip; JSON/YAML/typed HTML/GFF3 round trips | HTML is experimental; no JSON-LD |
| FHT | create/validate/verify/attach/strip; JSON/YAML/typed HTML/FASTA; gzip and exact FHR-parent case; C1 rejection with no normal outputs | No JSON-LD/GFA adoption; parent identity is not derivation proof |
| FHGM | native model verification in FHGFF3, JSON/YAML/GFF3 extension preservation, gzip; invalid model rejection with no normal outputs | Explicit implementation opt-in; no FHGM header or HTML/JSON-LD parity, predecessor-history staging remains outside this lane |

At this preparation checkpoint the next toolkit publication is not yet available.
The 0.13.0 tag failed its publication metadata guard and produced no GitHub Release
or registry release; its candidate receipts remain historical preparation. The
corrected publication vehicle is 0.13.1, to be used only after actual artifact verification. Candidate runs
must use `--preparation-only` and never fill the published-release receipt. The
final owning FHT handoff needs a named actual published wheel and exact installed
source proof; a candidate version string is insufficient.

```sh
python tests/run_family_acceptance.py \
  --nextflow /absolute/path/nextflow \
  --bioheaders /absolute/released/venv/bin/bioheaders \
  --expected-toolkit ACTUAL_PUBLISHED_VERSION \
  --wheel /absolute/release/fair_bioheaders-ACTUAL_PUBLISHED_VERSION-py3-none-any.whl \
  --wheel-sha256 MEASURED_PYPI_SHA256 \
  --artifact-url VERIFIED_RELEASE_DOWNLOAD_URL \
  --output /absolute/evidence/26.04.6
```

Repeat on the other supported baseline,26.10.4. The command records runtime
versions, fixture hashes, emitted artifacts and rejection outcomes. The five
existing header/model families are distinct from the five old Dockstore file-mode
rows. Native execution does not establish that the pinned 0.9.0 container can read
FHT or native FHGM.

## Remaining delivery and dependency direction

Actual toolkit publication/installed receipts precede final native release
acceptance. A default conda/container promotion additionally needs an actual
Bioconda package, BioContainer and Galaxy depot image plus reviewed upstream
module revisions. Existing pinned upstream files stay byte-identical; no future
container URL is invented. Source #7 retains this delivery work. Historical #35
closure is not used as proof of runtime completion.

The concrete FHT native runtime/fixture handoff to FHT-Specification#9 is a named
artifact. It does not require the entire Nextflow distribution tracker to close.
Likewise external alias or upstream release-owner work must not be replaced with
an unearned runtime claim. No new source issue or public pilot is required here.
