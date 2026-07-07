# Data Pipeline Template - Complete Exploration Guide

## Overview

This guide walks you through the `data-pipeline-template` repository, showing how it's structured, what each component does, and how to customize it for your bioinformatics needs.

## Repository Structure

```
data-pipeline-template/
├── pipelines/              # Nextflow workflow definitions (47% of codebase)
│   ├── wes_pipeline.nf
│   ├── rnaseq_pipeline.nf
│   ├── chipseq_pipeline.nf
│   ├── atacseq_pipeline.nf
│   ├── tacseq_pipeline.nf
│   ├── gwas_pipeline.nf           # NEW
│   ├── scrnaseq_pipeline.nf        # NEW
│   ├── differential_analysis.nf
│   ├── machine_learning.nf
│   └── multiomics_pipeline.nf
│
├── scripts/                # Python analysis modules (52% of codebase)
│   ├── downstream_analysis.py      # DE, volcano plots, GSEA, ML
│   ├── load_transform_filter.py    # Data preprocessing
│   ├── data_summary.py             # Data QC & summary stats
│   └── extended_analysis.py        # NEW - Advanced analytics
│
├── apps/                   # Streamlit visualization dashboards
│   ├── omics_visualizer.py         # Multi-omics results viewer
│   ├── visualization_dashboard.py  # NGS results viewer
│   └── interactive_explorer.py     # NEW - Advanced exploration
│
├── templates/              # Data format templates
│   ├── metadata_template.tsv
│   └── sample_config.yaml  # NEW
│
├── config.yaml.example     # Minimal configuration
├── config.yaml.complete    # Full configuration with all options
├── environment.yml         # Conda environment specification
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
└── Makefile                # Build automation
```

## Key Components

### 1. Configuration System

The template uses YAML-based configuration for pipeline parameters:

#### Minimal Config (`config.yaml.example`)
```yaml
pipeline:
  name: "Biological Data Pipeline"
  version: "1.0"

input:
  data_source: "genomic_sequence"
  file_format: "fastq"
  batch_size: 1000

steps:
  - name: "Quality Control"
    tool: "fastqc"
    parameters:
      quality_threshold: 30
```

#### Full Config (`config.yaml.complete`)
Supports multiple pipeline types with sophisticated parameters:

```yaml
pipelines:
  wes:              # Whole Exome Sequencing
  rnaseq:           # RNA-seq expression analysis
  chipseq:          # ChIP-sequencing peak calling
  atacseq:          # ATAC-seq accessibility
  gwas:             # Genome-wide association studies
  scrnaseq:         # Single-cell transcriptomics
  differential_analysis:
    fdr_threshold: 0.05
    lfc_threshold: 1.0
  gsea:             # Gene Set Enrichment Analysis
  machine_learning:
    methods:
      - random_forest
      - gradient_boosting
```

### 2. Nextflow Pipelines

Each pipeline in `pipelines/` implements a complete workflow.

#### Example: RNA-seq Pipeline

**File: `pipelines/rnaseq_pipeline.nf`**

Nextflow uses a process-based model:

```nextflow
#!/usr/bin/env nextflow

// Input: FASTQ files from sequencing
process QUALITY_CONTROL {
  container 'nfcore/rnaseq:latest'
  input:
    path reads
  output:
    path 'qc_results'
  script:
  '''
    fastqc $reads -o qc_results
  '''
}

// Quantify transcript abundance
process QUANTIFICATION {
  container 'salmon:latest'
  input:
    path transcriptome
    path reads
  output:
    path 'quants.sf'
  script:
  '''
    salmon quant -t $transcriptome -l A -r $reads -o .
  '''
}

// Differential expression analysis
process DIFFERENTIAL_ANALYSIS {
  container 'bioconductor/bioconductor:latest'
  input:
    path counts
    path metadata
  output:
    path 'de_results.csv'
  script:
  '''
    Rscript deseq2_analysis.R $counts $metadata
  '''
}

workflow {
  reads_ch = channel.fromPath('data/fastq/*.fastq.gz')
  qc_ch = QUALITY_CONTROL(reads_ch)
  quants_ch = QUANTIFICATION(transcriptome, reads_ch)
  results_ch = DIFFERENTIAL_ANALYSIS(quants_ch, metadata)
}
```

### 3. Python Analysis Modules

The `scripts/` directory contains modular analysis components.

