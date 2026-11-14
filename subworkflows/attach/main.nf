// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { FAIRBIOHEADERS_COMBINE }                 from '../../modules/nf-core/fairbioheaders/combine/main'
include { FAIRBIOHEADERS_VERIFY as CHECK_COMBINED } from '../../modules/nf-core/fairbioheaders/verify/main'
include { FAIRBIOHEADERS_CONVERT as EXTRACT_JSON }  from '../../modules/nf-core/fairbioheaders/convert/main'
include { sequenceKindOf; sequenceType }           from '../../modules/utils/main'

// Attaches metadata to a sequence file, verifies the result and extracts its JSON.
//
// As of issue #29 option (a) this composes the pinned **upstream** nf-core modules
// (modules/nf-core/fairbioheaders/{combine,convert,verify}) directly; the repository's
// header-family compatibility modules (FHR_COMBINE / FHR_CONVERT) are retired, and the
// repository's own verify implementation was retired in #29 slice 4 under the same
// include path (tuples and report names unchanged). The
// outputs therefore follow the upstream naming convention, not the old family names:
//   sequence : <id>.<input extension>   (genome.fasta -> ID.fasta, .fa -> ID.fa,
//                                        protein.faa -> ID.faa, assembly.gfa -> ID.gfa,
//                                        annotation.gff3 -> ID.gff3), .gz kept for
//                                        compressed input.
//   json     : <id>.json  (the header extracted from the attached file).
// The protein/genome distinction is NOT carried by the output name any more; it rides
// on `meta` (and on the header inside the file). `kind` must agree with the input
// extension ('fasta' and 'faa' are both FASTA, so FHP metadata may ride on .fa/.fasta
// and FHR metadata on .faa); it is validated here, not encoded in the output name.
//
// The upstream convert module defaults its output to <id>_converted.<format>; the
// extracted sidecar is published as <id>.json by the importing project configuring
//   process { withName: FAIRBIOHEADERS_CONVERT { ext.prefix = { meta.id } } }
// (the upstream module's documented mechanism; this repository sets it in
// nextflow.config and the harness project). The upstream combine defaults its prefix
// to meta.id already, so it needs no configuration. When meta.id + the sequence
// extension could equal the staged sequence file name, the upstream combine/convert
// refuse to overwrite their input (meta.yml documents the failure) — choose a
// non-colliding id or set ext.prefix yourself.
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
    // Upstream convert takes two input rows: the (meta, file) channel and a channel
    // of --to format values. The attached file is <id>.<ext>; extracting to <id>.json
    // (ext.prefix = meta.id) never equals it.
    EXTRACT_JSON(verified, Channel.value('json'))

    emit:
    sequence = verified
    json = EXTRACT_JSON.out.metadata
    reports = CHECK_COMBINED.out.report
    versions = FAIRBIOHEADERS_COMBINE.out.versions_fairbioheaders.mix(CHECK_COMBINED.out.versions_fairbioheaders, EXTRACT_JSON.out.versions_fairbioheaders)
}
