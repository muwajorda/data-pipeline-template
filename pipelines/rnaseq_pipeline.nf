#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "./data/rnaseq"
params.output_dir = "./results/rnaseq"
params.reference_genome = ""
params.annotation_file = ""
params.metadata_file = "./rnaseq_metadata.csv"

process rnaseq_metadata_extraction {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    input:
    path metadata_file
    
    output:
    path "rnaseq_metadata.json"
    path "sample_groups.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    
    df = pd.read_csv('${metadata_file}')
    
    # Extract RNA-seq specific metadata
    metadata = {
        'pipeline': 'RNA-seq',
        'total_samples': len(df),
        'experimental_conditions': df['condition'].unique().tolist() if 'condition' in df.columns else [],
        'treatments': df['treatment'].unique().tolist() if 'treatment' in df.columns else [],
        'replicates': df['replicate'].unique().tolist() if 'replicate' in df.columns else [],
        'samples': df.to_dict(orient='records')
    }
    
    # Create sample grouping for comparison
    sample_groups = {}
    for condition in df['condition'].unique() if 'condition' in df.columns else []:
        group = df[df['condition'] == condition]
        sample_groups[condition] = group['sample_id'].tolist() if 'sample_id' in df.columns else []
    
    with open('rnaseq_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open('sample_groups.json', 'w') as f:
        json.dump(sample_groups, f, indent=2)
    """
}

process quantify_expression {
    publishDir "${params.output_dir}/quantification", mode: 'copy'
    
    input:
    tuple val(sample_id), path(fastq_files)
    path annotation_file
    
    output:
    tuple val(sample_id), path("${sample_id}/quant.sf")
    path "${sample_id}_mapping_rate.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    
    salmon quant -i salmon_index \
        -l A \
        -r ${fastq_files} \
        -o ${sample_id} \
        --validateMappings
    
    # Extract mapping statistics
    import json
    with open('${sample_id}/aux_info/meta_info.json') as f:
        meta = json.load(f)
    
    mapping_stats = {
        'sample_id': '${sample_id}',
        'total_reads': meta.get('num_processed', 0),
        'mapped_reads': meta.get('num_mapped', 0)
    }
    
    with open('${sample_id}_mapping_rate.json', 'w') as f:
        json.dump(mapping_stats, f, indent=2)
    """
}

process create_count_matrix {
    publishDir "${params.output_dir}/counts", mode: 'copy'
    
    input:
    path quantification_files
    
    output:
    path "gene_count_matrix.csv"
    path "count_matrix_summary.json"
    
    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    import json
    import os
    
    # Create count matrix from salmon quantifications
    count_matrix = pd.DataFrame()
    
    for quant_file in "${quantification_files}".split():
        sample_name = os.path.dirname(quant_file).split('/')[-1]
        df = pd.read_csv(quant_file, sep='\t')
        df['Name'] = df['Name'].str.split('.').str[0]  # Get gene ID
        count_matrix[sample_name] = df.set_index('Name')['TPM']
    
    count_matrix.to_csv('gene_count_matrix.csv')
    
    summary = {
        'total_genes': len(count_matrix),
        'total_samples': len(count_matrix.columns),
        'genes_with_expression': (count_matrix > 0).sum().sum()
    }
    
    with open('count_matrix_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    """
}

process quality_control {
    publishDir "${params.output_dir}/qc", mode: 'copy'
    
    input:
    path count_matrix
    
    output:
    path "qc_report.html"
    path "qc_metrics.json"
    
    script:
    """
    #!/usr/bin/env python3
    import json
    import pandas as pd
    import numpy as np
    
    df = pd.read_csv('${count_matrix}', index_col=0)
    
    # Calculate QC metrics
    metrics = {
        'library_sizes': df.sum().to_dict(),
        'gene_counts': (df > 0).sum().to_dict(),
        'mean_expression': df.mean().to_dict(),
        'median_expression': df.median().to_dict()
    }
    
    with open('qc_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Generate HTML report
    html = f"""
    <html>
    <head><title>RNA-seq QC Report</title></head>
    <body>
    <h1>RNA-seq Quality Control Report</h1>
    <p>Total Samples: {len(df.columns)}</p>
    <p>Total Genes: {len(df)}</p>
    </body>
    </html>
    """
    
    with open('qc_report.html', 'w') as f:
        f.write(html)
    """
}

workflow rnaseq {
    take:
    fastq_ch
    annotation_file
    metadata_ch
    
    main:
    rnaseq_metadata_extraction(metadata_ch)
    quantify_expression(fastq_ch, annotation_file)
    create_count_matrix(quantify_expression.out[0].collect())
    quality_control(create_count_matrix.out[0])
    
    emit:
    count_matrix = create_count_matrix.out
    metadata = rnaseq_metadata_extraction.out
}
