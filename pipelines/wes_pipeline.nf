#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process fastqc {
    input:
    path fastq_file
    output:
    path "*.html", path "*.zip"
    script:
    "
    fastqc ${fastq_file} -o .
    "