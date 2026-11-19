#!/usr/bin/env nextflow
// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Adds FAIR-bioHeaders metadata to FASTA, protein FASTA, GFA or GFF3 files and
// verifies the result: FAIRBIOHEADERS_COMBINE (the pinned upstream nf-core
// module) writes the headed file with its checksum, then FAIRBIOHEADERS_VERIFY
// (also the pinned upstream nf-core module since issue #29 slice 4) checks the
// header against the schema and the checksum.
//
// Issue #29 option (a): this workflow now calls the pinned upstream combine
// directly (the repository's header-family compatibility module modules/combine
// is retired). The upstream module names its output after the input's extension
// — <id>.fasta / <id>.fa / <id>.faa / <id>.gfa / <id>.gff3, with .gz kept for
// compressed input — instead of the old <id>.fhr.fa / <id>.fhp.faa names, and it
// keeps the header family only inside the file (the metadata's schema URL), not
// in the file name. See docs/module-migration.md.
// See README.md in this directory for the parameters.

include { FAIRBIOHEADERS_COMBINE } from '../../modules/nf-core/fairbioheaders/combine/main'
include { FAIRBIOHEADERS_VERIFY    } from '../../modules/nf-core/fairbioheaders/verify/main'
include { isSampleId; combineId    } from '../../modules/local/utils/main'

// A samplesheet path: a URL or absolute path as is, otherwise relative to the sheet.
// The sheet itself may be a URL, such as the raw GitHub URL of the test samplesheet.
def sheetFile(sheet, String path) {
    if (path.contains('://') || path.startsWith('/')) {
        return file(path, checkIfExists: true)
    }
    def resolved = sheet.parent.resolve(path).normalize()
    if (!resolved.exists()) {
        error("Samplesheet ${sheet.toUriString()}: no such file: ${resolved.toUriString()}")
    }
    return resolved
}

// The sample id becomes the pinned modules' output prefix, which they interpolate
// into shell commands, so it must be a plain file-name token. Same rule as the
// example (main.nf) and FHR_ATTACH: letters, digits, dot, underscore or hyphen,
// starting with a letter or digit. Returns a problem message (or null) rather than
// throwing, so the caller's error() reaches the user unwrapped.
def sampleIdProblem(Object id, String source) {
    return isSampleId(id) ? null : "Invalid sample id '${id}' in ${source}: an id must contain only letters, digits, dot, underscore or hyphen, starting with a letter or digit"
}

workflow {
    main:
    def input
    if (params.input) {
        // Samplesheet: CSV with the columns id,metadata,sequence. Relative paths are
        // relative to the samplesheet's directory. Every id is checked, and ids must
        // be unique (two rows with one id would publish over each other), before any
        // task runs.
        def sheet = file(params.input, checkIfExists: true)
        input = channel.fromPath(sheet)
            .splitCsv(header: true, strip: true)
            .toList()
            .flatMap { rows ->
                rows.each { row ->
                    if (!row.id || !row.metadata || !row.sequence) {
                        error("Samplesheet ${params.input}: each row needs id, metadata and sequence: ${row}")
                    }
                    def problem = sampleIdProblem(row.id, "samplesheet ${params.input}")
                    if (problem) {
                        error(problem)
                    }
                }
                def records = rows.collect { row ->
                    def sequence = sheetFile(sheet, row.sequence)
                    [[id: combineId(row.id, sequence.name)], sheetFile(sheet, row.metadata), sequence]
                }
                // Checked on the final ids, after the collision guard may have added .combined.
                def duplicates = records.groupBy { record -> record[0].id }.findAll { id, group -> group.size() > 1 }
                if (duplicates) {
                    error("Samplesheet ${params.input}: duplicate sample id " + duplicates.collect { id, group -> "${id} (${group.size()} rows)" }.join('; '))
                }
                records
            }
    } else if (params.metadata && params.sequence) {
        def sequence = file(params.sequence, checkIfExists: true)
        def base = sequence.name.replaceFirst(/(\.(fa|fasta|fna|faa|gfa|gff3?))?(\.b?gz)?$/, '')
        def id = params.id ? params.id.toString() : base
        def problem = sampleIdProblem(id, params.id ? '--id' : "the name of ${sequence.name} (give --id)")
        if (problem) {
            error(problem)
        }
        input = channel.of([[id: combineId(id, sequence.name)], file(params.metadata, checkIfExists: true), sequence])
    } else {
        error("Give --input samplesheet.csv, or --metadata and --sequence (see README.md).")
    }

    FAIRBIOHEADERS_COMBINE(input)
    FAIRBIOHEADERS_VERIFY(FAIRBIOHEADERS_COMBINE.out.sequence)
}
