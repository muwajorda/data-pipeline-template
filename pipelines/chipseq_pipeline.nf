#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "./data/chipseq"
params.output_dir = "./results/chipseq"
params.reference_genome = ""
params.blacklist_regions = ""
params.metadata_file = "./chipseq_metadata.csv"

process chipseq_metadata_extraction {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    input:
    path metadata_file
    
    output:
    path "chipseq_metadata.json"
    path "sample_mapping.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    
    df = pd.read_csv('${metadata_file}')
    
    # Extract ChIP-seq specific metadata
    metadata = {
        'pipeline': 'ChIP-seq',
        'total_samples': len(df),
        'sample_types': df['sample_type'].unique().tolist() if 'sample_type' in df.columns else [],
        'transcription_factors': df['transcription_factor'].unique().tolist() if 'transcription_factor' in df.columns else [],
        'cell_types': df['cell_type'].unique().tolist() if 'cell_type' in df.columns else [],
        'samples': df.to_dict(orient='records')
    }
    
    # Create sample mapping (input vs control)
    sample_mapping = {}
    for idx, row in df.iterrows():
        if 'sample_id' in row:
            control = row.get('control_sample', '')
            sample_mapping[row['sample_id']] = {
                'sample_type': row.get('sample_type', 'unknown'),
                'control': control,
                'transcription_factor': row.get('transcription_factor', 'unknown')
            }
    
    with open('chipseq_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open('sample_mapping.json', 'w') as f:
        json.dump(sample_mapping, f, indent=2)
    """
}

process chipseq_qc_filter {
    publishDir "${params.output_dir}/qc", mode: 'copy'
    
    input:
    tuple val(sample_id), path(bam_file)
    
    output:
    tuple val(sample_id), path("${sample_id}_qc.json")
    path "${sample_id}_filtered.bam"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import subprocess
    
    # Calculate QC metrics
    result = subprocess.run(['samtools', 'flagstat', '${bam_file}'],
                          capture_output=True, text=True)
    flagstat = result.stdout
    
    result = subprocess.run(['samtools', 'view', '-c', '${bam_file}'],
                          capture_output=True, text=True)
    total_reads = int(result.stdout.strip())
    
    # Filter BAM: remove low quality, duplicates, unmapped
    subprocess.run(['samtools', 'view', '-b', '-q', '30', '-F', '1804',
                    '${bam_file}', '-o', '${sample_id}_filtered.bam'])
    
    result = subprocess.run(['samtools', 'view', '-c', '${sample_id}_filtered.bam'],
                          capture_output=True, text=True)
    filtered_reads = int(result.stdout.strip())
    
    qc = {
        'sample_id': '${sample_id}',
        'total_reads': total_reads,
        'filtered_reads': filtered_reads,
        'filtering_efficiency': (filtered_reads / total_reads * 100) if total_reads > 0 else 0,
        'flagstat': flagstat
    }
    
    with open('${sample_id}_qc.json', 'w') as f:
        json.dump(qc, f, indent=2)
    """
}

process peak_calling {
    publishDir "${params.output_dir}/peaks", mode: 'copy'
    
    input:
    tuple val(sample_id), path(sample_bam)
    path control_bam
    
    output:
    tuple val(sample_id), path("${sample_id}_peaks.narrowPeak")
    path "${sample_id}_model.r"
    
    script:
    """
    macs2 callpeak \
        -t ${sample_bam} \
        -c ${control_bam} \
        -f BAM \
        -g hs \
        -n ${sample_id} \
        --outdir . \
        -p 0.01 \
        --bdg \
        -m 5 50
    """
}

process annotate_peaks {
    publishDir "${params.output_dir}/annotated_peaks", mode: 'copy'
    
    input:
    tuple val(sample_id), path(peak_file)
    path reference_genome
    
    output:
    tuple val(sample_id), path("${sample_id}_annotated.bed")
    path "${sample_id}_peak_annotation.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import subprocess
    
    # Annotate peaks using Homer
    subprocess.run(['annotatePeaks.pl', '${peak_file}',
                    '${reference_genome}',
                    '-gtf', 'genes.gtf',
                    '-o', '${sample_id}_annotated.bed'])
    
    # Parse annotation results
    annotation_summary = {
        'total_peaks': 0,
        'peak_types': {},
        'annotation_file': '${sample_id}_annotated.bed'
    }
    
    with open('peaks', 'r') as f:
        for line in f:
            if not line.startswith('#'):
                annotation_summary['total_peaks'] += 1
    
    with open('${sample_id}_peak_annotation.json', 'w') as f:
        json.dump(annotation_summary, f, indent=2)
    """
}

process chipseq_consensus_peaks {
    publishDir "${params.output_dir}/consensus", mode: 'copy'
    
    input:
    path peak_files
    
    output:
    path "consensus_peaks.bed"
    path "consensus_summary.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    
    # Merge peaks from multiple samples
    peaks = []
    for peak_file in "${peak_files}".split():
        df = pd.read_csv(peak_file, sep='\t', header=None,
                        names=['chrom', 'start', 'end', 'name', 'score'])
        peaks.append(df)
    
    merged = pd.concat(peaks, ignore_index=True)
    merged = merged.sort_values(['chrom', 'start'])
    
    # Find consensus peaks (appearing in multiple samples)
    consensus = merged.drop_duplicates(subset=['chrom', 'start', 'end'])
    consensus.to_csv('consensus_peaks.bed', sep='\t', header=False, index=False)
    
    summary = {
        'total_consensus_peaks': len(consensus),
        'input_samples': len(set("${peak_files}".split())),
        'chrom_distribution': consensus['chrom'].value_counts().to_dict()
    }
    
    with open('consensus_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    """
}

workflow chipseq {
    take:
    sample_bams_ch
    control_bam_ch
    reference_genome
    metadata_ch
    
    main:
    chipseq_metadata_extraction(metadata_ch)
    chipseq_qc_filter(sample_bams_ch)
    peak_calling(chipseq_qc_filter.out[0], control_bam_ch)
    annotate_peaks(peak_calling.out, reference_genome)
    chipseq_consensus_peaks(annotate_peaks.out[0].collect())
    
    emit:
    peaks = annotate_peaks.out
    metadata = chipseq_metadata_extraction.out
    consensus_peaks = chipseq_consensus_peaks.out
}
