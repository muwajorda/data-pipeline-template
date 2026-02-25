#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.reads = "data/*_{1,2}.fastq.gz"
params.outdir = "results"

process fastqc {
    input:
    path reads

    output:
    path "results/fastqc/*"

    script:
    """
    fastqc -o results/fastqc/ ${reads}
    """
}

process trim_galore {
    input:
    path reads

    output:
    path "results/trimmed/*"

    script:
    """
    trim_galore --paired ${reads} -o results/trimmed/
    """
}

process star_align {
    input:
    path reads

    output:
    path "results/aligned/*.bam"

    script:
    """
    STAR --runThreadN 4 --genomeDir /path/to/genome_index --readFilesIn ${reads} --outFileNamePrefix results/aligned/
    """
}

process sort_bam {
    input:
    path bam

    output:
    path "results/sorted/*.sorted.bam"

    script:
    """
    samtools sort -o results/sorted/${bam.baseName}.sorted.bam ${bam}
    """
}

process mark_duplicates {
    input:
    path sorted_bam

    output:
    path "results/marked_duplicates/*.rmdup.bam"

    script:
    """
    picard MarkDuplicates I=${sorted_bam} O=results/marked_duplicates/${sorted_bam.baseName}.rmdup.bam M=results/marked_duplicates/${sorted_bam.baseName}.metrics.txt
    """
}

process featureCounts {
    input:
    path marked_bam

    output:
    path "results/counts/counts.txt"

    script:
    """
    featureCounts -a /path/to/annotation.gtf -o results/counts/counts.txt ${marked_bam}
    """
}

workflow {
    fastqc(params.reads)
    trimmed = trim_galore(fastqc.out)
    aligned = star_align(trimmed)
    sorted = sort_bam(aligned)
    marked = mark_duplicates(sorted)
    featureCounts(marked)
}