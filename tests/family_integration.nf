// SPDX-License-Identifier: MPL-2.0
// Integration orchestration only; the installed toolkit owns all validation.
include { FHR_CREATE_JSON } from '../modules/local/create_json/main'
include { FAIRBIOHEADERS_VERIFY as VERIFY_SOURCE } from '../modules/nf-core/fairbioheaders/verify/main'
include { FAIRBIOHEADERS_CONVERT as TO_FORMAT } from '../modules/nf-core/fairbioheaders/convert/main'
include { FAIRBIOHEADERS_CONVERT as BACK_JSON } from '../modules/nf-core/fairbioheaders/convert/main'
include { FHR_ATTACH } from '../subworkflows/attach/main'
include { FHR_STRIP } from '../modules/local/strip/main'
include { FHR_VERIFY_LINKS } from '../modules/local/verify_links/main'

process ASSERT_METADATA {
    input:
    tuple val(meta), val(metadata)
    output:
    path "${meta.id}.metadata.ok"
    exec:
    assert new groovy.json.JsonSlurper().parseText(metadata.text) == meta.expected
    task.workDir.resolve("${meta.id}.metadata.ok").text = 'OK\n'
}
process ASSERT_PAYLOAD {
    input:
    tuple val(meta), val(sequence)
    output:
    path "${meta.id}.payload.ok"
    exec:
    assert java.util.Arrays.equals(sequence.bytes, file(params.expected_payload ?: params.payload).bytes)
    task.workDir.resolve("${meta.id}.payload.ok").text = 'OK\n'
}
workflow {
    main:
    def metadata = file(params.metadata, checkIfExists: true)
    def fields = new groovy.json.JsonSlurper().parseText(metadata.text)
    def original = file(params.source, checkIfExists: true)
    def payload = file(params.payload, checkIfExists: true)
    def formats = params.formats.tokenize(',')
    if (!formats || !formats.every { it in ['json', 'yaml', 'html', 'jsonld', 'fasta', 'gff3', 'gfa'] })
        throw new IllegalArgumentException('Unsupported acceptance format')
    VERIFY_SOURCE(channel.of(tuple([id: 'source'], original)))
    FHR_CREATE_JSON(channel.of(tuple([id: 'created'], fields)))
    TO_FORMAT(FHR_CREATE_JSON.out.json.flatMap { meta, json ->
        formats.collect { fmt -> tuple([id: "to-${fmt}", expected: fields], json) }
    }, channel.fromList(formats))
    BACK_JSON(TO_FORMAT.out.metadata.map { meta, converted ->
        tuple([id: "${meta.id}-back", expected: fields], converted)
    }, channel.fromList(formats.collect { 'json' }))
    ASSERT_METADATA(BACK_JSON.out.metadata)
    FHR_ATTACH(FHR_CREATE_JSON.out.json.map { meta, json ->
        tuple([id: 'attached', family: params.family], json, payload, params.kind)
    })
    FHR_STRIP(FHR_ATTACH.out.sequence.map { meta, sequence -> tuple(meta, sequence, params.kind) })
    ASSERT_PAYLOAD(FHR_STRIP.out.stripped)
    FHR_VERIFY_LINKS(channel.of(tuple([id: 'source-links'], original,
        params.parent ? [file(params.parent, checkIfExists: true)] : [])))
    // All assertion and verification branches must complete before normal results
    // are published; a schema/checksum/model/round-trip failure withholds outputs.
    gate = ASSERT_METADATA.out.collect().combine(ASSERT_PAYLOAD.out.collect())
        .combine(VERIFY_SOURCE.out.report.collect()).combine(FHR_VERIFY_LINKS.out.report.collect()).map { true }
    results = FHR_ATTACH.out.sequence.mix(FHR_ATTACH.out.json, BACK_JSON.out.metadata)
        .combine(gate).map { meta, artifact, _gate -> tuple(meta, artifact) }
    publish:
    accepted = results
}
output {
    accepted {
        path { meta, artifact -> artifact >> "${meta.id}/${artifact.name}" }
    }
}
