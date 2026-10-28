process FAIRBIOHEADERS_COMBINE {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fair-bioheaders:0.8.2--pyhdfd78af_0':
        'quay.io/biocontainers/fair-bioheaders:0.8.2--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(metadata), path(sequence)

    output:
    tuple val(meta), path("${prefix}.fh*"), emit: sequence
    tuple val("${task.process}"), val('fair-bioheaders'), eval("bioheaders --version"), emit: versions_fairbioheaders, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    prefix = task.ext.prefix ?: "${meta.id}"
    // Single-quote for the shell: file names and meta.id may hold any character.
    def quote = { value -> "'" + value.toString().replace("'", "'\\''") + "'" }
    // Protein FASTA (.faa) is FASTA to the toolkit.
    def type = sequence.name ==~ /.*\.gfa(\.b?gz)?$/ ? 'gfa'
        : sequence.name ==~ /.*\.gff3?(\.b?gz)?$/ ? 'gff3' : 'fasta'
    // The output is BGZF-compressed when its name ends in .gz: keep the input's compression.
    def gz = sequence.name ==~ /.*\.b?gz$/ ? '.gz' : ''
    // The output is named by its header type, which the toolkit takes from the metadata's
    // schema URL: FHR (<prefix>.fhr.fa, <prefix>.fhr.gfa), FHP (<prefix>.fhp.faa) or
    // FHGFF3 (<prefix>.fhgff3.gff3). bioheaders combine rejects a header type the
    // sequence type cannot carry, such as FHP on GFA or FHR on GFF3.
    def extension = [gfa: 'gfa', gff3: 'gff3', fasta: 'fa'][type]
    """
    bioheaders convert --to json ${quote.call(metadata)} header-type.json
    family="\$(python -c 'import json, sys, bioheaders; print(bioheaders.header_type(json.load(open(sys.argv[1], encoding="utf-8"))).lower())' header-type.json)"
    case "\$family" in
        fhp) extension=faa ;;
        *) extension=${extension} ;;
    esac

    bioheaders combine \\
        --type ${type} \\
        ${args} \\
        --output ${quote.call(prefix)}".\$family.\$extension${gz}" \\
        ${quote.call(metadata)} \\
        ${quote.call(sequence)}
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    def quote = { value -> "'" + value.toString().replace("'", "'\\''") + "'" }
    def type = sequence.name ==~ /.*\.gfa(\.b?gz)?$/ ? 'gfa'
        : sequence.name ==~ /.*\.gff3?(\.b?gz)?$/ ? 'gff3' : 'fasta'
    // Without running the toolkit, protein FASTA (.faa) stands for FHP.
    def protein = sequence.name ==~ /.*\.faa(\.b?gz)?$/
    def header = type == 'gff3' ? 'fhgff3' : protein ? 'fhp' : 'fhr'
    def extension = [gfa: 'gfa', gff3: 'gff3', fasta: protein ? 'faa' : 'fa'][type]
    def gzipped = quote.call("${prefix}.${header}.${extension}.gz")
    def plain = quote.call("${prefix}.${header}.${extension}")
    def output = sequence.name ==~ /.*\.b?gz$/
        ? "echo '' | gzip > ${gzipped}"
        : "touch ${plain}"
    """
    ${output}
    """
}
