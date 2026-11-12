// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Repository-owned compatibility module (issue #29, slice 2a). The pinned upstream
// nf-core fairbioheaders/convert now lives at modules/nf-core/fairbioheaders/convert
// (revision 4dc3bc5477); it takes the output format as a second input row, names the
// output PREFIX.<format> with PREFIX defaulting to <meta.id>_converted, and can emit
// only the toolkit's --to tokens. This process preserves the suite's documented channel
// contract instead: one (meta, metadata, output_format) tuple, the ID.fhr.<format> name
// the example, FHR_ATTACH and the harness markers publish, the `faa` format (which is
// not a --to token: `bioheaders convert --to faa` exits 2) and a format whitelist that
// rejects an unusable value before the task is submitted. With
// `ext.prefix = { "${meta.id}.fhr" }` the pinned module reproduces these bytes for
// json/yaml/html and header extraction, which tests/run.py asserts; `faa`, the tuple
// shape and the pre-launch rejection are the remaining gaps. It backs main.nf and
// FHR_ATTACH until they are resolved; see docs/module-migration.md for the exact
// contract comparison and the adoption procedure.

include { fhrFormat; quote; sampleId } from '../utils/main'

process FHR_CONVERT {
    tag "${meta.id}: ${format}"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fair-bioheaders:0.9.0--pyhdfd78af_0':
        'quay.io/biocontainers/fair-bioheaders:0.9.0--pyhdfd78af_0' }"

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