#### Downstream Analysis (`scripts/downstream_analysis.py`)

Provides differential analysis, visualization, and ML:

```python
from scripts.downstream_analysis import (
    DifferentialAnalysis,
    VolcanoPlot,
    GSEAAnalysis,
    MachineLearningAnalysis,
    AnalysisPipeline
)

# Example: RNA-seq differential analysis
de_analyzer = DifferentialAnalysis(fdr_threshold=0.05, lfc_threshold=1.0)
results = de_analyzer.rna_seq_deseq2_analysis(
    count_matrix=df,
    sample_groups={'control': ['C1', 'C2'], 'treatment': ['T1', 'T2']}
)

# Create volcano plot
volcano = VolcanoPlot(fdr_threshold=0.05)
fig, summary = volcano.create_volcano_plot(results, output_path='volcano.png')

# Run GSEA
gsea = GSEAAnalysis(gmt_file='genesets.gmt')
gsea_results = gsea.run_gsea(results)

# Machine learning for biomarker discovery
ml = MachineLearningAnalysis()
features, scores = ml.feature_selection_rf(count_matrix, target)
clusters, metrics = ml.clustering_analysis(count_matrix[features])
```

#### Data Preprocessing (`scripts/load_transform_filter.py`)

Handles data ingestion and quality control:

```python
from scripts.load_transform_filter import (
    DataLoader,
    DataTransformer,
    QualityFilter
)

# Load data
loader = DataLoader()
df = loader.load_expression_matrix('data.csv')

# Transform
transformer = DataTransformer()
normalized = transformer.normalize(df, method='quantile')
log_transformed = transformer.log_transform(normalized, pseudocount=1)

# Filter
filter = QualityFilter(min_expression=10, min_samples=2)
filtered = filter.apply(log_transformed)
```

### 4. Visualization Dashboards

#### Omics Visualizer (`apps/omics_visualizer.py`)

Streamlit app supporting WES, ChIP-seq, RNA-seq, and TACSEQ:

```bash
streamlit run apps/omics_visualizer.py
```

Features:
- Multi-omics dashboard with unified metrics
- Assay-specific visualizations (volcano plots, MA plots, peak distributions)
- Comparative analysis across pipeline types
- Interactive filtering and data exploration

```python
# The app structure:
# Page 1: Dashboard - Overview of all pipeline results
# Page 2: WES Analysis - Variant distribution, quality metrics
# Page 3: ChIP-seq Analysis - Peak calling results
# Page 4: RNA-seq Analysis - Gene expression patterns
# Page 5: TACSEQ Analysis - Chromatin accessibility dynamics
# Page 6: Comparative Analysis - Cross-omics correlations
```

## How to Use the Template

### Step 1: Set Up Environment

```bash
# Clone the repository
git clone https://github.com/muwajorda/data-pipeline-template.git
cd data-pipeline-template

# Option A: Conda environment (recommended)
conda env create -f environment.yml
conda activate bioinformatics-env

# Option B: Docker
make docker
docker run -v $(pwd):/workspace pipeline-template
```

### Step 2: Prepare Your Data

Create a `data/` directory with your FASTQ files:

```bash
mkdir -p data/fastq results logs
# Place your *.fastq.gz files in data/fastq/
```

### Step 3: Configure the Pipeline

Edit `config.yaml` to specify:
- Input/output directories
- Tool parameters
- Analysis type (RNA-seq, WES, etc.)
- Cloud provider and resources

```yaml
pipelines:
  rnaseq:
    enabled: true
    input_dir: "./data/fastq"
    reference_genome: "/ref/human_genome.fa"
    annotation_file: "/ref/genes.gtf"
    tools:
      quantification: "salmon"
      de_analysis: "deseq2"
    parameters:
      min_count: 10
      fdr_threshold: 0.05
```

### Step 4: Run the Pipeline

```bash
# Option A: Using Makefile
make run

# Option B: Direct Python
python -m pipeline_template.pipeline

# Option C: Nextflow
nextflow run pipelines/rnaseq_pipeline.nf -c nextflow.config
```

### Step 5: Visualize Results

```bash
cd apps
pip install -r requirements.txt
streamlit run omics_visualizer.py
```

Then navigate to `http://localhost:8501` and upload your results CSV files.

## Customization Examples

### Example 1: Custom RNA-seq Workflow

