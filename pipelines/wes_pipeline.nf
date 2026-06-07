#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "./data/fastq"
params.output_dir = "./results"
params.reference_genome = ""
params.config_file = "./config.yaml"
params.metadata_file = "./metadata.csv"

// WES Pipeline processes and quality control
process extract_metadata {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    input:
    path metadata_file
    
    output:
    path "sample_metadata.json"
    path "qc_metadata.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    import hashlib
    from datetime import datetime
    
    # Read metadata
    df = pd.read_csv('${metadata_file}')
    
    # Create structured metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'pipeline': 'WES',
        'samples': df.to_dict(orient='records'),
        'statistics': {
            'total_samples': len(df),
            'columns': list(df.columns)
        }
    }
    
    # QC metadata schema
    qc_metadata = {
        'version': '1.0',
        'schema': {
            'sample_id': 'string',
            'fastq_files': 'array',
            'file_sizes': 'array',
            'checksums': 'array',
            'sequencing_date': 'string',
            'read_count': 'integer',
            'quality_score': 'string'
        }
    }
    
    with open('sample_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open('qc_metadata.json', 'w') as f:
        json.dump(qc_metadata, f, indent=2)
    """
}

process fastqc {
    publishDir "${params.output_dir}/qc/fastqc", mode: 'copy'
    
    input:
    path fastq_file
    
    output:
    path "*.html"
    path "*.zip"
    
    script:
    """
    fastqc ${fastq_file} -o .
    """
}

process trim_reads {
    publishDir "${params.output_dir}/trimmed", mode: 'copy'
    
    input:
    tuple val(sample_id), path(fastq_files)
    
    output:
    tuple val(sample_id), path("*_trimmed.fastq.gz")
    
    script:
    """
    trimmomatic PE -threads 8 \
        ${fastq_files[0]} ${fastq_files[1]} \
        ${sample_id}_R1_trimmed.fastq.gz ${sample_id}_R1_unpaired.fastq.gz \
        ${sample_id}_R2_trimmed.fastq.gz ${sample_id}_R2_unpaired.fastq.gz \
        LEADING:20 TRAILING:20 MINLEN:50
    """
}

process align_bwa {
    publishDir "${params.output_dir}/alignments", mode: 'copy'
    
    input:
    tuple val(sample_id), path(fastq_files)
    path reference_genome
    
    output:
    tuple val(sample_id), path("${sample_id}.bam")
    
    script:
    """
    bwa mem -M -t 8 ${reference_genome} ${fastq_files} | \
        samtools view -b - | \
        samtools sort -o ${sample_id}.bam -
    samtools index ${sample_id}.bam
    """
}

process mark_duplicates {
    publishDir "${params.output_dir}/deduped", mode: 'copy'
    
    input:
    tuple val(sample_id), path(bam_file)
    
    output:
    tuple val(sample_id), path("${sample_id}_dedup.bam")
    path "${sample_id}_dup_metrics.txt"
    
    script:
    """
    picard MarkDuplicates \
        INPUT=${bam_file} \
        OUTPUT=${sample_id}_dedup.bam \
        METRICS_FILE=${sample_id}_dup_metrics.txt \
        CREATE_INDEX=true
    """
}

process variant_calling {
    publishDir "${params.output_dir}/variants", mode: 'copy'
    
    input:
    tuple val(sample_id), path(bam_file)
    path reference_genome
    
    output:
    tuple val(sample_id), path("${sample_id}.vcf.gz")
    
    script:
    """
    gatk HaplotypeCaller \
        -R ${reference_genome} \
        -I ${bam_file} \
        -O ${sample_id}.vcf.gz \
        --ERC GVCF
    """
}

process vcf_filtering {
    publishDir "${params.output_dir}/filtered_variants", mode: 'copy'
    
    input:
    tuple val(sample_id), path(vcf_file)
    
    output:
    tuple val(sample_id), path("${sample_id}_filtered.vcf.gz")
    path "${sample_id}_filter_report.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import subprocess
    
    # Filter VCF
    subprocess.run(['bcftools', 'filter', 
                    '-i', 'QUAL>30 && DP>10',
                    '${vcf_file}', 
                    '-o', '${sample_id}_filtered.vcf.gz',
                    '-O', 'z'])
    
    # Generate filter report
    result = subprocess.run(['bcftools', 'view', '-H', '${vcf_file}'],
                          capture_output=True, text=True)
    original_count = len(result.stdout.strip().split('\n'))
    
    result = subprocess.run(['bcftools', 'view', '-H', '${sample_id}_filtered.vcf.gz'],
                          capture_output=True, text=True)
    filtered_count = len(result.stdout.strip().split('\n'))
    
    report = {
        'original_variants': original_count,
        'filtered_variants': filtered_count,
        'variants_removed': original_count - filtered_count
    }
    
    with open('${sample_id}_filter_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    """
}

workflow wes {
    take:
    fastq_ch
    metadata_ch
    reference_genome
    
    main:
    extract_metadata(metadata_ch)
    fastqc(fastq_ch)
    trim_reads(fastq_ch)
    align_bwa(trim_reads.out, reference_genome)
    mark_duplicates(align_bwa.out)
    variant_calling(mark_duplicates.out, reference_genome)
    vcf_filtering(variant_calling.out)
    
    emit:
    filtered_vcf = vcf_filtering.out
    metadata = extract_metadata.out
}
