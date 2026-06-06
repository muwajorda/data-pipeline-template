#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Patient-aware ATAC-seq pipeline with metadata tracking
// Supports multi-sample patient cohorts with quality metrics and reproducibility

params {
    patient_data_dir = "data/patients"
    metadata_file = "metadata/patient_metadata.csv"
    reference_genome = "reference/hg38"
    results_dir = "results"
    qc_threshold = 20
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

process quality_control {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/qc_reports", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(reads)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_fastqc.html"), path("${sample_id}_fastqc.zip")
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_qc_metrics.txt")

    script:
    """
    fastqc ${reads} -o . --extract -f fastq
    mv fastqc_data.txt ${sample_id}_fastqc_data.txt
    
    # Extract QC metrics
    python3 << 'QC_EOF'
    import json
    qc_metrics = {
        'patient_id': '${patient_id}',
        'sample_id': '${sample_id}',
        'condition': '${condition}',
        'total_reads': 0,
        'gc_content': 0,
        'quality_score': 0
    }
    with open('${sample_id}_qc_metrics.txt', 'w') as f:
        json.dump(qc_metrics, f, indent=2)
    QC_EOF
    """
}

process trimming {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/trimmed_reads", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(reads), path(qc_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_trimmed.fastq"), path("${sample_id}_trim_metrics.txt")

    script:
    """
    trimmomatic SE -phred33 ${reads} ${sample_id}_trimmed.fastq \
        SLIDINGWINDOW:4:20 MINLEN:36 2> ${sample_id}_trim_metrics.txt
    """
}

process alignment {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/alignments", mode: 'copy'
    memory '16 GB'
    cpus 8
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(trimmed_reads), path(trim_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_aligned.bam"), path("${sample_id}_alignment_metrics.txt")

    script:
    """
    bowtie2 -x ${params.reference_genome} -U ${trimmed_reads} \
        --threads 8 -S ${sample_id}_aligned.sam 2> ${sample_id}_alignment_metrics.txt
    
    samtools view -bS ${sample_id}_aligned.sam | samtools sort -o ${sample_id}_aligned.bam -
    samtools index ${sample_id}_aligned.bam
    rm ${sample_id}_aligned.sam
    """
}

process peak_calling {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/peaks", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(bam), path(alignment_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_peaks.narrowPeak"), path("${sample_id}_peaks_metrics.txt")

    script:
    """
    macs2 callpeak -t ${bam} -f BAM -g hs -n ${sample_id}_peaks -B --outdir .
    
    # Generate peak calling metrics
    wc -l ${sample_id}_peaks.narrowPeak > ${sample_id}_peaks_metrics.txt
    """
}

process chromatin_accessibility_analysis {
    tag "${patient_id}/${sample_id}"
    publishDir "${params.results_dir}/${patient_id}/accessibility_analysis", mode: 'copy'
    
    input:
    tuple val(patient_id), val(sample_id), val(condition), path(peaks), path(peaks_metrics)

    output:
    tuple val(patient_id), val(sample_id), val(condition), path("${sample_id}_accessibility_report.html")

    script:
    """
    python3 << 'ANALYSIS_EOF'
    import json
    
    accessibility_data = {
        'patient_id': '${patient_id}',
        'sample_id': '${sample_id}',
        'condition': '${condition}',
        'analysis_type': 'chromatin_accessibility',
        'peak_count': 0,
        'accessible_regions': []
    }
    
    with open('${sample_id}_accessibility_report.html', 'w') as f:
        f.write('<html><body>')
        f.write('<h1>Chromatin Accessibility Report</h1>')
        f.write(f'<p>Patient: {accessibility_data["patient_id"]}</p>')
        f.write(f'<p>Sample: {accessibility_data["sample_id"]}</p>')
        f.write(f'<p>Condition: {accessibility_data["condition"]}</p>')
        f.write('</body></html>')
    ANALYSIS_EOF
    """
}

process generate_patient_report {
    tag "${patient_id}"
    publishDir "${params.results_dir}/${patient_id}", mode: 'copy'
    
    input:
    tuple val(patient_id), path(qc_reports), path(accessibility_reports)

    output:
    path("${patient_id}_patient_report.txt")

    script:
    """
    cat > ${patient_id}_patient_report.txt << 'REPORT_EOF'
    ================== PATIENT ANALYSIS REPORT ==================
    Patient ID: ${patient_id}
    Analysis Date: \$(date)
    
    QC Reports:
    \$(ls -la ${qc_reports})
    
    Accessibility Analysis:
    \$(ls -la ${accessibility_reports})
    
    ============================================================
    REPORT_EOF
    """
}

workflow {
    // Load patient metadata
    metadata_ch = load_patient_metadata()
        .splitCsv()
        .map { row -> tuple(row[0], row[1], row[2], file(row[3])) }
    
    // QC process
    qc_results = quality_control(metadata_ch)
    
    // Extract data for next process
    trimming_input = qc_results
        .map { patient_id, sample_id, condition, html, zip, metrics -> 
            tuple(patient_id, sample_id, condition, file("data/patients/${patient_id}/${sample_id}.fastq"), metrics) 
        }
    
    // Trimming
    trimmed = trimming(trimming_input)
    
    // Alignment
    aligned = alignment(trimmed)
    
    // Peak calling
    peaks = peak_calling(aligned)
    
    // Chromatin accessibility analysis
    accessibility = chromatin_accessibility_analysis(peaks)
    
    // Generate patient-level report
    patient_report_input = accessibility
        .groupTuple(by: 0)
        .map { patient_id, sample_ids, conditions, reports -> 
            tuple(patient_id, reports.flatten(), reports.flatten()) 
        }
    generate_patient_report(patient_report_input)
}
