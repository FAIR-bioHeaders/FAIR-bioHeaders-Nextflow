// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { FAIRBIOHEADERS_COMBINE } from '../../modules/nf-core/fairbioheaders/combine/main'
include { FAIRBIOHEADERS_VERIFY as CHECK_COMBINED } from '../../modules/nf-core/fairbioheaders/verify/main'
include { FHR_CONVERT as EXTRACT_JSON } from '../../modules/convert/main'
include { sequenceKindOf; sequenceType } from '../../modules/utils/main'

// Attaches metadata to a sequence file, verifies the result and extracts its JSON.
// FAIRBIOHEADERS_COMBINE takes the sequence type from the file extension and names
// the output by header type (ID.fhr.fa, ID.fhr.gfa, ID.fhp.faa); `kind` must agree
// with the extension ('fasta' and 'faa' are both FASTA, so FHP metadata may ride on
// .fa/.fasta and FHR metadata on .faa).
workflow FHR_ATTACH {
    take:
    records // tuple(meta, metadata, sequence, kind): kind is 'fasta', 'faa' or 'gfa'

    main:
    combine_input = records.map { meta, metadata, sequence, kind ->
        if (!(kind in ['fasta', 'faa', 'gfa']))
            throw new IllegalArgumentException("Unsupported format '${kind}'; expected fasta, faa, gfa")
        def actual = sequenceKindOf(sequence)
        if (sequenceType(actual, ['fasta', 'faa', 'gfa', 'gff3']) != sequenceType(kind))
            throw new IllegalArgumentException("Sequence format '${kind}' does not match the extension of ${sequence.name} (${actual}); rename the file or change the format")
        tuple(meta, metadata, sequence)
    }
    FAIRBIOHEADERS_COMBINE(combine_input)
    CHECK_COMBINED(FAIRBIOHEADERS_COMBINE.out.sequence)
    // Only verified files continue: the verify task fails otherwise, and the
    // report carries the same meta, which is unique per record.
    verified = FAIRBIOHEADERS_COMBINE.out.sequence
        .join(CHECK_COMBINED.out.report, failOnDuplicate: true, failOnMismatch: true)
        .map { meta, sequence, _report -> tuple(meta, sequence) }
    EXTRACT_JSON(verified.map { meta, sequence -> tuple(meta, sequence, 'json') })

    emit:
    sequence = verified
    json = EXTRACT_JSON.out.converted
    reports = CHECK_COMBINED.out.report
    versions = FAIRBIOHEADERS_COMBINE.out.versions_fairbioheaders.mix(CHECK_COMBINED.out.versions_fairbioheaders, EXTRACT_JSON.out.versions_fairbioheaders)
}
