#!/usr/bin/env python3
"""Exercise native DSL2 composition with a named installed released toolkit.

No schema rules are implemented here: JSON equality, byte equality, process
status and explicit report assertions are the integration oracles. Existing
fixture bytes/provenance are checked before use; transformations use the CLI.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/five-types'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nextflow', required=True)
    parser.add_argument('--bioheaders', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected-toolkit', default='0.13.0')
    parser.add_argument('--preparation-only', action='store_true')
    parser.add_argument('--wheel', type=Path)
    parser.add_argument('--wheel-sha256')
    parser.add_argument('--artifact-url')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PATH'] = str(Path(args.bioheaders).resolve().parent) + os.pathsep + env['PATH']
    env['BIOHEADERS_EXPERIMENTAL_FHGM'] = '1'
    env['BIOHEADERS_FHGM_CONTRACT'] = '0.1'
    env.pop('BIOHEADERS_EXPERIMENTAL_FHT', None)
    env['NXF_ANSI_LOG'] = 'false'
    version = subprocess.check_output([args.bioheaders, '--version'], text=True, env=env).strip()
    assert version == args.expected_toolkit, version
    if not args.preparation_only:
        assert args.wheel and args.wheel_sha256 and args.artifact_url, 'actual release artifact proof is required'
    proof_code = "import bioheaders,importlib.metadata as m,json,pathlib; d=m.distribution('fair-bioheaders'); print(json.dumps({'location':str(pathlib.Path(bioheaders.__file__).parent),'version':d.version,'direct_url':json.loads(d.read_text('direct_url.json') or '{}')}))"
    installed = json.loads(subprocess.check_output([str(Path(args.bioheaders).resolve().parent/'python'), '-c', proof_code], text=True, env=env, cwd=out))
    assert installed['version'] == version
    assert not installed['direct_url'].get('dir_info', {}).get('editable'), installed
    artifact = None
    if args.wheel:
        wheel = args.wheel.resolve()
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if args.wheel_sha256:
            assert digest == args.wheel_sha256
        package = Path(installed['location'])
        with zipfile.ZipFile(wheel) as archive:
            package_files = [n for n in archive.namelist() if n.startswith('bioheaders/') and not n.endswith('/')]
            assert package_files
            for name in package_files:
                assert archive.read(name) == (package.parent/name).read_bytes(), name
        artifact = {'url': args.artifact_url, 'wheel': str(wheel), 'sha256': digest, 'packageFilesByteCompared': len(package_files)}
    provenance = json.loads((FIX / 'provenance.json').read_text())
    for row in provenance['copied']:
        data = (FIX / row['file']).read_bytes()
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    rows = []

    def command(argv, log, expected=0):
        run = subprocess.run(list(map(str, argv)), cwd=out, env=env, capture_output=True)
        log.write_bytes(run.stdout + run.stderr)
        assert run.returncode == expected, (argv, run.returncode, log)
        return run

    families = [('FHR', 'fhr.fasta', 'fasta', 'json,yaml,html,fasta,gfa,jsonld'),
                ('FHP', 'fhp.fasta', 'fasta', 'json,yaml,html,fasta'),
                ('FHGFF3', 'fhgff3.gff3', 'gff3', 'json,yaml,html,gff3'),
                ('FHT', 'fht.fasta', 'fasta', 'json,yaml,html,fasta'),
                ('FHGM', 'fhgm.gff3', 'gff3', 'json,yaml,gff3')]
    def exercise(family, name, kind, formats, label=None, compressed=False, parent=None):
        label = label or family
        prepared = out / label
        prepared.mkdir(exist_ok=True)
        metadata = prepared / 'input.json'
        payload = prepared / ('payload.' + kind)
        source = FIX / name
        if compressed:
            source = prepared / ('source.' + kind + '.gz')
            source.write_bytes(gzip.compress((FIX / name).read_bytes(), mtime=0))
        command([args.bioheaders, 'convert', source, metadata, '--to', 'json'], prepared / 'extract.log')
        command([args.bioheaders, 'strip', source, payload], prepared / 'strip.log')
        expected_payload = payload
        if compressed:
            payload = prepared / ('payload.' + kind + '.gz')
            payload.write_bytes(gzip.compress(expected_payload.read_bytes(), mtime=0))
        results = prepared / 'results'
        argv = [args.nextflow, 'run', ROOT/'tests/family_integration.nf', '-c', ROOT/'tests/family_integration.config',
                 '-w', prepared/'work', '--metadata', metadata, '--source', source, '--payload', payload,
                 '--kind', kind, '--family', family, '--formats', formats, '--expected_payload', expected_payload, '--outdir', results]
        if parent:
            argv += ['--parent', FIX / parent]
        command(argv, prepared/'nextflow.log')
        artifacts = sorted(str(p.relative_to(results)) for p in results.rglob('*') if p.is_file())
        assert len(artifacts) == len(formats.split(',')) + 2, (family, artifacts)
        reports = list((prepared/'work').rglob('source.verify.txt'))
        assert len(reports) == 1 and 'Checksum verified.' in reports[0].read_text(), label
        if family == 'FHGM':
            report = reports[0].read_text()
            assert 'FHGM model 0.1: model result: pass' in report
            assert 'released FHGFF3 header: pass' in report and 'file checksum: verify' in report
            assert 'GFF3 feature syntax/biology: not-run' in report
        if parent:
            link_reports = list((prepared/'work').rglob('source-links.verify-links.txt'))
            assert len(link_reports) == 1
            assert 'not checked' not in link_reports[0].read_text().lower()
        rows.append({'case': label, 'family': family, 'kind': kind, 'compressed': compressed, 'formats': formats.split(','), 'exit': 0, 'published': artifacts})
        return metadata, expected_payload

    prepared_inputs = {}
    for family, name, kind, formats in families:
        prepared_inputs[family] = exercise(family, name, kind, formats)
    exercise('FHT', 'fht.fasta', 'fasta', 'json,yaml,html,fasta', label='FHT-gzip', compressed=True)
    exercise('FHGM', 'fhgm.gff3', 'gff3', 'json,yaml,gff3', label='FHGM-gzip', compressed=True)
    exercise('FHT', 'fht-parent.fasta', 'fasta', 'json,yaml,html,fasta', label='FHT-parent', parent='parent.fasta')

    for family, source_name, kind in [('FHT', 'fht-reject.fasta', 'fasta'), ('FHGM', 'fhgm-reject.gff3', 'gff3')]:
        label = family + '-reject'
        prepared = out / label
        prepared.mkdir(exist_ok=True)
        metadata, payload = prepared_inputs[family]
        results = prepared / 'results'
        argv = [args.nextflow, 'run', ROOT/'tests/family_integration.nf', '-c', ROOT/'tests/family_integration.config',
                '-w', prepared/'work', '--metadata', metadata, '--source', FIX/source_name, '--payload', payload,
                '--kind', kind, '--family', family, '--formats', 'json,yaml', '--outdir', results]
        run = subprocess.run(list(map(str, argv)), cwd=out, env=env, capture_output=True)
        (prepared/'nextflow.log').write_bytes(run.stdout + run.stderr)
        assert run.returncode != 0, label
        diagnostic = run.stdout + run.stderr
        for report in (prepared/'work').rglob('source.verify.txt'):
            diagnostic += report.read_bytes()
        marker = b'C1: completeness component counts must sum to total' if family == 'FHT' else b'model result: reject (K1)'
        assert marker in diagnostic, (label, 'intended rejection diagnostic missing')
        assert not [p for p in results.rglob('*') if p.is_file()], label
        rows.append({'case': label, 'family': family, 'exit': run.returncode, 'expectedRejection': True, 'published': []})
    receipt = {'toolkit': version, 'nextflow': subprocess.check_output([args.nextflow, '-version'], text=True, env=env).strip(),
               'preparationOnly': args.preparation_only, 'installed': installed, 'artifact': artifact, 'fixtureSource': provenance, 'cases': rows,
               'limits': ['Native host execution; upstream 0.9.0 conda/container pins are not promoted by this receipt.',
                          'FHGM is a native model in FHGFF3, not a fifth header type; model checks are explicitly enabled.',
                          'GFF3 feature/biology validation is separate and not claimed by model checks.']}
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'toolkit': version, 'types': 5, 'cases': len(rows), 'preparationOnly': args.preparation_only}))


if __name__ == '__main__':
    main()
