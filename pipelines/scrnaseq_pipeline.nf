#!/usr/bin/env nextflow

/*
 * Single-cell RNA-seq Pipeline
 * Processes 10x Genomics and other single-cell data
 */

params.fastq = 'data/fastq'
params.transcriptome = 'ref/transcriptome.fasta'
params.output = 'results/scrnaseq'
params.chemistry = 'v3'  // 10x chemistry version
params.expect_cells = 5000

process CELLRANGER_COUNT {
  tag "${sample_id}"
  container 'cellranger:latest'
  cpus 16
  memory '64 GB'
  time '8h'
  
  input:
    val sample_id
    path fastq_dir
  
  output:
    path "${sample_id}/outs/filtered_feature_bc_matrix"
  
  script:
  '''
    cellranger count \
      --id=$sample_id \
      --transcriptome=$params.transcriptome \
      --fastqs=$fastq_dir \
      --sample=$sample_id \
      --chemistry=$params.chemistry \
      --expect-cells=$params.expect_cells
  '''
}

process SEURAT_QC {
  tag "${sample_id}"
  container 'seuratproject/seurat:latest'
  
  input:
    val sample_id
    path matrix
  
  output:
    path "${sample_id}_seurat_qc.rds"
  
  script:
  '''
    Rscript - <<EOF
    library(Seurat)
    
    # Load data
    data <- Read10X(data.dir = '$matrix')
    seurat <- CreateSeuratObject(counts = data, project = '$sample_id')
    
    # QC metrics
    seurat[["percent.mt"]] <- PercentageFeatureSet(seurat, pattern = "^MT-")
    seurat[["percent.ribo"]] <- PercentageFeatureSet(seurat, pattern = "^RP[SL]")
    
    # Filter cells
    seurat <- subset(seurat, 
                     nFeature_RNA > 200 & nFeature_RNA < 5000 &
                     percent.mt < 10)
    
    # Normalize and scale
    seurat <- NormalizeData(seurat)
    seurat <- FindVariableFeatures(seurat)
    seurat <- ScaleData(seurat)
    
    # Dimensionality reduction
    seurat <- RunPCA(seurat)
    seurat <- RunUMAP(seurat, dims = 1:30)
    
    # Save
    saveRDS(seurat, '${sample_id}_seurat_qc.rds')
    EOF
  '''
}

process CLUSTERING {
  tag "${sample_id}"
  container 'seuratproject/seurat:latest'
  
  input:
    path seurat_object
  
  output:
    tuple path('*.rds'), path('*.csv')
  
  script:
  '''
    Rscript - <<EOF
    library(Seurat)
    library(SingleR)
    
    seurat <- readRDS('$seurat_object')
    
    # Find neighbors and clusters
    seurat <- FindNeighbors(seurat, dims = 1:30)
    seurat <- FindClusters(seurat, resolution = 0.5)
    
    # Identify cell types using SingleR
    # (requires reference data)
    
    # Save clustered object
    saveRDS(seurat, 'clustered.rds')
    
    # Export cluster assignments
    cluster_data <- data.frame(
      cell = colnames(seurat),
      cluster = Idents(seurat)
    )
    write.csv(cluster_data, 'clusters.csv', row.names=FALSE)
    EOF
  '''
}

process DIFFERENTIAL_EXPRESSION {
  tag "cluster_comparison"
  container 'seuratproject/seurat:latest'
  
  input:
    path clustered_object
  
  output:
    path 'de_results.csv'
  
  script:
  '''
    Rscript - <<EOF
    library(Seurat)
    
    seurat <- readRDS('$clustered_object')
    
    # Find markers for each cluster
    markers <- FindAllMarkers(seurat, only.pos = TRUE, 
                            min.pct = 0.25, logfc.threshold = 0.25)
    
    write.csv(markers, 'de_results.csv', row.names=FALSE)
    EOF
  '''
}

process VISUALIZATION {
  tag "umap_and_plots"
  container 'seuratproject/seurat:latest'
  
  input:
    path clustered_object
  
  output:
    tuple path('umap.png'), path('feature_plots.png')
  
  script:
  '''
    Rscript - <<EOF
    library(Seurat)
    library(ggplot2)
    
    seurat <- readRDS('$clustered_object')
    
    # UMAP colored by cluster
    p1 <- DimPlot(seurat, reduction = 'umap', label = TRUE)
    ggsave('umap.png', p1, width=8, height=8)
    
    # Feature plots for top genes
    top_genes <- c('CD3D', 'CD4', 'CD8A', 'MS4A1', 'CD14', 'LYZ')
    p2 <- FeaturePlot(seurat, features = top_genes, reduction = 'umap')
    ggsave('feature_plots.png', p2, width=12, height=8)
    EOF
  '''
}

workflow {
  // Get sample IDs from directory
  samples = channel.from('sample1', 'sample2', 'sample3')
  
  // Cell Ranger
  matrices = CELLRANGER_COUNT(samples, params.fastq)
  
  // Seurat QC
  seurat_objects = SEURAT_QC(samples, matrices)
  
  // Clustering
  clustered = CLUSTERING(seurat_objects)
  
  // DE analysis
  de_results = DIFFERENTIAL_EXPRESSION(clustered)
  
  // Visualization
  VISUALIZATION(clustered)
}
