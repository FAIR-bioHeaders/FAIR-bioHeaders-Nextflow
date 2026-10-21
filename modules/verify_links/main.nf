// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { bioheadersVersionCheck; bioheadersVersionReport; failOnMismatch; quote; requireAllParents; sampleId; sequenceKindOf; sequenceType } from '../utils/main'

// Checks the parent files a protein (FHP) or genome (FHR) header records in
// derivedFrom against candidate files, using the pinned toolkit's
// `bioheaders verify-links`. The toolkit owns every rule; this module only
// composes it, preserves meta, quotes staged paths and constrains the report
// name. A match proves file identity by checksum, never biological correctness.
//
// The report is always emitted. `verified` is emitted only when the recorded
// parents matched (or none were recorded). Exit status 1 (unreadable or invalid
// input, or an invalid parent) always fails; exit status 3 (a recorded parent
// did not match, or with ext.require_all could not be checked) fails unless
// ext.fail_on_mismatch is false, in which case the report is emitted and the
// input is omitted from `verified`.
process FHR_VERIFY_LINKS {
    tag "${meta.id}"
    label 'fhr'

    input:
    tuple val(meta), path(sequence, stageAs: 'input/*'), path(parents, stageAs: 'parents/*')

    output:
    tuple val(meta), path("${meta.id}.verify-links.txt"), emit: report
    // The verified input is linked into verified/ by the script; only a match is
    // emitted, so a mismatching file never reaches `verified`.
    tuple val(meta), path("verified/*"), emit: verified, optional: true
    tuple val(meta), path('versions.yml'), emit: versions

    script:
    def id = sampleId(meta)
    def type = sequenceType(sequenceKindOf(sequence), ['fasta', 'faa', 'gfa', 'gff3'])
    def requireAll = requireAllParents(task.ext)
    def failOnMismatch = failOnMismatch(task.ext)
    def input = quote(sequence)
    def parentArgs = (parents instanceof Collection ? parents : [parents])
        .findAll { parent -> parent }
        .collect { parent -> quote(parent) }
        .join(' ')
    def report = quote("${id}.verify-links.txt")
    def name = quote(sequence.name)
    """
    ${bioheadersVersionCheck()}
    set +e
    bioheaders verify-links --type ${type} ${requireAll ? '--require-all' : ''} ${input} ${parentArgs} > ${report}
    status=\$?
    set -e
    if [ "\$status" -ne 0 ] && [ "\$status" -ne 3 ]; then
        printf 'Parent-link verification of %s is incomplete (bioheaders verify-links exit status %s): the input or a parent file is unreadable or invalid; see the message above\\n' ${name} "\$status" >&2
        exit 2
    fi
    if [ "\$status" -eq 3 ]; then
        cat ${report} >&2
        if ${failOnMismatch}; then
            printf 'Parent-link verification failed for %s: a recorded parent did not match a supplied file (report: %s). Set ext.fail_on_mismatch = false to emit the report and continue.\\n' ${name} ${report} >&2
            exit 1
        fi
    else
        mkdir -p verified
        ln -s ../${input} verified/
    fi
    ${bioheadersVersionReport()}
    """
}
