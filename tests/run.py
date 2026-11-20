#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Exercise DSL2 modules in an external project, with no testing framework dependency."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = 'A' * 43 + '='
parser = argparse.ArgumentParser()
parser.add_argument('--nextflow', default='nextflow')
parser.add_argument('--converter-source', type=Path)
args = parser.parse_args()
env = dict(os.environ, NXF_OFFLINE='true', NXF_SYNTAX_PARSER='v2')
passed = []


class CheckFailed(Exception):
    pass


def check(condition, message):
    """Explicit check that, unlike assert, is not removed by python -O."""
    if not condition:
        raise CheckFailed(message)


def run(script, directory, options=(), failure=None):
    result = subprocess.run([args.nextflow, 'run', str(script), '-ansi-log', 'false', '-c', str(directory / 'nextflow.config'), *options], cwd=directory, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if failure:
        check(result.returncode != 0 and failure in result.stdout, f'expected failure containing {failure!r}:\n{result.stdout}')
    else:
        check(result.returncode == 0, result.stdout)
    name = Path(script).name
    passed.append(name)
    print(f'{name}: expected rejection ({failure})' if failure else f'{name}: passed', flush=True)
    return result.stdout


def published(directory):
    return sorted(str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file())


def junit_totals(path):
    def count(node):
        cases = list(node.findall('testcase'))
        suites = [child for child in node if child.tag in ('testsuite', 'testsuites')]
        if not cases and not suites:
            # A summary-only leaf has no atomic evidence to count instead.
            return tuple(int(node.get(key, 0)) for key in ('tests', 'failures', 'errors', 'skipped'))
        own = (len(cases), sum(case.find('failure') is not None for case in cases),
               sum(case.find('error') is not None for case in cases),
               sum(case.find('skipped') is not None for case in cases))
        # Ignore aggregate attributes, but retain summary-only sibling leaves.
        children = [count(suite) for suite in suites]
        return tuple(own[i] + sum(child[i] for child in children) for i in range(4))
    return count(ET.parse(path).getroot())


def snapshot(directory):
    return {str(path.relative_to(directory)): path.stat().st_mtime_ns for path in directory.rglob('*') if '.git' not in path.parts}


def main():
    with tempfile.TemporaryDirectory(prefix='fhr-nextflow-tests-') as tmp:
        work = Path(tmp)
        (work / 'nextflow.config').write_text('nextflow.enable.dsl = 2\nprocess { withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { meta.id } } }\n')
        fields = json.loads((ROOT / 'examples/metadata.json').read_text())
        fields['documentation'] = "Unicode β; quotes ' and \\" + '"; $(touch SHOULD_NOT_EXIST)'
        fixture = work / "metadata with ' quotes.json"
        fixture.write_text(json.dumps(fields))

        # Native composition: five metadata round trips and two exact-byte sequence round trips.
        integration = work / 'integration.nf'
        integration.write_text((ROOT / 'tests/integration.nf').read_text().replace("from '../", f"from '{ROOT}/"))
        run(integration, work, ['--fixture', str(fixture), '--fixtures', str(ROOT / 'examples')])
        check(len(list((work / 'work').glob('*/*/*.ok'))) == 7, 'expected seven round-trip markers')
        check(not list(work.rglob('SHOULD_NOT_EXIST')), 'shell metacharacters in metadata were executed')
        created = next((work / 'work').glob('*/*/rich.json')).read_text(encoding='utf-8')
        check('Unicode β' in created and '\\u03b2' not in created, 'non-ASCII metadata was escaped')

        # Serializer edge cases: Unicode, nulls, sets, Date/NaN/Infinity rejection.
        json_test = work / 'json.nf'
        json_test.write_text((ROOT / 'tests/json.nf').read_text().replace("from '../", f"from '{ROOT}/"))
        check('JSON serialization:' in run(json_test, work), 'JSON edge-case script did not report')
        date_field = work / 'date-field.nf'
        date_field.write_text("include { FHR_CREATE_JSON } from '" + str(ROOT / 'modules/local/create_json/main') + "'\nworkflow { FHR_CREATE_JSON(Channel.of(tuple([id:'date'], [dateCreated: new Date(0)]))) }\n")
        run(date_field, work, failure='unsupported type java.util.Date')

        # Missing required metadata and invalid digest must fail before JSON is emitted.
        for name, change, message in [('missing', lambda f: f.pop('genome'), 'genome'), ('seqcol', lambda f: f.update(seqcol_id='bad'), 'seqcol_id')]:
            invalid = dict(fields)
            change(invalid)
            source = work / f'{name}.json'
            source.write_text(json.dumps(invalid))
            run(ROOT / 'main.nf', work, ['--metadata', str(source), '--outdir', str(work / name)], failure=message)
            check(not (work / name).exists(), f'{name}: outputs were published after a validation failure')
        malformed = work / 'malformed.json'
        malformed.write_text('{broken')
        run(ROOT / 'main.nf', work, ['--metadata', str(malformed)], failure='Cannot parse metadata JSON')
        run(ROOT / 'main.nf', work, ['--id', '../unsafe'], failure='meta.id')
        run(ROOT / 'main.nf', work, ['--id', '123', '--outdir', str(work / 'numeric-id')])
        check((work / 'numeric-id/123/metadata/123.json').exists(), 'numeric --id was not accepted as a sample ID')
        run(ROOT / 'main.nf', work, ['--metadata', str(fixture)], failure='rename the file or use --id')
        bad_format = work / 'bad-format.nf'
        bad_format.write_text("include { FAIRBIOHEADERS_CONVERT } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/convert/main') + "'\nworkflow { FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id:'bad'], file(params.metadata))), Channel.value('exe')) }\n")
        # Upstream convert has no pre-launch format whitelist: an unusable --to token
        # fails inside the task (the toolkit's argparse), where FHR_CONVERT used to
        # reject it before submission. #29 option (a) adopts the upstream surface.
        run(bad_format, work, ['--metadata', str(fixture)], failure="invalid choice: 'exe'")
        attached = next((work / 'work').glob('*/*/attached-fasta.fasta'))
        tampered = work / 'tampered.fasta'
        tampered.write_bytes(attached.read_bytes().replace(b'AAAATCGATCGGCATA', b'TAAATCGATCGGCATA'))
        bad_checksum = work / 'bad-checksum.nf'
        bad_checksum.write_text("include { FAIRBIOHEADERS_VERIFY } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/verify/main') + "'\nworkflow { FAIRBIOHEADERS_VERIFY(Channel.of(tuple([id:'tampered'], file(params.sequence)))) }\n")
        run(bad_checksum, work, ['--sequence', str(tampered)], failure='checksum')
        # FHR lines must form the leading header block (converter 0.3.1).
        late_header = work / 'late-header.fasta'
        late_header.write_bytes(attached.read_bytes() + b';~documentation: after the sequence\n')
        run(bad_checksum, work, ['--sequence', str(late_header)], failure='after sequence data')
        concatenated = work / 'concatenated.fasta'
        concatenated.write_bytes(attached.read_bytes() * 2)
        run(bad_checksum, work, ['--sequence', str(concatenated)], failure='after sequence data')

        # Several metadata files: one output directory per file-derived ID, never shared.
        batch = work / 'batch'
        for directory, name, genome in [('one', 'alpha.json', 'Alpha'), ('one', 'beta.fhr.json', 'Beta'), ('two', 'alpha.json', 'Alpha again')]:
            (batch / directory).mkdir(parents=True, exist_ok=True)
            (batch / directory / name).write_text(json.dumps(dict(fields, genome=genome)))
        output = work / 'batch-output'
        run(ROOT / 'main.nf', work, ['--metadata', str(batch / 'one/*.json'), '--outdir', str(output)])
        expected = ['alpha/metadata/alpha.json', 'alpha/metadata/alpha.yaml', 'beta/metadata/beta.json', 'beta/metadata/beta.yaml']
        check(published(output) == expected, f'unexpected batch outputs: {published(output)}')
        for sample, genome in [('alpha', 'Alpha'), ('beta', 'Beta')]:
            check(json.loads((output / sample / 'metadata' / f'{sample}.json').read_text())['genome'] == genome, f'{sample}: output belongs to another input')
        run(ROOT / 'main.nf', work, ['--metadata', str(batch / '*/alpha.json'), '--outdir', str(work / 'duplicate')], failure='Duplicate meta.id')
        run(ROOT / 'main.nf', work, ['--metadata', str(batch / 'one/*.json'), '--id', 'shared', '--outdir', str(work / 'shared')], failure='--id names a single output')
        check(not (work / 'duplicate').exists() and not (work / 'shared').exists(), 'outputs were published for ambiguous IDs')

        # With a sequence, only the attached file and metadata carrying its computed checksum are published.
        output = work / 'sequence-output'
        run(ROOT / 'main.nf', work, ['--sequence', str(ROOT / 'examples/assembly.gfa'), '--sequence_format', 'gfa', '--outdir', str(output)])
        expected = ['example/sequence/example.gfa', 'example/sequence/example.json', 'example/sequence/example.yaml']
        check(published(output) == expected, f'unexpected sequence outputs: {published(output)}')
        for name in published(output):
            check(PLACEHOLDER.encode() not in (output / name).read_bytes(), f'{name} contains the placeholder checksum')

        # GFF3 validation: optional genome ([]), gzip input, warnings, errors, incomplete input.
        gff3 = ROOT / 'tests/fixtures/gff3'
        module = "include { GFF3_VALIDATE } from '" + str(ROOT / 'modules/local/gff3_validate/main') + "'\n"
        gff3_module = work / 'gff3-module.nf'
        gff3_module.write_text(module + """workflow {
    def fixtures = params.fixtures
    GFF3_VALIDATE(Channel.of(
        tuple([id: 'plain'], file("${fixtures}/genes-with-genome.gff3"), []),
        tuple([id: 'gz'], file("${fixtures}/canonical-gene-gzip.gff3.gz"), []),
        tuple([id: 'stop'], file("${fixtures}/bio-008-internal-stop.gff3"), file("${fixtures}/genome.fa")),
        tuple([id: 'duplicate'], file("${fixtures}/str-001-duplicate-id.gff3"), [])
    ).filter { meta, gff3, genome -> meta.id in params.ids.tokenize(',') })
    GFF3_VALIDATE.out.valid.map { meta, gff3 -> "VALID ${meta.id} ${gff3.name}" }.view()
    GFF3_VALIDATE.out.reports.map { meta, json, html -> "REPORT ${meta.id} ${json.name} ${html.name}" }.view()
}
""")
        output = run(gff3_module, work, ['--fixtures', str(gff3), '--ids', 'plain,gz,stop'])
        for sample, name in [('plain', 'genes-with-genome.gff3'), ('gz', 'canonical-gene-gzip.gff3.gz'), ('stop', 'bio-008-internal-stop.gff3')]:
            check(f'VALID {sample} {name}' in output, f'{sample}: valid GFF3 not emitted on valid:\n{output}')
            check(f'REPORT {sample} {sample}.gff3-validate.json {sample}.gff3-validate.html' in output, f'{sample}: reports not emitted')
        report = json.loads(next((work / 'work').glob('*/*/stop.gff3-validate.json')).read_text())
        check(report['valid'] and report['tool']['version'] == '0.1.0', f'unexpected genome report: {report}')
        check([f['rule'] for f in report['findings']] == ['BIO-008'], f'expected one BIO-008 warning with the genome: {report["findings"]}')
        check('<html' in next((work / 'work').glob('*/*/stop.gff3-validate.html')).read_text().lower(), 'HTML report missing')
        run(gff3_module, work, ['--fixtures', str(gff3), '--ids', 'duplicate'], failure='GFF3 validation failed for str-001-duplicate-id.gff3')
        check(any('GFF-STR-001' in path.read_text() for path in (work / 'work').glob('*/*/duplicate.gff3-validate.json')), 'failing task did not keep its JSON report')
        bad_genome = work / 'bad-genome.nf'
        bad_genome.write_text(module + "workflow { GFF3_VALIDATE(Channel.of(tuple([id:'stop'], file(params.gff3), file(params.genome)))) }\n")
        run(bad_genome, work, ['--gff3', str(gff3 / 'bio-008-internal-stop.gff3'), '--genome', str(gff3 / 'str-001-duplicate-id.gff3')], failure='validation incomplete')
        bad_id = work / 'gff3-bad-id.nf'
        bad_id.write_text(module + "workflow { GFF3_VALIDATE(Channel.of(tuple([id:'../x'], file(params.gff3), []))) }\n")
        run(bad_id, work, ['--gff3', str(gff3 / 'genes-with-genome.gff3')], failure='meta.id')
        # fail_on_errors = false: invalid files emit reports but are not emitted on valid.
        lenient = work / 'gff3-continue'
        lenient.mkdir()
        (lenient / 'nextflow.config').write_text('nextflow.enable.dsl = 2\nprocess { withName: GFF3_VALIDATE { ext.fail_on_errors = false } }\n')
        output = run(gff3_module, lenient, ['--fixtures', str(gff3), '--ids', 'plain,duplicate'])
        check('VALID plain' in output and 'VALID duplicate' not in output, f'invalid GFF3 emitted on valid:\n{output}')
        check('REPORT duplicate duplicate.gff3-validate.json' in output, 'invalid GFF3 reports not emitted')

        # Example workflow: reports published per GFF3 ID; errors fail unless --gff3_fail_on_errors false.
        output = work / 'gff3-output'
        run(ROOT / 'main.nf', work, ['--gff3', str(gff3 / '*.gff3*'), '--gff3_genome', str(gff3 / 'genome.fa'), '--outdir', str(output), '--gff3_fail_on_errors', 'false'])
        expected = sorted(f'{sample}/gff3/{sample}.gff3-validate.{ext}' for sample in ['bio-008-internal-stop', 'canonical-gene-gzip', 'genes-with-genome', 'str-001-duplicate-id'] for ext in ['html', 'json'])
        check([name for name in published(output) if '/gff3/' in name] == expected, f'unexpected GFF3 outputs: {published(output)}')
        check(not json.loads((output / 'str-001-duplicate-id/gff3/str-001-duplicate-id.gff3-validate.json').read_text())['valid'], 'invalid GFF3 reported as valid')
        run(ROOT / 'main.nf', work, ['--gff3', str(gff3 / 'str-001-duplicate-id.gff3'), '--outdir', str(work / 'gff3-strict')], failure='GFF3 validation failed')
        check(not (work / 'gff3-strict/str-001-duplicate-id').exists(), 'reports published after a failing GFF3 validation')
        run(ROOT / 'main.nf', work, ['--gff3', str(gff3 / 'genes-with-genome.gff3'), '--gff3_genome', str(work / 'missing.fa')], failure='missing.fa')
        run(ROOT / 'main.nf', work, ['--gff3', str(gff3 / 'genes-with-genome.gff3'), '--gff3_translation_table', '11'], failure='needs a genome')
        duplicate_gff3 = work / 'duplicate-gff3'
        duplicate_gff3.mkdir()
        shutil.copy(gff3 / 'genes-with-genome.gff3', duplicate_gff3 / 'sample.gff3')
        shutil.copy(gff3 / 'canonical-gene-gzip.gff3.gz', duplicate_gff3 / 'sample.gff3.gz')
        run(ROOT / 'main.nf', work, ['--gff3', str(duplicate_gff3 / '*'), '--outdir', str(work / 'gff3-duplicate')], failure='Duplicate meta.id from GFF3 files')

        # Protein FASTA (FHP): create/convert/attach/strip, validation, malformed
        # headers and parent-link verification through the pinned toolkit.
        fhp = ROOT / 'tests/fixtures/fhp'
        chain = fhp / 'chain'
        create = "include { FHR_CREATE_JSON } from '" + str(ROOT / 'modules/local/create_json/main') + "'\n"
        convert = "include { FAIRBIOHEADERS_CONVERT } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/convert/main') + "'\n"
        attach = "include { FHR_ATTACH } from '" + str(ROOT / 'subworkflows/attach/main') + "'\n"
        strip = "include { FHR_STRIP } from '" + str(ROOT / 'modules/local/strip/main') + "'\n"
        verify_header = "include { FAIRBIOHEADERS_VERIFY } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/verify/main') + "'\n"
        validate = "include { FAIRBIOHEADERS_VALIDATE } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/validate/main') + "'\n"
        verify = "include { FHR_VERIFY_LINKS } from '" + str(ROOT / 'modules/local/verify_links/main') + "'\n"

        compose = work / 'fhp-compose.nf'
        compose.write_text(create + convert + attach + strip + """process ASSERT_PROTEIN_BYTES {
    input:
    tuple val(meta), val(sequence)
    output:
    path "${meta.id}.ok"
    exec:
    assert java.util.Arrays.equals(sequence.bytes, file(meta.original).bytes)
    task.workDir.resolve("${meta.id}.ok").text = 'OK\\n'
}

workflow {
    def records = params.metadata.tokenize(',').collect { path ->
        def source = file(path)
        tuple([id: source.name.replaceFirst(/\\.fhp\\.json$/, '')], new groovy.json.JsonSlurper().parseText(source.text))
    }
    FHR_CREATE_JSON(Channel.fromList(records))
    // Issue #29 option (a): the header-only protein conversion uses the upstream
    // convert, whose extension is the --to token, so a protein header serialises to
    // <id>.fasta (there is no --to faa). The protein/genome distinction is NOT in the
    // file name any more; it rides on meta.sequenceKind and on the FHP header inside
    // the file. A distinct id keeps the header-only conversion (<id>-header.fasta)
    // apart from the attached file (<id>.faa) and its extracted JSON (<id>.json).
    def header = FHR_CREATE_JSON.out.json.map { meta, json -> tuple([id: meta.id + '-header', sequenceKind: 'faa'], json) }
    FAIRBIOHEADERS_CONVERT(header, Channel.value('fasta'))
    FHR_ATTACH(FHR_CREATE_JSON.out.json.map { meta, json -> tuple(meta, json, file(params.sequence, checkIfExists: true), 'faa') })
    FHR_STRIP(FHR_ATTACH.out.sequence.map { meta, sequence -> tuple([id: meta.id, original: params.original], sequence, 'faa') })
    ASSERT_PROTEIN_BYTES(FHR_STRIP.out.stripped)
    FHR_CREATE_JSON.out.json.view { meta, json -> "CREATED ${meta.id} ${json.name}" }
    FAIRBIOHEADERS_CONVERT.out.metadata.view { meta, converted -> "CONVERTED ${meta.id} kind=${meta.sequenceKind} ${converted.name}" }
    FHR_ATTACH.out.sequence.view { meta, sequence -> "ATTACHED ${meta.id} ${sequence.name}" }
    FHR_ATTACH.out.json.view { meta, json -> "EXTRACTED ${meta.id} ${json.name}" }
    FHR_STRIP.out.stripped.view { meta, sequence -> "STRIPPED ${meta.id} ${sequence.name}" }
}
""")
        sets = ','.join(str(fhp / f'{name}.fhp.json') for name in ['predicted', 'database', 'mixed'])
        before_ok = len(list((work / 'work').glob('*/*/*.ok')))
        output = run(compose, work, ['--metadata', sets, '--sequence', str(fhp / 'protein.faa'), '--original', str(fhp / 'protein.faa')])
        for sample in ['predicted', 'database', 'mixed']:
            for marker in [f'CREATED {sample} {sample}.json', f'CONVERTED {sample}-header kind=faa {sample}-header.fasta', f'ATTACHED {sample} {sample}.faa', f'EXTRACTED {sample} {sample}.json', f'STRIPPED {sample} {sample}.stripped.faa']:
                check(marker in output, f'{sample}: missing {marker!r}:\n{output}')
        check(len(list((work / 'work').glob('*/*/*.ok'))) == before_ok + 3, 'protein strip byte checks did not run')
        for sample in ['predicted', 'database', 'mixed']:
            records = [json.loads(path.read_text()) for path in (work / 'work').glob(f'*/*/{sample}.json')]
            check(records and all(record['sourceType'] == sample for record in records), f'{sample}: metadata lost sourceType')
            check(any(record['checksum'] != PLACEHOLDER for record in records), f'{sample}: attachment did not replace the placeholder checksum')
        # The header-only protein file is a .fasta (extension is the --to token), yet its
        # bytes are an FHP header: the family is proven by content and meta, not by .faa.
        converted = next((work / 'work').glob('*/*/predicted-header.fasta')).read_text()
        check(converted.startswith(';~schema: https://w3id.org/fair-bioheaders/fhp/') and '>' not in converted, f'FHP metadata-to-fasta conversion is not an FHP header:\n{converted}')
        # A supported compressed input is read by its magic bytes.
        output = run(compose, work, ['--metadata', sets, '--sequence', str(fhp / 'protein.faa.gz'), '--original', str(fhp / 'protein.faa')])
        # Combine keeps the input's compression: the attached file is BGZF.
        check('ATTACHED predicted predicted.faa.gz' in output, f'compressed protein input was not combined:\n{output}')

        faa_verify = work / 'faa-verify.nf'
        faa_verify.write_text(verify_header + """workflow {
    FAIRBIOHEADERS_VERIFY(Channel.of(tuple([id: params.id ?: 'protein'], file(params.sequence, checkIfExists: true))))
    FAIRBIOHEADERS_VERIFY.out.report.view { meta, report -> "VERIFIED ${meta.id} ${report.name}" }
}
""")
        output = run(faa_verify, work, ['--sequence', str(chain / 'protein.fhp.faa')])
        check('VERIFIED protein protein.verify.txt' in output, f'FHP FASTA was not verified:\n{output}')
        run(faa_verify, work, ['--sequence', str(fhp / 'malformed-missing-proteome.fhp.faa')], failure='proteome')
        run(faa_verify, work, ['--sequence', str(fhp / 'malformed-duplicate-checksum.fhp.faa')], failure='duplicate key')

        # Direct FHGFF3 verification (issue #29 slice 4): these three cases moved here
        # from the retired repository verify suite, whose nf-tests the pinned upstream
        # nf-core/modules revision 6fb4f8f1 does not carry (its four cases cover plain
        # FHR FASTA, changed-after-combine, no-header and stub). The compressed case
        # stays covered through the FHR_ATTACH gzip run below, which only emits its
        # ATTACHED marker after verify has joined a passing report for the BGZF file.
        output = run(faa_verify, work, ['--id', 'annotation', '--sequence', str(chain / 'annotation.fhgff3.gff3')])
        check('VERIFIED annotation annotation.verify.txt' in output, f'FHGFF3 was not verified:\n{output}')
        # Without the retired local module's --type whitelist the toolkit infers the
        # sequence type from the extension and rejects odd ones in the task; the local
        # module forced any non-GFA/GFF3 name to FASTA instead (docs/module-migration.md).
        odd_extension = work / 'protein-header.txt'
        odd_extension.write_bytes((chain / 'protein.fhp.faa').read_bytes())
        run(faa_verify, work, ['--id', 'odd', '--sequence', str(odd_extension)], failure='Unsupported file extension')
        # The merged upstream revision dropped the spaced-name tests its review heads
        # carried (as convert did); this suite keeps the verify case: the staged path
        # holds spaces and the module interpolates it unquoted, so success plus a
        # single-line file: report pins Nextflow's staged-path escaping.
        spaced_sequence = work / 'protein with space.faa'
        spaced_sequence.write_bytes((chain / 'protein.fhp.faa').read_bytes())
        output = run(faa_verify, work, ['--id', 'spaced', '--sequence', str(spaced_sequence)])
        check('VERIFIED spaced spaced.verify.txt' in output, f'spaced-name FHP FASTA was not verified:\n{output}')
        report_lines = next((work / 'work').glob('*/*/spaced.verify.txt')).read_text().splitlines()
        check(len(report_lines) == 2 and report_lines[0].startswith('file: ')
              and report_lines[0].endswith('protein with space.faa')
              and report_lines[1] == 'Checksum verified.',
              f'spaced-name verify report is not the documented two lines: {report_lines}')
        # The same case on the **prefix** (F8): since nf-core/modules def10bc21a the
        # pinned modules double-quote their prefix-derived output paths, so a
        # caller-supplied ext.prefix containing a space now names the report as given.
        # (Until that pin move the unquoted redirect died with "syntax error near
        # unexpected token `prefix.verify.txt'"; this assertion replaced that one.)
        # Double quotes do not stop $(...) or backtick expansion, so the suite's own
        # callers still gate every id with isSampleId (see the Dockstore cases below).
        prefix_dir = work / 'verify-spaced-prefix'
        prefix_dir.mkdir()
        (prefix_dir / 'nextflow.config').write_text("nextflow.enable.dsl = 2\nprocess { withName: FAIRBIOHEADERS_VERIFY { ext.prefix = { 'spaced prefix' } } }\n")
        output = run(faa_verify, prefix_dir, ['--sequence', str(chain / 'protein.fhp.faa')])
        check('VERIFIED protein spaced prefix.verify.txt' in output, f'a spaced ext.prefix did not name the verify report:\n{output}')

        # Standalone FHP metadata: FAIRBIOHEADERS_VALIDATE (no sequence, no checksum check).
        validate_script = work / 'fhp-validate.nf'
        validate_script.write_text(validate + """workflow {
    FAIRBIOHEADERS_VALIDATE(Channel.of(tuple([id: 'metadata'], file(params.metadata, checkIfExists: true))))
    FAIRBIOHEADERS_VALIDATE.out.report.view { meta, report -> "VALIDATED ${meta.id} ${report.name}" }
}
""")
        output = run(validate_script, work, ['--metadata', str(fhp / 'mixed.fhp.json')])
        check('VALIDATED metadata metadata.validate.txt' in output, f'FHP metadata was not validated:\n{output}')
        invalid = json.loads((fhp / 'predicted.fhp.json').read_text())
        invalid.pop('sourceType')
        source = work / 'fhp-no-sourcetype.fhp.json'
        source.write_text(json.dumps(invalid))
        run(validate_script, work, ['--metadata', str(source)], failure='sourceType')

        # FHR 2.1 x- extension fields through FAIRBIOHEADERS_VALIDATE (issue #29):
        # these cases moved here when the module was pinned to the upstream
        # nf-core/modules revision 86e852ef, whose tests do not cover the FHR 2.1
        # x- rule; see docs/module-migration.md.
        fhr21 = dict(fields, schema='https://w3id.org/fair-bioheaders/fhr/v0.5.0', schemaVersion='2.1', **{'x-example-pipeline': {'name': 'test-pipeline', 'steps': ['assemble']}})
        source = work / 'fhr21-extension.fhr.json'
        source.write_text(json.dumps(fhr21))
        output = run(validate_script, work, ['--metadata', str(source)])
        check('VALIDATED metadata metadata.validate.txt' in output, f'FHR 2.1 x- extension field was not validated:\n{output}')
        fhr20 = dict(fhr21, schema='https://w3id.org/fair-bioheaders/fhr/v0.4.0', schemaVersion='2.0')
        source = work / 'fhr20-extension.fhr.json'
        source.write_text(json.dumps(fhr20))
        run(validate_script, work, ['--metadata', str(source)], failure='x-example-pipeline')

        # Invalid FHP metadata is rejected by the pinned schema, not by Nextflow.
        for name, change, message in [
            ('fhp-missing', lambda fields: fields.pop('proteome'), 'proteome'),
            ('fhp-sourcetype', lambda fields: fields.update(sourceType='unknown'), 'sourceType'),
            ('fhp-schema', lambda fields: fields.update(schema='https://w3id.org/fair-bioheaders/fhp/v9.9.9'), 'unsupported schema version'),
        ]:
            invalid = json.loads((fhp / 'predicted.fhp.json').read_text())
            change(invalid)
            source = work / f'{name}.fhp.json'
            source.write_text(json.dumps(invalid))
            run(ROOT / 'main.nf', work, ['--metadata', str(source), '--outdir', str(work / name)], failure=message)
            check(not (work / name).exists(), f'{name}: outputs were published after a validation failure')

        # FHP HTML microdata is supported from toolkit 0.8.2 (FAIR-bioHeaders-Tools#98,
        # which closed #58): FHP metadata round-trips through HTML.
        fhp_html = work / 'fhp-html.nf'
        fhp_html.write_text(convert + "include { FAIRBIOHEADERS_CONVERT as BACK_TO_JSON } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/convert/main') + "'\n" + """workflow {
    FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id: 'fhp'], file(params.metadata, checkIfExists: true))), Channel.value('html'))
    BACK_TO_JSON(FAIRBIOHEADERS_CONVERT.out.metadata.map { meta, html -> tuple([id: 'fhp-back'], html) }, Channel.value('json'))
    BACK_TO_JSON.out.metadata.view { meta, json -> "ROUNDTRIP ${json}" }
}
""")
        output = run(fhp_html, work, ['--metadata', str(fhp / 'predicted.fhp.json')])
        back = Path(next(line for line in output.splitlines() if line.startswith('ROUNDTRIP ')).split(' ', 1)[1])
        check(json.loads(back.read_text()) == json.loads((fhp / 'predicted.fhp.json').read_text()), 'FHP metadata did not round-trip through HTML')

        # The suite's convert is now the pinned upstream fairbioheaders/convert
        # (FHR_CONVERT is retired). This runs it on this repository's fixtures and
        # asserts the observable contract of issue #29 option (a): plain <id>.<format>
        # output names via ext.prefix = meta.id (set in the harness project's
        # nextflow.config), header extraction from a combined FHP file, and the two
        # upstream failure surfaces -- an unusable --to token fails inside the task,
        # and an output name that would overwrite a staged input is refused.
        pinned_convert = "include { FAIRBIOHEADERS_CONVERT } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/convert/main') + "'\n"
        parity_meta = work / 'parity-metadata.json'
        parity_meta.write_text(json.dumps(fields))
        conv = work / 'convert-upstream.nf'
        conv.write_text(pinned_convert + """workflow {
    def plain = file(params.metadata, checkIfExists: true)
    def records = [
        tuple('json', plain, 'json'),
        tuple('yaml', plain, 'yaml'),
        tuple('html', plain, 'html'),
        tuple('extract', file(params.protein, checkIfExists: true), 'json')
    ]
    FAIRBIOHEADERS_CONVERT(
        Channel.fromList(records.collect { key, path, fmt -> tuple([id: "cvt-${key}".toString()], path) }),
        Channel.fromList(records.collect { key, path, fmt -> fmt })
    )
    FAIRBIOHEADERS_CONVERT.out.metadata.view { meta, path -> "CONVERTED ${meta.id} ${path.name}" }
}
""")
        output = run(conv, work, ['--metadata', str(parity_meta), '--protein', str(chain / 'protein.fhp.faa')])
        for key, name in [('json', 'cvt-json.json'), ('yaml', 'cvt-yaml.yaml'), ('html', 'cvt-html.html'), ('extract', 'cvt-extract.json')]:
            check(f'CONVERTED cvt-{key} {name}' in output, f'{key}: the upstream convert did not publish the plain <id>.<format> name:\n{output}')
        # The extracted sidecar is the FHP header of the combined file, as JSON.
        extracted = json.loads(next((work / 'work').glob('*/*/cvt-extract.json')).read_text())
        check(extracted['schema'].endswith('/fhp/v0.4.0') and extracted['sourceType'] == 'predicted', f'header extraction lost FHP metadata: {extracted}')

        # Upstream rejects an unknown or unsupported --to token inside the task (the
        # toolkit's argparse); there is no `faa` token, and no pre-launch whitelist.
        for format, message in [('faa', "invalid choice: 'faa'"), ('exe', "invalid choice: 'exe'")]:
            bad_upstream = work / f'convert-upstream-{format}.nf'
            bad_upstream.write_text(pinned_convert + f"""workflow {{
    FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id: 'bad'], file(params.metadata, checkIfExists: true))), Channel.value('{format}'))
}}
""")
            run(bad_upstream, work, ['--metadata', str(parity_meta)], failure=message)

        # Upstream refuses an output that would overwrite a staged input (its documented
        # collision guard): here the output <id>.json equals the input file's own name.
        collide_meta = work / 'cvt.json'
        collide_meta.write_text(json.dumps(fields))
        collide = work / 'convert-upstream-collide.nf'
        collide.write_text(pinned_convert + """workflow {
    FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id: 'cvt'], file(params.metadata, checkIfExists: true))), Channel.value('json'))
}
""")
        run(collide, work, ['--metadata', str(collide_meta)], failure='Input and output names are the same')

        # The merged upstream revision dropped the spaced-file-name test its review head
        # carried, so this suite keeps that case: the fixture file name holds spaces and
        # single quotes and the module interpolates the staged path unquoted.
        spaced_upstream = work / 'convert-upstream-spaced.nf'
        spaced_upstream.write_text(pinned_convert + """workflow {
    FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id: 'spaced'], file(params.metadata, checkIfExists: true))), Channel.value('json'))
    FAIRBIOHEADERS_CONVERT.out.metadata.view { meta, path -> "SPACED ${path.name}" }
}
""")
        output = run(spaced_upstream, work, ['--metadata', str(fixture)])
        check('SPACED spaced.json' in output, f'the pinned upstream convert did not read the spaced and quoted metadata name:\n{output}')
        report = next((work / 'work').glob('*/*/spaced.json'))
        check(json.loads(report.read_text()) == fields, 'the pinned upstream convert did not reproduce the metadata')

        # Toolkit 0.7.0+ selects FHR 2.0 for the raw-main URL. Since 0.8.4 (spec rule V6,
        # FAIR-bioHeaders-Tools#114) a record citing raw-main with the number 1 as
        # schemaVersion is read as FHR 1 (v0.3.1) with a deprecation warning; a string
        # '1' still selects FHR 2.0 and is rejected. The bundled example cites fhr/v0.3.1.
        raw_main = json.loads((ROOT / 'examples/metadata.json').read_text())
        raw_main['schema'] = 'https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json'
        source = work / 'fhr-raw-main.json'
        source.write_text(json.dumps(raw_main))
        raw_main_work = work / 'fhr-raw-main-work'
        run(ROOT / 'main.nf', work, ['-work-dir', str(raw_main_work), '--metadata', str(source), '--outdir', str(work / 'fhr-raw-main')])
        check((work / 'fhr-raw-main/fhr-raw-main/metadata/fhr-raw-main.json').is_file(), 'raw-main FHR 1 record was not published')
        task_errors = ''.join(path.read_text() for path in raw_main_work.glob('*/*/.command.err'))
        check('is read as FHR 1 (v0.3.1)' in task_errors, f'raw-main FHR 1 record did not warn:\n{task_errors}')
        raw_main['schemaVersion'] = '1'
        source = work / 'fhr-raw-main-string.json'
        source.write_text(json.dumps(raw_main))
        run(ROOT / 'main.nf', work, ['--metadata', str(source), '--outdir', str(work / 'fhr-raw-main-string')], failure='schemaVersion')
        check(not (work / 'fhr-raw-main-string').exists(), 'fhr-raw-main-string: outputs were published after a validation failure')

        # Parent-link verification: match, unavailable and mismatching parents,
        # require_all and fail_on_mismatch, plus the genome -> annotation -> protein chain.
        verify_script = work / 'verify-links.nf'
        verify_script.write_text(verify + """workflow {
    def parents = params.parents ? params.parents.tokenize(',').collect { file(it, checkIfExists: true) } : []
    FHR_VERIFY_LINKS(Channel.of(tuple([id: params.id ?: 'protein'], file(params.sequence, checkIfExists: true), parents)))
    FHR_VERIFY_LINKS.out.report.view { meta, report -> "REPORT ${meta.id} ${report.name}" }
    FHR_VERIFY_LINKS.out.verified.view { meta, path -> "VERIFIED ${meta.id} ${path.name}" }
}
""")
        output = run(verify_script, work, ['--sequence', str(chain / 'protein.fhp.faa'), '--parents', str(chain / 'annotation.fhgff3.gff3')])
        check('REPORT protein protein.verify-links.txt' in output and 'VERIFIED protein protein.fhp.faa' in output, f'matching parent was not verified:\n{output}')
        report = next((work / 'work').glob('*/*/protein.verify-links.txt')).read_text()
        check('matched' in report and 'file identity only' in report, f'unexpected verify-links report:\n{report}')
        # Unavailable parents: the task succeeds, but "not checked" must never be
        # emitted on verified (a missing parent is not a match).
        output = run(verify_script, work, ['--id', 'unchecked', '--sequence', str(chain / 'protein.fhp.faa')])
        check('REPORT unchecked unchecked.verify-links.txt' in output and 'VERIFIED' not in output, f'unchecked parents were emitted on verified:\n{output}')
        report = next((work / 'work').glob('*/*/unchecked.verify-links.txt')).read_text()
        check('not checked' in report, f'unavailable parents were not reported as unchecked:\n{report}')
        run(verify_script, work, ['--sequence', str(chain / 'protein.fhp.faa'), '--parents', str(chain / 'other-annotation.fhgff3.gff3')], failure='Parent-link verification failed')
        required = work / 'verify-required'
        required.mkdir()
        (required / 'nextflow.config').write_text('nextflow.enable.dsl = 2\nprocess { withName: FHR_VERIFY_LINKS { ext.require_all = true } }\n')
        run(verify_script, required, ['--sequence', str(chain / 'protein.fhp.faa')], failure='Parent-link verification failed')
        lenient = work / 'verify-lenient'
        lenient.mkdir()
        (lenient / 'nextflow.config').write_text('nextflow.enable.dsl = 2\nprocess { withName: FHR_VERIFY_LINKS { ext.fail_on_mismatch = false } }\n')
        output = run(verify_script, lenient, ['--sequence', str(chain / 'protein.fhp.faa'), '--parents', str(chain / 'other-annotation.fhgff3.gff3')])
        check('REPORT protein protein.verify-links.txt' in output and 'VERIFIED' not in output, f'mismatching link was verified:\n{output}')
        output = run(verify_script, work, ['--id', 'annotation', '--sequence', str(chain / 'annotation.fhgff3.gff3'), '--parents', str(chain / 'genome.fhr.fasta')])
        check('VERIFIED annotation annotation.fhgff3.gff3' in output, f'genome-annotation link did not match:\n{output}')
        run(verify_script, work, ['--sequence', str(fhp / 'malformed-missing-proteome.fhp.faa')], failure='is incomplete')

        # The runnable example accepts protein FASTA with --sequence_format faa.
        output = work / 'protein-output'
        run(ROOT / 'main.nf', work, ['--metadata', str(ROOT / 'examples/protein-metadata.json'), '--sequence', str(ROOT / 'examples/protein.faa'), '--sequence_format', 'faa', '--outdir', str(output)])
        expected = ['protein-metadata/sequence/protein-metadata.faa', 'protein-metadata/sequence/protein-metadata.json', 'protein-metadata/sequence/protein-metadata.yaml']
        check(published(output) == expected, f'unexpected protein example outputs: {published(output)}')
        check((output / 'protein-metadata/sequence/protein-metadata.faa').read_bytes().startswith(b';~schema: https://w3id.org/fair-bioheaders/fhp/'), 'protein example is not an FHP header')

        # The runnable example also publishes verify-links reports per ID.
        output = work / 'verify-output'
        run(ROOT / 'main.nf', work, ['--verify_links', str(chain / 'protein.fhp.faa'), '--verify_parents', str(chain / 'annotation.fhgff3.gff3'), '--outdir', str(output)])
        check((output / 'protein.fhp/verify-links/protein.fhp.verify-links.txt').exists(), 'main.nf did not publish the verify-links report')
        run(ROOT / 'main.nf', work, ['--verify_links', str(chain / 'protein.fhp.faa'), '--verify_parents', str(chain / 'other-annotation.fhgff3.gff3'), '--outdir', str(work / 'verify-bad')], failure='Parent-link verification failed')
        check(not (work / 'verify-bad/protein.fhp').exists(), 'verify-links reports were published after a mismatch')
        # Omitting --verify_parents must reach the module as an empty list.
        output = work / 'verify-no-parents'
        run(ROOT / 'main.nf', work, ['--verify_links', str(chain / 'protein.fhp.faa'), '--outdir', str(output)])
        report = (output / 'protein.fhp/verify-links/protein.fhp.verify-links.txt').read_text()
        check('not checked' in report, f'omitted --verify_parents did not reach the module as an empty list:\n{report}')

        # Sample ids reach the pinned modules' shell commands as their output prefix, so
        # every entry point gates them with isSampleId before any task runs.
        pwned = 'x;touch PWNED_$(id -un);#'
        attach_bad_id = work / 'attach-bad-id.nf'
        attach_bad_id.write_text(attach + "workflow { FHR_ATTACH(Channel.of(tuple([id: params.bad], file(params.metadata), file(params.sequence), 'fasta'))) }\n")
        for bad in [pwned, '../escape']:
            run(attach_bad_id, work, ['--bad', bad, '--metadata', str(ROOT / 'examples/metadata.json'), '--sequence', str(ROOT / 'examples/genome.fasta')], failure="Invalid meta.id")
        check(not list(work.rglob('PWNED_*')), 'FHR_ATTACH ran a shell command embedded in meta.id')

        # The Dockstore workflow: both input branches check every id, and samplesheet ids
        # must be unique (two rows with one id used to publish over each other and report
        # success).
        dockstore = ROOT / 'workflows/fairbioheaders/main.nf'
        sheet_dir = work / 'dockstore'
        sheet_dir.mkdir()
        (sheet_dir / 'nextflow.config').write_text('nextflow.enable.dsl = 2\n')
        shutil.copy(ROOT / 'examples/metadata.json', sheet_dir / 'genome.json')
        shutil.copy(ROOT / 'examples/genome.fasta', sheet_dir / 'genome.fasta')
        for name, rows, message in [
            ('injection', [pwned], "Invalid sample id 'x;touch PWNED_"),
            ('traversal', ['../../../../ESCAPE'], "Invalid sample id '../../../../ESCAPE'"),
            ('duplicate', ['same', 'same'], 'duplicate sample id same (2 rows)'),
            ('combined-duplicate', ['genome', 'genome.combined'], 'duplicate sample id genome.combined (2 rows)'),
        ]:
            sheet = sheet_dir / f'{name}.csv'
            sheet.write_text('id,metadata,sequence\n' + ''.join(f'{row},genome.json,genome.fasta\n' for row in rows))
            run(dockstore, sheet_dir, ['--input', str(sheet), '--outdir', str(sheet_dir / f'{name}-out')], failure=message)
            check(not (sheet_dir / f'{name}-out').exists(), f'{name}: the Dockstore workflow published outputs')
        run(dockstore, sheet_dir, ['--metadata', 'genome.json', '--sequence', 'genome.fasta', '--id', 'a b'], failure="Invalid sample id 'a b' in --id")
        weird = sheet_dir / 'odd name.fasta'
        shutil.copy(ROOT / 'examples/genome.fasta', weird)
        run(dockstore, sheet_dir, ['--metadata', 'genome.json', '--sequence', str(weird)], failure="Invalid sample id 'odd name'")
        check(not list(work.rglob('PWNED_*')) and not list(work.rglob('ESCAPE*')) and not list(work.parent.glob('ESCAPE*')), 'the Dockstore workflow ran or wrote outside its work directory')
        # Valid input still runs end to end, and the default id that would collide with
        # the input name gets the .combined disambiguator.
        sheet = sheet_dir / 'valid.csv'
        sheet.write_text('id,metadata,sequence\nsample-1,genome.json,genome.fasta\ngenome,genome.json,genome.fasta\n')
        run(dockstore, sheet_dir, ['--input', str(sheet), '--outdir', str(sheet_dir / 'valid-out')])
        check(published(sheet_dir / 'valid-out') == ['combine/genome.combined.fasta', 'combine/sample-1.fasta', 'verify/genome.combined.verify.txt', 'verify/sample-1.verify.txt'],
              f'unexpected Dockstore outputs: {published(sheet_dir / "valid-out")}')

        # combineId mirrors the pinned combine's case-sensitive extension rule: only a
        # lower-case gz/bgz keeps two tokens, so genome.FA.GZ -> genome.GZ (no clash)
        # while genome.GZ with id genome would overwrite its input and is disambiguated.
        combine_id = work / 'combine-id.nf'
        combine_id.write_text("include { combineId } from '" + str(ROOT / 'modules/local/utils/main') + """'
