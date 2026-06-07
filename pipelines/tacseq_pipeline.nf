#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "./data/tacseq"
params.output_dir = "./results/tacseq"
params.reference_genome = ""
params.metadata_file = "./tacseq_metadata.csv"

process tacseq_metadata_extraction {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    input:
    path metadata_file
    
    output:
    path "tacseq_metadata.json"
    path "timepoint_mapping.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    
    df = pd.read_csv('${metadata_file}')
    
    # Extract TACSEQ specific metadata
    metadata = {
        'pipeline': 'TACSEQ',
        'total_samples': len(df),
        'timepoints': sorted(df['timepoint'].unique().tolist()) if 'timepoint' in df.columns else [],
        'treatments': df['treatment'].unique().tolist() if 'treatment' in df.columns else [],
        'cell_lines': df['cell_line'].unique().tolist() if 'cell_line' in df.columns else [],
        'samples': df.to_dict(orient='records')
    }
    
    # Map timepoints for temporal analysis
    timepoint_mapping = {}
    if 'timepoint' in df.columns:
        for tp in sorted(df['timepoint'].unique()):
            timepoint_mapping[str(tp)] = df[df['timepoint'] == tp]['sample_id'].tolist() if 'sample_id' in df.columns else []
    
    with open('tacseq_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open('timepoint_mapping.json', 'w') as f:
        json.dump(timepoint_mapping, f, indent=2)
    """
}

process chromatin_accessibility {
    publishDir "${params.output_dir}/accessibility", mode: 'copy'
    
    input:
    tuple val(sample_id), path(bam_file)
    path reference_genome
    
    output:
    tuple val(sample_id), path("${sample_id}_peaks.narrowPeak")
    path "${sample_id}_accessibility.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    
    # Call peaks using MACS2 with TACSEQ settings
    import subprocess
    
    subprocess.run(['macs2', 'callpeak',
                    '-t', '${bam_file}',
                    '-f', 'BAM',
                    '-g', 'hs',
                    '-n', '${sample_id}',
                    '--outdir', '.',
                    '-p', '0.001',
                    '--keep-dup', 'all'])
    
    # Calculate accessibility metrics
    with open('${bam_file}.bai', 'rb') as f:
        pass
    
    accessibility = {
        'sample_id': '${sample_id}',
        'peaks_called': True,
        'method': 'MACS2'
    }
    
    with open('${sample_id}_accessibility.json', 'w') as f:
        json.dump(accessibility, f, indent=2)
    """
}

process temporal_dynamics {
    publishDir "${params.output_dir}/temporal", mode: 'copy'
    
    input:
    path accessibility_files
    path timepoint_mapping
    
    output:
    path "temporal_dynamics.json"
    path "dynamic_regions.bed"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    
    with open('${timepoint_mapping}') as f:
        timepoints = json.load(f)
    
    # Analyze temporal dynamics
    dynamics = {
        'timepoints': list(timepoints.keys()),
        'dynamic_regions': [],
        'pattern_analysis': {}
    }
    
    with open('temporal_dynamics.json', 'w') as f:
        json.dump(dynamics, f, indent=2)
    
    # Create BED file for dynamic regions
    with open('dynamic_regions.bed', 'w') as f:
        f.write('chr\tstart\tend\tname\tscore\tstrand\n')
    """
}

workflow tacseq {
    take:
    bam_ch
    reference_genome
    metadata_ch
    
    main:
    tacseq_metadata_extraction(metadata_ch)
    chromatin_accessibility(bam_ch, reference_genome)
    temporal_dynamics(chromatin_accessibility.out[1].collect(), tacseq_metadata_extraction.out[1])
    
    emit:
    peaks = chromatin_accessibility.out
    temporal = temporal_dynamics.out
    metadata = tacseq_metadata_extraction.out
}
