#!/usr/bin/env nextflow
// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Adds FAIR-bioHeaders metadata to FASTA, protein FASTA, GFA or GFF3 files and
// verifies the result: FAIRBIOHEADERS_COMBINE (the pinned upstream nf-core
// module) writes the headed file with its checksum, then FAIRBIOHEADERS_VERIFY
// checks the header against the schema and the checksum.
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

// The extension the upstream combine keeps for the given sequence file (its last
// name token, or last two for .gz/.bgz so compression is preserved).
def combineExtension(String name) {
    def tokens = name.tokenize('.')
    def lower = name.toLowerCase()
    return (lower.endsWith('.gz') || lower.endsWith('.bgz')) ? tokens.takeRight(2).join('.') : tokens.takeRight(1)[0]
}

// The combine output is <id>.<extension>; the toolkit refuses to overwrite the
// staged input. When that name would equal the sequence file's own name (which is
// exactly what the default id derived from the file name produces), add the prefix
// disambiguator the upstream module documents. (Issue #29 option (a) collision guard.)
def combineId(String id, String sequenceName) {
    if (!id) {
        return id
    }
    return ("${id}.${combineExtension(sequenceName)}" == sequenceName) ? "${id}.combined" : id
}

workflow {
    main:
    def input
    if (params.input) {
        // Samplesheet: CSV with the columns id,metadata,sequence. Relative paths are
        // relative to the samplesheet's directory.
        def sheet = file(params.input, checkIfExists: true)
        input = channel.fromPath(sheet)
            .splitCsv(header: true, strip: true)
            .map { row ->
                if (!row.id || !row.metadata || !row.sequence) {
                    error("Samplesheet ${params.input}: each row needs id, metadata and sequence: ${row}")
                }
                def sequence = sheetFile(sheet, row.sequence)
                [[id: combineId(row.id, sequence.name)], sheetFile(sheet, row.metadata), sequence]
            }
    } else if (params.metadata && params.sequence) {
        def sequence = file(params.sequence, checkIfExists: true)
        def base = sequence.name.replaceFirst(/(\.(fa|fasta|fna|faa|gfa|gff3?))?(\.b?gz)?$/, '')
        def id = combineId(params.id ?: base, sequence.name)
        input = channel.of([[id: id], file(params.metadata, checkIfExists: true), sequence])
    } else {
        error("Give --input samplesheet.csv, or --metadata and --sequence (see README.md).")
    }

    FAIRBIOHEADERS_COMBINE(input)
    FAIRBIOHEADERS_VERIFY(FAIRBIOHEADERS_COMBINE.out.sequence)
}