workflow {
    def cases = [['genome', 'genome.fa.gz', 'genome.combined'], ['genome', 'genome.fasta.bgz', 'genome.combined'],
                 ['genome', 'genome.FA.GZ', 'genome'], ['genome', 'genome.GZ', 'genome.combined'],
                 ['genome', 'genome.fasta', 'genome.combined'], ['sample', 'genome.fasta', 'sample']]
    cases.each { id, name, expected ->
        def got = combineId(id, name)
        if (got != expected)
            error("combineId(${id}, ${name}) = ${got}, expected ${expected}")
    }
    println 'COMBINE-ID OK'
}
""")
        check('COMBINE-ID OK' in run(combine_id, work), 'combineId cases did not run')

        # The example: --metadata genome.json --sequence genome.fasta derives the id
        # genome, whose combine output genome.fasta would equal the input; the example
        # now applies the same .combined disambiguator as the Dockstore workflow.
        output = work / 'collision-output'
        run(ROOT / 'main.nf', work, ['--metadata', str(sheet_dir / 'genome.json'), '--sequence', str(sheet_dir / 'genome.fasta'), '--outdir', str(output)])
        check(published(output) == ['genome.combined/sequence/genome.combined.fasta', 'genome.combined/sequence/genome.combined.json', 'genome.combined/sequence/genome.combined.yaml'],
              f'unexpected example outputs for a colliding name: {published(output)}')

        # FHGFF3 workflow composition beyond parent fixtures (issue #7 / #35):
        # FHR_CREATE_JSON map -> FAIRBIOHEADERS_VALIDATE (JSON) -> FAIRBIOHEADERS_COMBINE
        # (plain and gzip GFF3) -> FAIRBIOHEADERS_VERIFY -> FAIRBIOHEADERS_CONVERT
        # (header extraction to json/yaml/gff3 and round trips back to json, plus
        # rejection of unsupported jsonld/html in toolkit 0.9.0) -> FHR_VERIFY_LINKS
        # -> GFF3_VALIDATE header-mode options (ext.header require/skip).
        combine = "include { FAIRBIOHEADERS_COMBINE } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/combine/main') + "'\n"
        fhgff3_fields = {
            'schema': 'https://w3id.org/fair-bioheaders/fhgff3/v0.4.0',
            'schemaVersion': '1.0',
            'annotation': 'Synthetic example annotation',
            'taxon': {'name': 'Homo sapiens', 'uri': 'https://identifiers.org/taxonomy:9606'},
            'version': '0.0.1',
            'metadataAuthor': [{'name': 'Adam Wright', 'uri': 'https://orcid.org/0000-0002-5719-4024'}],
            'dateCreated': '2026-10-21',
            'annotationProtocol': 'https://example.org/synthetic-annotation-protocol',
            'annotationSoftware': [{'name': 'Synthetic annotator', 'version': '1.0'}],
            'derivedFrom': [{'headerType': 'FHR', 'checksum': 'IHnspOEQ7lB6QJ5S+ZoWIFgWkOekkupMTD+O8pDY9IA=', 'relationship': 'annotates'}],
            'checksum': PLACEHOLDER,
        }
        fhgff3_json = work / 'fhgff3-meta.json'
        fhgff3_json.write_text(json.dumps(fhgff3_fields))
        fhgff3_compose = work / 'fhgff3-compose.nf'
        fhgff3_compose.write_text(
            create + combine + verify_header + convert
            + "include { FAIRBIOHEADERS_CONVERT as FHGFF3_BACK_JSON } from '" + str(ROOT / 'modules/nf-core/fairbioheaders/convert/main') + "'\n"
            + verify + """workflow {
    def fields = new groovy.json.JsonSlurper().parseText(file(params.metadata, checkIfExists: true).text)
    FHR_CREATE_JSON(Channel.of(tuple([id: 'fhgff3-created'], fields)))
    FAIRBIOHEADERS_COMBINE(FHR_CREATE_JSON.out.json.flatMap { meta, json ->
        [
            tuple([id: 'fhgff3-plain'], json, file(params.gff3, checkIfExists: true)),
            tuple([id: 'fhgff3-gz'], json, file(params.gff3_gz, checkIfExists: true))
        ]
    })
    FAIRBIOHEADERS_VERIFY(FAIRBIOHEADERS_COMBINE.out.sequence)
    def plain_headed = FAIRBIOHEADERS_COMBINE.out.sequence.filter { meta, path -> meta.id == 'fhgff3-plain' }
    def formats = ['json', 'yaml', 'gff3']
    FAIRBIOHEADERS_CONVERT(
        plain_headed.flatMap { meta, path ->
            formats.collect { fmt -> tuple([id: "fhgff3-extract-${fmt}".toString()], path) }
        },
        Channel.fromList(formats)
    )
    def non_json = FAIRBIOHEADERS_CONVERT.out.metadata.filter { meta, path -> meta.id != 'fhgff3-extract-json' }
    FHGFF3_BACK_JSON(
        non_json.map { meta, path -> tuple([id: "${meta.id}-back".toString()], path) },
        Channel.fromList(['json', 'json'])
    )
    FHR_VERIFY_LINKS(plain_headed.map { meta, path ->
        tuple([id: 'fhgff3-links'], path, [file(params.parent, checkIfExists: true)])
    })
    FHR_CREATE_JSON.out.json.view { meta, path -> "FHGFF3_CREATED ${meta.id} ${path.name}" }
    FAIRBIOHEADERS_COMBINE.out.sequence.view { meta, path -> "FHGFF3_COMBINED ${meta.id} ${path.name}" }
    FAIRBIOHEADERS_VERIFY.out.report.view { meta, path -> "FHGFF3_VERIFIED ${meta.id} ${path.name}" }
    FAIRBIOHEADERS_CONVERT.out.metadata.view { meta, path -> "FHGFF3_EXTRACTED ${meta.id} ${path.name}" }
    FHGFF3_BACK_JSON.out.metadata.view { meta, path -> "FHGFF3_ROUNDTRIP ${meta.id} ${path.name}" }
    FHR_VERIFY_LINKS.out.verified.view { meta, path -> "FHGFF3_LINKED ${meta.id} ${path.name}" }
}
""")
        output = run(
            fhgff3_compose,
            work,
            [
                '--metadata', str(fhgff3_json),
                '--gff3', str(ROOT / 'workflows/fairbioheaders/assets/test/no-header.gff3'),
                '--gff3_gz', str(gff3 / 'canonical-gene-gzip.gff3.gz'),
                '--parent', str(chain / 'genome.fhr.fasta'),
            ],
        )
        for marker in [
            'FHGFF3_CREATED fhgff3-created fhgff3-created.json',
            'FHGFF3_COMBINED fhgff3-plain fhgff3-plain.gff3',
            'FHGFF3_COMBINED fhgff3-gz fhgff3-gz.gff3.gz',
            'FHGFF3_VERIFIED fhgff3-plain fhgff3-plain.verify.txt',
            'FHGFF3_VERIFIED fhgff3-gz fhgff3-gz.verify.txt',
            'FHGFF3_EXTRACTED fhgff3-extract-json fhgff3-extract-json.json',
            'FHGFF3_EXTRACTED fhgff3-extract-yaml fhgff3-extract-yaml.yaml',
            'FHGFF3_EXTRACTED fhgff3-extract-gff3 fhgff3-extract-gff3.gff3',
            'FHGFF3_ROUNDTRIP fhgff3-extract-yaml-back fhgff3-extract-yaml-back.json',
            'FHGFF3_ROUNDTRIP fhgff3-extract-gff3-back fhgff3-extract-gff3-back.json',
            'FHGFF3_LINKED fhgff3-links fhgff3-plain.gff3',
        ]:
            check(marker in output, f'missing FHGFF3 workflow marker {marker!r}:\n{output}')
        extracted_fhgff3 = json.loads(next((work / 'work').glob('*/*/fhgff3-extract-json.json')).read_text())
        check(
            extracted_fhgff3['schema'].endswith('/fhgff3/v0.4.0')
            and extracted_fhgff3['checksum'] != PLACEHOLDER,
            f'FHGFF3 header extraction did not replace the placeholder checksum: {extracted_fhgff3}',
        )
        for back_name in ('fhgff3-extract-yaml-back.json', 'fhgff3-extract-gff3-back.json'):
            back_record = json.loads(next((work / 'work').glob(f'*/*/{back_name}')).read_text())
            check(back_record == extracted_fhgff3, f'{back_name} did not round-trip FHGFF3 metadata')
        header_only_gff3 = next((work / 'work').glob('*/*/fhgff3-extract-gff3.gff3')).read_text()
        check(
            header_only_gff3.startswith('##gff-version 3\n#~schema: https://w3id.org/fair-bioheaders/fhgff3/'),
            f'FHGFF3 --to gff3 output is not a GFF3 header block:\n{header_only_gff3}',
        )
        invalid_fhgff3 = dict(fhgff3_fields)
        invalid_fhgff3.pop('annotation')
        bad_fhgff3_source = work / 'fhgff3-missing.json'
        bad_fhgff3_source.write_text(json.dumps(invalid_fhgff3))
        run(ROOT / 'main.nf', work, ['--metadata', str(bad_fhgff3_source), '--outdir', str(work / 'fhgff3-missing')], failure='annotation')
        check(not (work / 'fhgff3-missing').exists(), 'fhgff3-missing: outputs were published after a validation failure')
        for unsupported_fmt in ('jsonld', 'html'):
            fhgff3_unsupported = work / f'fhgff3-convert-{unsupported_fmt}.nf'
            fhgff3_unsupported.write_text(pinned_convert + f"""workflow {{
    FAIRBIOHEADERS_CONVERT(Channel.of(tuple([id: 'fhgff3-bad'], file(params.metadata, checkIfExists: true))), Channel.value('{unsupported_fmt}'))
}}
""")
            run(fhgff3_unsupported, work, ['--metadata', str(fhgff3_json)], failure='JSON-LD and HTML microdata output are not available for FHGFF3 metadata yet')

        # GFF3_VALIDATE header-mode options (ext.header require/skip) on headed and
        # headerless GFF3 files.
        gff3_header_script = work / 'gff3-header.nf'
        gff3_header_script.write_text(module + """workflow {
    GFF3_VALIDATE(Channel.of(tuple([id: params.id], file(params.gff3, checkIfExists: true), [])))
    GFF3_VALIDATE.out.valid.view { meta, gff3 -> "VALID_HEADER ${meta.id} ${gff3.name}" }
    GFF3_VALIDATE.out.reports.view { meta, json, html -> "REPORT_HEADER ${meta.id} ${json.name}" }
}
""")
        for mode, rule in [('require', 'HDR-002'), ('skip', 'HDR-003')]:
            mode_dir = work / f'gff3-header-{mode}'
            mode_dir.mkdir()
            (mode_dir / 'nextflow.config').write_text(f"nextflow.enable.dsl = 2\nprocess {{ withName: GFF3_VALIDATE {{ ext.header = '{mode}' }} }}\n")
            output = run(gff3_header_script, mode_dir, ['--id', f'headed-{mode}', '--gff3', str(chain / 'annotation.fhgff3.gff3')])
            check(f'VALID_HEADER headed-{mode} annotation.fhgff3.gff3' in output, f'headed GFF3 failed under ext.header={mode}:\n{output}')
            report = json.loads(next((mode_dir / 'work').glob(f'*/*/headed-{mode}.gff3-validate.json')).read_text())
            check(report['valid'] and report['header_lines'] == 20 and [f['rule'] for f in report['findings']] == [rule],
                  f'unexpected GFF3 header report for ext.header={mode}: {report}')
        run(gff3_header_script, work / 'gff3-header-require', ['--id', 'no-header-require', '--gff3', str(gff3 / 'genes-with-genome.gff3')],
            failure='GFF3 validation failed for genes-with-genome.gff3')
        check(any('HDR-001' in path.read_text() for path in (work / 'gff3-header-require/work').glob('*/*/no-header-require.gff3-validate.json')),
              'ext.header=require on a headerless GFF3 did not record HDR-001')

        if args.converter_source:
            source = args.converter_source.resolve()
            before = snapshot(source)
            output = work / 'converter-output'
            run(ROOT / 'main.nf', work, ['--converter_source', str(source), '--outdir', str(output)])
            total, failures, errors, skipped = junit_totals(output / 'converter-tests/converter-tests.xml')
            check(total > 0 and failures + errors == 0, f'converter JUnit report: {total} tests, {failures} failures, {errors} errors')
            check((output / 'example/metadata/example.json').exists(), 'results were not published after passing tests')
            check(snapshot(source) == before, 'converter tests modified the supplied checkout')
            print(f'Converter wrapper: {total - failures - errors - skipped} passed, {skipped} skipped, {failures} failures, {errors} errors ({total} total).', flush=True)

            # A failing test publishes reports, withholds results and fails the run, also
            # when -resume follows an edit to a nested test file.
            mutable = work / 'converter-copy'
            shutil.copytree(source, mutable, ignore=shutil.ignore_patterns('.git'))
            run(ROOT / 'main.nf', work, ['--converter_source', str(mutable), '--outdir', str(work / 'copy-output')])
            with (mutable / 'tests/fhr_test.py').open('a') as tests:
                tests.write('\n\ndef test_injected_failure():\n    assert False\n')
            output = work / 'failing-output'
            run(ROOT / 'main.nf', work, ['-resume', '--converter_source', str(mutable), '--outdir', str(output)], failure='Converter tests failed')
            check(published(output) == ['converter-tests/converter-tests.log', 'converter-tests/converter-tests.xml'], f'unexpected outputs after failing tests: {published(output)}')
            total, failures, errors, skipped = junit_totals(output / 'converter-tests/converter-tests.xml')
            check(failures + errors == 1, f'expected one failing converter test, found {failures} failures, {errors} errors')
            check('test_injected_failure' in (output / 'converter-tests/converter-tests.log').read_text(), 'failure missing from published log')

            # 0.0.0 is never the installed version (a fixed future version stops mismatching
            # once the pin reaches it).
            pyproject = mutable / 'pyproject.toml'
            pyproject.write_text(re.sub(r'(?m)^version = "[^"]+"', 'version = "0.0.0"', pyproject.read_text(), count=1))
            run(ROOT / 'main.nf', work, ['--converter_source', str(mutable), '--outdir', str(work / 'mismatch')], failure="converter source version is '0.0.0'")
            check(not (work / 'mismatch' / 'example').exists(), 'results published with a mismatched converter checkout')
    print(f'PASS: {len(passed)} pipeline runs and rejection cases (round trips, exact bytes, JSON edge cases, per-file IDs, publication gates, GFF3 validation, protein FHP composition and parent-link verification).')


if __name__ == '__main__':
    try:
        main()
    except CheckFailed as error:
        sys.exit(f'FAIL: {error}')
