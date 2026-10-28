process FAIRBIOHEADERS_VALIDATE {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fair-bioheaders:0.8.2--pyhdfd78af_0':
        'quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(metadata)

    output:
    tuple val(meta), path("*.validate.txt"), emit: report
    tuple val("${task.process}"), val('fair-bioheaders'), eval("bioheaders --version"), emit: versions_fairbioheaders, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    // Single-quote for the shell: file names and meta.id may hold any character.
    def quote = { value -> "'" + value.toString().replace("'", "'\\''") + "'" }
    def report = quote.call("${prefix}.validate.txt")
    // Standalone metadata only (no sequence and no checksum check; see
    // fairbioheaders/verify for headed files). The schema URL selects the header type
    // (FHR, FHP or FHGFF3) and schema version; metadata that fails its schema, or that
    // cites a schema version the toolkit does not bundle, exits non-zero, so the task
    // fails. The report records the validated file and the result.
    """
    {
        printf 'file: %s\\n' ${quote.call(metadata)}
        bioheaders validate ${args} ${quote.call(metadata)}
    } > ${report}
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def quote = { value -> "'" + value.toString().replace("'", "'\\''") + "'" }
    def report = quote.call("${prefix}.validate.txt")
    """
    touch ${report}
    """
}
