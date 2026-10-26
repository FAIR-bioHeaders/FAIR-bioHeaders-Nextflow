// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { metadataJson; sampleId } from '../utils/main'

include { FAIRBIOHEADERS_VALIDATE as VALIDATE_CREATED_JSON } from '../nf-core/fairbioheaders/validate/main'

process FHR_WRITE_JSON {
    tag "${meta.id}"

    input:
    tuple val(meta), val(fields)

    output:
    tuple val(meta), path("${meta.id}.fhr.json"), emit: json

    exec:
    def id = sampleId(meta)
    if (!(fields instanceof Map))
        throw new IllegalArgumentException('FHR fields must be a map')
    task.workDir.resolve("${id}.fhr.json").text = metadataJson(fields)
}

workflow FHR_CREATE_JSON {
    take:
    records // tuple(meta, fields): all required and optional FHR fields

    main:
    FHR_WRITE_JSON(records)
    VALIDATE_CREATED_JSON(FHR_WRITE_JSON.out.json)
    // Only JSON that validated is emitted: the validation task fails otherwise, and
    // the report carries the same meta, which is unique per record.
    validated = FHR_WRITE_JSON.out.json
        .join(VALIDATE_CREATED_JSON.out.report, failOnDuplicate: true, failOnMismatch: true)
        .map { meta, json, _report -> tuple(meta, json) }

    emit:
    json = validated
    reports = VALIDATE_CREATED_JSON.out.report
    versions = VALIDATE_CREATED_JSON.out.versions_fairbioheaders
}
