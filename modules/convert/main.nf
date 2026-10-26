// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

include { fhrFormat; quote; sampleId } from '../utils/main'

process FHR_CONVERT {
    tag "${meta.id}: ${format}"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fair-bioheaders:0.8.2--pyhdfd78af_0':
        'quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(metadata, stageAs: 'input/*'), val(format)

    output:
    tuple val(meta), path("${meta.id}.fhr.${format}"), emit: converted
    tuple val("${task.process}"), val('fair-bioheaders'), eval('bioheaders --version'), emit: versions_fairbioheaders, topic: versions

    script:
    def id = sampleId(meta)
    def ext = fhrFormat(format, ['json', 'yaml', 'html', 'fasta', 'faa', 'gfa'])
    """
    fhr-convert ${quote(metadata)} ${quote("${id}.fhr.${ext}")}
    """
}
