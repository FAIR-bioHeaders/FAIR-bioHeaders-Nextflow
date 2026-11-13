// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { FHR_CREATE_JSON } from '../modules/create_json/main'
include { FAIRBIOHEADERS_CONVERT as TO_FORMAT } from '../modules/nf-core/fairbioheaders/convert/main'
include { FAIRBIOHEADERS_CONVERT as BACK_JSON } from '../modules/nf-core/fairbioheaders/convert/main'
include { FHR_ATTACH } from '../subworkflows/attach/main'
include { FHR_STRIP } from '../modules/strip/main'

process ASSERT_ROUNDTRIP {
    input:
    tuple val(meta), val(json)
    output:
    path "${meta.id}.ok"
    exec:
    def actual = new groovy.json.JsonSlurper().parseText(json.text)
    assert actual == meta.expected
    task.workDir.resolve("${meta.id}.ok").text = 'OK\n'
}
process ASSERT_BYTES {
    input:
    tuple val(meta), val(sequence)
    output:
    path "${meta.id}.ok"
    exec:
    assert java.util.Arrays.equals(sequence.bytes, file(meta.original).bytes)
    task.workDir.resolve("${meta.id}.ok").text = 'OK\n'
}
workflow {
    def fields = new groovy.json.JsonSlurper().parseText(file(params.fixture).text)
    def formats = ['json', 'yaml', 'html', 'fasta', 'gfa']
    FHR_CREATE_JSON(Channel.of(tuple([id: 'rich'], fields)))
    // Upstream convert takes two input rows: the (meta, file) channel and a channel of
    // --to format values, zipped positionally. Each format round-trips through JSON.
    TO_FORMAT(
        FHR_CREATE_JSON.out.json.flatMap { meta, json ->
            formats.collect { fmt -> tuple([id: fmt, expected: fields], json) }
        },
        Channel.fromList(formats)
    )
    BACK_JSON(
        TO_FORMAT.out.metadata.map { meta, converted -> tuple([id: "${meta.id}-back", expected: meta.expected], converted) },
        Channel.fromList(formats.collect { 'json' })
    )
    ASSERT_ROUNDTRIP(BACK_JSON.out.metadata)
    FHR_ATTACH(FHR_CREATE_JSON.out.json.flatMap { meta, json ->
        ['fasta', 'gfa'].collect { kind ->
            def original = file("${params.fixtures}/${kind == 'fasta' ? 'genome.fasta' : 'assembly.gfa'}")
            tuple([id: "attached-${kind}", original: original.toString()], json, original, kind)
        }
    })
    FHR_STRIP(FHR_ATTACH.out.sequence.map { meta, sequence -> tuple(meta, sequence, sequence.name.endsWith('.gfa') ? 'gfa' : 'fasta') })
    ASSERT_BYTES(FHR_STRIP.out.stripped)
}
