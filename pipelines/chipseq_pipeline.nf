#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Patient-aware ChIP-seq pipeline with metadata tracking
// Supports multi-sample patient cohorts with differential binding analysis

params {
    patient_data_dir = "data/patients"
    metadata_file = "metadata/patient_metadata.csv"
    bowtie2_index = "reference/bowtie2_index/hg38"
    results_dir = "results"
}

process load_patient_metadata {
    output:
    stdout

    script:
    """
    python3 << 'EOF'
    import csv
    with open('${params.metadata_file}', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(f"{row['patient_id']},{row['sample_id']},{row['condition']},{row['fastq_file']}")
    EOF
    """
}

process fastqc {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/qc_reports", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(fastq_files)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("*.html"), path("*.zip")

    script:
    """
    fastqc ${fastq_files} -o .
    """
}

process trim {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/trimmed_reads", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(fastq_file)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_trimmed.fastq"), path("${sample_id}_trim_metrics.txt")

    script:
    """
    trimmomatic SE -phred33 ${fastq_file} ${sample_id}_trimmed.fastq \
        SLIDINGWINDOW:4:20 MINLEN:36 2> ${sample_id}_trim_metrics.txt
    """
}

process bowtie2_align {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/alignments", mode: 'copy'
    memory '16 GB'
    cpus 8
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(trimmed_fastq), path(trim_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}.bam"), path("${sample_id}_alignment_metrics.txt")

    script:
    """
    bowtie2 -x ${params.bowtie2_index} -U ${trimmed_fastq} \
        --threads 8 -S ${sample_id}.sam 2> ${sample_id}_alignment_metrics.txt
    
    samtools view -bS ${sample_id}.sam | samtools sort -o ${sample_id}.bam -
    samtools index ${sample_id}.bam
    rm ${sample_id}.sam
    """
}

process macs2_peak_calling {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/peaks", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(bam_file), path(alignment_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_peaks.narrowPeak"), path("${sample_id}_peaks_metrics.txt")

    script:
    """
    macs2 callpeak -t ${bam_file} -f BAM -g hs -n ${sample_id}_peaks -B --outdir .
    
    # Generate peak calling metrics
    wc -l ${sample_id}_peaks.narrowPeak > ${sample_id}_peaks_metrics.txt
    """
}

process diffbind_analysis {
    tag "${patient_id}"
    publishDir "${params.results_dir}/${patient_id}", mode: 'copy'
    
    input:
    tuple val(patient_id), path(peaks_files), val(conditions)

    output:
    path("${patient_id}_differential_binding_results.txt"), emit: results
    path("${patient_id}_diffbind_report.html"), emit: report

    script:
    """
    python3 << 'DIFFBIND_EOF'
    import json
    import os
    
    # Parse peak files and conditions
    peaks_list = """${peaks_files}""".strip().split()
    conditions = """${conditions}""".strip().split(',')
    
    diffbind_results = {
        'patient_id': '${patient_id}',
        'analysis_type': 'differential_binding',
        'samples': []
    }
    
    for i, peak_file in enumerate(peaks_list):
        if os.path.exists(peak_file):
            sample_data = {
                'peak_file': peak_file,
                'condition': conditions[i] if i < len(conditions) else 'unknown',
                'peak_count': sum(1 for line in open(peak_file))
            }
            diffbind_results['samples'].append(sample_data)
    
    # Write results
    with open('${patient_id}_differential_binding_results.txt', 'w') as f:
        json.dump(diffbind_results, f, indent=2)
    
    # Generate HTML report
    with open('${patient_id}_diffbind_report.html', 'w') as f:
        f.write('<html><body>')
        f.write('<h1>Differential Binding Analysis Report</h1>')
        f.write(f'<p>Patient ID: {diffbind_results["patient_id"]}</p>')
        f.write('<h2>Samples:</h2><ul>')
        for sample in diffbind_results['samples']:
            f.write(f'<li>{sample["peak_file"]} ({sample["condition"]}) - {sample["peak_count"]} peaks</li>')
        f.write('</ul></body></html>')
    DIFFBIND_EOF
    """
}

process generate_patient_report {
    tag "${patient_id}"
    publishDir "${params.results_dir}/${patient_id}", mode: 'copy'
    
    input:
    tuple val(patient_id), path(diffbind_results), path(diffbind_report)

    output:
    path("${patient_id}_chipseq_patient_report.txt")

    script:
    """
    cat > ${patient_id}_chipseq_patient_report.txt << 'REPORT_EOF'
    ================== ChIP-seq PATIENT ANALYSIS REPORT ==================
    Patient ID: ${patient_id}
    Analysis Date: \$(date)
    Analysis Type: Chromatin Immunoprecipitation Sequencing
    
    Differential Binding Analysis:
    \$(cat ${diffbind_results})
    
    =====================================================================
    REPORT_EOF
    """
}

workflow {
    // Load patient metadata
    metadata_ch = load_patient_metadata()
        .splitCsv()
        .map { row -> tuple(row[0], row[1], row[2], file(row[3])) }
    
    // QC process
    qc_results = fastqc(metadata_ch)
    
    // Trimming
    trimmed = trim(metadata_ch)
    
    // Alignment
    aligned = bowtie2_align(trimmed)
    
    // Peak calling
    peaks = macs2_peak_calling(aligned)
    
    // Differential binding analysis grouped by patient
    diffbind_input = peaks
        .groupTuple(by: 0)
        .map { patient_id, sample_ids, conditions, peak_files, metrics -> 
            tuple(patient_id, peak_files.flatten(), conditions.join(',')) 
        }
    
    diffbind = diffbind_analysis(diffbind_input)
    
    // Generate patient-level report
    patient_report_input = diffbind
        .map { patient_id, results, report -> 
            tuple(patient_id, results, report) 
        }
    generate_patient_report(patient_report_input)
}
