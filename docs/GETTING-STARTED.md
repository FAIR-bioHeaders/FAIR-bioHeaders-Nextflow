# Operator and integration guide

This is a DSL2 composition suite, not a schema authority or another validator.
The default reproducible environment uses toolkit 0.9.0 and validator 0.1.0;
the separate [five-type handoff](FIVE-TYPE-HANDOFF.md) records actual 0.13.1
preparation, not an automatic Conda/BioContainers repin.

Use Java 21, Nextflow 26.04.6 and the hash-locked Python 3.13 environment in the
[README installation](../README.md#run-the-example). The second nf-test baseline
26.10.4 is separately checked in CI. For pinned nf-core modules/Dockstore use the
recorded container profile and module migration procedure; never edit vendored
copies to make a test pass. The toolkit's version, suite version and header
schemaVersion are distinct. No new release is performed by this guide.

The README's sequence example creates per-ID attached files and metadata under
`results/ID/sequence`; standalone mode writes `results/ID/metadata`. Use a fresh
`--outdir` for a trial and supply your own metadata for real data. The bundled
example is synthetic. Exact file checksums are calculated by the toolkit,
whereas SeqCol/accessions/authors remain supplied claims. Inputs are preserved.

| Interface/helper | Contract |
| --- | --- |
| `modules/local/create_json` | Serializes supplied values and invokes the pinned toolkit for metadata validation; does not invent fields. |
| `subworkflows/attach` | Composes canonical upstream combine/verify/convert; carries meta and sequence kind through channel tuples. |
| `modules/local/strip` | Removes file headers with the pinned toolkit; outputs preserve the selected sequence type. |
| `modules/local/verify_links` | Checks explicit local parents; file identity is not biological derivation. |
| `modules/local/gff3_validate` | Wraps the pinned validator; genome and optional header checks remain distinct layers. |
| `modules/local/utils` | Validates IDs/format allowlists, quotes shell arguments and serializes JSON; not a schema validator. |
| `tests/run.py` | External-project integration harness; optional converter-source test results gate published example outputs. |

A task failure is a nonzero workflow outcome, not a rejected scientific result
silently converted to success. GFF3 `--gff3_fail_on_errors false` deliberately
publishes error reports; unreadable/incomplete inputs still fail. Skips and
missing header/model/biology prerequisites do not pass. Reports name actual
runtime/source versions; the [capability matrix](CAPABILITY-MATRIX.md) distinguishes
source/preparation from adopted default support.

Use [PIPELINES.md](PIPELINES.md) for channel signatures and imports. Validate IDs,
quote staged paths and keep native outputs under `task.workDir`. Run untrusted
workflows only in an appropriate sandbox: a Nextflow script can execute commands,
containers can access mounted files and compression/jobs still consume resources.
This suite is not a hostile workflow isolation service. Ordinary data validation
uses bundled schemas; dependency installation and explicit Nextflow/container
resolution can use the network. See [maintenance](ROUND16-MAINTENANCE.md) and
[CONTRIBUTING](../CONTRIBUTING.md) for checks and human-only merges.
