// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { fhrFormat; quote; sampleId; sequenceType } from '../utils/main'

process FHR_STRIP {
    tag "${meta.id}: ${kind}"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fair-bioheaders:0.8.2--pyhdfd78af_0':
        'quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(sequence, stageAs: 'input/*'), val(kind)

    output:
    tuple val(meta), path("${meta.id}.stripped.${kind}"), emit: stripped
    tuple val("${task.process}"), val('fair-bioheaders'), eval('bioheaders --version'), emit: versions_fairbioheaders, topic: versions

    script:
    def id = sampleId(meta)
    def type = fhrFormat(kind, ['fasta', 'faa', 'gfa'])
    """
    fhr-${sequenceType(type, ['fasta', 'faa', 'gfa'])}-strip ${quote(sequence)} ${quote("${id}.stripped.${type}")}
    """
}
