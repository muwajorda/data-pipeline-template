#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process fastqc {
    input:
    path fastq_files

    output:
    path "*.html"
    path "*.zip"

    script:
    """
    fastqc $fastq_files -o .
    """
}

process trim {
    input:
    path fastq_file

    output:
    path "${fastq_file.baseName}_trimmed.fastq"

    script:
    """
    trimmomatic SE -phred33 $fastq_file ${fastq_file.baseName}_trimmed.fastq SLIDINGWINDOW:4:20 MINLEN:36
    """
}

process bowtie2_align {
    input:
    path trimmed_fastq

    output:
    path "*.bam"

    script:
    """
    bowtie2 -x /path/to/bowtie2_index -U $trimmed_fastq | samtools view -bS - > ${trimmed_fastq.baseName}.bam
    """
}

process macs2_peak_calling {
    input:
    path bam_file

    output:
    path "*.narrowPeak"

    script:
    """
    macs2 callpeak -t $bam_file -f BAM -g hs -n ${bam_file.baseName} --outdir .
    """
}

process diffbind_analysis {
    input:
    path peaks_files

    output:
    path "differential_binding_results.txt"

    script:
    """
    Rscript diffbind_analysis.R $peaks_files
    """
}

workflow {
    fastq_files = dir('path/to/fastq_files/*.fastq')
    
    fastqc_results = fastqc(fastq_files)
    trimmed_files = fastq_files.map { trim(it) }
    aligned_bams = trimmed_files.map { bowtie2_align(it) }
    peaks = aligned_bams.map { macs2_peak_calling(it) }
    diffbind_analysis(peaks)
}