Create `pipelines/custom_rnaseq.nf`:

```nextflow
#!/usr/bin/env nextflow

params.reads = 'data/fastq/*.fastq.gz'
params.transcriptome = 'ref/transcriptome.fasta'
params.output = 'results'

process TRIM_READS {
  input:
    tuple val(sample), path(read1), path(read2)
  output:
    tuple val(sample), path('*_trimmed.fq.gz')
  script:
  '''
    trimmomatic PE -threads 4 \
      $read1 $read2 \
      ${sample}_trimmed_1.fq.gz ${sample}_unpaired_1.fq.gz \
      ${sample}_trimmed_2.fq.gz ${sample}_unpaired_2.fq.gz \
      ILLUMINACLIP:adapters.fa:2:30:10
  '''
}

process SALMON_QUANT {
  input:
    tuple val(sample), path(trimmed_reads)
  output:
    path "${sample}/quant.sf"
  script:
  '''
    salmon quant -t $params.transcriptome \
      -l A -r $trimmed_reads \
      -o $sample -p 4
  '''
}

workflow {
  reads = channel.fromFilePairs(params.reads)
  trim_ch = TRIM_READS(reads)
  quant_ch = SALMON_QUANT(trim_ch)
}
```

### Example 2: Add Custom Analysis Step

Create `scripts/custom_analysis.py`:

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from umap import UMAP

class DimensionalityReduction:
    def __init__(self, method='umap'):
        self.method = method
    
    def reduce(self, expression_matrix, n_components=2):
        # Normalize
        scaler = StandardScaler()
        normalized = scaler.fit_transform(expression_matrix)
        
        # Reduce dimensions
        if self.method == 'umap':
            reducer = UMAP(n_components=n_components)
            embedding = reducer.fit_transform(normalized)
        
        return pd.DataFrame(
            embedding,
            columns=[f'UMAP_{i}' for i in range(n_components)],
            index=expression_matrix.index
        )

# Usage
reducer = DimensionalityReduction(method='umap')
umap_coords = reducer.reduce(count_matrix, n_components=2)
```

## New Extensions

### GWAS Pipeline

**File: `pipelines/gwas_pipeline.nf`**

Genome-wide association studies for identifying genetic variants associated with traits:

```nextflow
process QC_GWAS {
  // Quality control specific to GWAS
  // - Hardy-Weinberg equilibrium
  // - Minor allele frequency filtering
  // - Linkage disequilibrium pruning
}

process ASSOCIATION_TEST {
  // Run association tests (logistic/linear regression)
}

process MANHATTAN_PLOT {
  // Visualize results
}
```

### Single-cell RNA-seq Pipeline

**File: `pipelines/scrnaseq_pipeline.nf`**

Processing and analysis of single-cell transcriptomics data:

```nextflow
process CELL_RANGER_COUNT {
  // 10x Genomics data processing
}

process QUALITY_CONTROL {
  // Cell filtering, doublet detection
}

process DIMENSIONALITY_REDUCTION {
  // PCA, UMAP, t-SNE
}

process CLUSTERING {
  // Cell type identification
}
```

## Best Practices

1. **Version Control**: Always version your config files and custom scripts
2. **Reproducibility**: Use fixed software versions and seed values
3. **Documentation**: Document custom parameters and modifications
4. **Testing**: Test on small datasets before full-scale runs
5. **Modularity**: Create reusable workflow components
6. **Monitoring**: Check logs regularly for errors

## Troubleshooting

### Issue: "Tool not found" errors
**Solution**: Ensure all required tools are installed:
```bash
conda install -c bioconda bwa samtools gatk fastqc salmon
```

### Issue: Memory errors
**Solution**: Adjust resource parameters in config:
```yaml
resources:
  cpu: 16
  memory_gb: 64
  temp_dir: "/tmp/pipeline"
```

### Issue: Nextflow cache issues
**Solution**: Clear work directory:
```bash
rm -rf work/
nextflow clean
```

## Resources

- [Nextflow Documentation](https://www.nextflow.io/docs/latest/index.html)
- [nf-core Pipelines](https://nf-co.re/)
- [Bioconductor](https://www.bioconductor.org/)
- [BioPython](https://biopython.org/)

## Support

For issues or questions:
1. Check existing documentation
2. Review logs in `logs/` directory
3. Open an issue on GitHub with details
