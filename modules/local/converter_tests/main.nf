// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { directoryDigest; quote; sampleId } from '../utils/main'

// Runs a converter checkout's pytest suite against the installed converter.
// The checkout's declared version must equal the installed fair-bioheaders
// version, so the tests match the code they test. It is copied into
// the task directory, so the input directory is never modified. This process
// succeeds even when tests fail so that the JUnit XML, log and pytest exit
// status are always emitted; FHR_CHECK_CONVERTER_TESTS then fails the run.
//
// The BioContainers fair-bioheaders image has no pytest, so this process runs in
// the repository's own image (label 'fhr', params.fhr_container, built from
// environment/), or in environment.yml with the conda profile.
process FHR_RUN_CONVERTER_TESTS {
    tag "${meta.id}"
    label 'fhr'

    conda "${moduleDir}/environment.yml"

    input:
    // source_digest covers the checkout's file contents: Nextflow hashes a
    // directory input by its own metadata only, so without it -resume would
    // reuse results after a nested test file is edited.
    tuple val(meta), path(converter_source, stageAs: 'source'), val(source_digest)

    output:
    tuple val(meta), path('converter-tests.xml'), path('converter-tests.log'), emit: reports
    tuple val(meta), env('FHR_TESTS_EXIT'), emit: status
    tuple val("${task.process}"), val('fair-bioheaders'), eval('bioheaders --version'), emit: versions_fairbioheaders, topic: versions

    script:
    sampleId(meta)
    """
    export PYTHONDONTWRITEBYTECODE=1
    python -I - ${quote(converter_source)} checkout <<'PY'
    import shutil, sys, tomllib
    from importlib.metadata import version as installed_version
    from pathlib import Path
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    for required in ('pyproject.toml', 'pytest.ini', 'tests'):
        if not (source / required).exists():
            sys.exit(f'converter source has no {required}: {source.resolve()}')
    project = tomllib.loads((source / 'pyproject.toml').read_text(encoding='utf-8'))
    version = project.get('project', {}).get('version') or project.get('tool', {}).get('poetry', {}).get('version')
    installed = installed_version('fair-bioheaders')
    if version != installed:
        sys.exit(f'converter source version is {version!r}; the installed converter is {installed}')
    shutil.copytree(source, target, symlinks=True, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', '*.pyc'))
    PY
    set +e
    (
        cd checkout
        # -P keeps the checkout off sys.path: tests import the installed converter.
        python -P -c 'import fhr; print("converter under test:", fhr.__version__, fhr.__file__)'
        python -P -m pytest -p no:cacheprovider --junitxml=../converter-tests.xml
    ) > converter-tests.log 2>&1
    FHR_TESTS_EXIT=\$?
    set -e
    if [ ! -s converter-tests.xml ]; then
        printf '<?xml version="1.0" encoding="utf-8"?>\\n<testsuites><testsuite name="pytest" tests="0" errors="1" failures="0"><testcase name="pytest"><error message="pytest exited with status %s without a JUnit report"/></testcase></testsuite></testsuites>\\n' "\$FHR_TESTS_EXIT" > converter-tests.xml
    fi
    """
}

process FHR_CHECK_CONVERTER_TESTS {
    tag "${meta.id}"

    input:
    tuple val(meta), val(exit_status)

    output:
    val(meta), emit: passed

    exec:
    if (exit_status.toString().trim() != '0')
        throw new IllegalStateException("Converter tests failed (pytest exit status ${exit_status}); see converter-tests.log and converter-tests.xml")
}

workflow FHR_CONVERTER_TESTS {
    take:
    sources // tuple(meta, converter_source_directory)

    main:
    FHR_RUN_CONVERTER_TESTS(sources.map { meta, source -> tuple(meta, source, directoryDigest(source)) })
    FHR_CHECK_CONVERTER_TESTS(FHR_RUN_CONVERTER_TESTS.out.status)

    emit:
    reports = FHR_RUN_CONVERTER_TESTS.out.reports // (meta, junit_xml, log), emitted whether or not tests pass
    passed = FHR_CHECK_CONVERTER_TESTS.out.passed // meta, only after pytest exits 0
    versions = FHR_RUN_CONVERTER_TESTS.out.versions_fairbioheaders
}
