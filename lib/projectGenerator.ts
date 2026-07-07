export function generateProjectFiles(
  assessment: any,
  recommendation: any
): Record<string, string> {
  const projectName = 'bioinformatics-project'
  const files: Record<string, string> = {}

  // package.json
  files['package.json'] = JSON.stringify(
    {
      name: projectName,
      version: '1.0.0',
      description: `Bioinformatics pipeline generated for ${assessment.dataType}`,
      scripts: {
        'nextflow:run': 'nextflow run main.nf',
        'build:docker': 'docker build -t bioinformatics-pipeline .',
        'setup:env': 'conda env create -f environment.yml',
      },
      dependencies: {},
    },
    null,
    2
  )

  // environment.yml
  files['environment.yml'] = `name: bioinformatics-env
channels:
  - conda-forge
  - bioconda
dependencies:
  - python=3.11
  - nextflow
  - ${recommendation.tools?.join('\n  - ') || 'samtools\n  - bwa'}
`

  // main.nf
  files['main.nf'] = generateNextflowScript(recommendation)

  // Dockerfile
  files['Dockerfile'] = `FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["nextflow", "run", "main.nf"]
`

  // README.md
  files['README.md'] = `# ${projectName}

Bioinformatics pipeline for ${assessment.dataType}

## Generated Configuration

- **Data Type**: ${assessment.dataType}
- **Analysis Type**: ${assessment.analysisType}
- **Experience Level**: ${assessment.experience}
- **Deployment Method**: ${assessment.deploymentMethod}

## Recommended Pipelines

${recommendation.pipelines?.map((p: string) => `- ${p}`).join('\n') || '- RNA-seq'}

## Recommended Tools

${recommendation.tools?.map((t: string) => `- ${t}`).join('\n') || '- samtools'}

## Setup

\`\`\`bash
# Create conda environment
conda env create -f environment.yml
conda activate bioinformatics-env

# Install dependencies
pip install -r requirements.txt
\`\`\`

## Usage

\`\`\`bash
nextflow run main.nf --input data/ --output results/
\`\`\`

## Documentation

See ARCHITECTURE.md for pipeline design details.
`

  // config.yaml
  files['config.yaml'] = `pipeline:
  name: "Bioinformatics Pipeline"
  version: "1.0"
  analysis_type: "${assessment.analysisType}"
  data_type: "${assessment.dataType}"

input:
  data_dir: "./data"
  file_format: "fastq"

output:
  results_dir: "./results"
  reports_dir: "./reports"

tools:
  recommended: [${recommendation.tools?.map((t: string) => `"${t}"`).join(', ') || '"samtools"'}]

resources:
  memory: "16GB"
  cpus: 8
  time: "24h"
`

  // requirements.txt
  files['requirements.txt'] = `pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
pyyaml>=6.0
pytest>=7.4.0
`

  // scripts directory
  files['scripts/data_processing.py'] = `#!/usr/bin/env python3
"""Data processing script for bioinformatics pipeline"""

import pandas as pd
import sys
from pathlib import Path

def process_data(input_file: str, output_file: str):
    """Process input data and save results"""
    print(f"Processing {input_file}...")
    
    # Add your data processing logic here
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python data_processing.py <input> <output>")
        sys.exit(1)
    
    process_data(sys.argv[1], sys.argv[2])
`

  files['ARCHITECTURE.md'] = `# Pipeline Architecture

## Generated for: ${assessment.dataType}

### Analysis Type
${assessment.analysisType}

### Recommended Components

${recommendation.pipelines?.map((p: string) => `- **${p}**`).join('\n') || '- RNA-seq pipeline'}

### Tools & Technologies

${recommendation.tools?.map((t: string) => `- ${t}`).join('\n') || '- samtools'}

### Complexity Level
${recommendation.estimated_complexity}

### Rationale
${recommendation.rationale}
`

  return files
}

function generateNextflowScript(recommendation: any): string {
  return `#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "./data"
params.output_dir = "./results"
params.help = false

if (params.help) {
    println """
    Bioinformatics Pipeline
    ======================
    
    Usage:
        nextflow run main.nf --input_dir <path> --output_dir <path>
    
    Options:
        --input_dir     Input directory (default: ./data)
        --output_dir    Output directory (default: ./results)
    """
    exit(0)
}

process process_data {
    publishDir params.output_dir, mode: 'copy'
    
    input:
    path input_files
    
    output:
    path "processed_*.txt"
    
    script:
    """
    # Add your analysis steps here
    echo "Processing data..."
    touch processed_output.txt
    """
}

process generate_report {
    publishDir params.output_dir, mode: 'copy'
    
    input:
    path processed_files
    
    output:
    path "report.html"
    
    script:
    """
    echo "<html><body>Analysis Report</body></html>" > report.html
    """
}

workflow {
    input_data = Channel.fromPath("\${params.input_dir}/*")
    process_data(input_data)
    generate_report(process_data.out.collect())
}
`
}
