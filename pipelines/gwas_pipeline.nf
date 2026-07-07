#!/usr/bin/env nextflow

/*
 * GWAS (Genome-Wide Association Studies) Pipeline
 * Performs association analysis between genetic variants and phenotypic traits
 */

params.vcf = 'data/*.vcf.gz'
params.phenotype = 'data/phenotype.txt'
params.covariate = null
params.output = 'results/gwas'
params.threads = 4
params.maf_threshold = 0.05
params.hwe_pval = 0.001
params.ld_window = 100

process VCF_QC {
  tag "${vcf.simpleName}"
  container 'vcftools/vcftools:latest'
  
  input:
    path vcf
  
  output:
    path "${vcf.simpleName}_qc.vcf.gz"
  
  script:
  '''
    # Filter by MAF and HWE
    vcftools --gzvcf $vcf \
      --maf $params.maf_threshold \
      --hwe $params.hwe_pval \
      --recode --stdout | gzip > ${vcf.simpleName}_qc.vcf.gz
    
    # Index
    tabix -p vcf ${vcf.simpleName}_qc.vcf.gz
  '''
}

process VCF_TO_PLINK {
  tag "${vcf.simpleName}"
  container 'plink2:latest'
  
  input:
    path vcf
  
  output:
    tuple path('*.bed'), path('*.bim'), path('*.fam')
  
  script:
  '''
    plink2 --vcf $vcf --make-bed --out genotypes
  '''
}

process LD_PRUNE {
  container 'plink2:latest'
  
  input:
    tuple path(bed), path(bim), path(fam)
  
  output:
    tuple path('*.bed'), path('*.bim'), path('*.fam')
  
  script:
  '''
    plink2 --bed $bed --bim $bim --fam $fam \
      --indep-pairwise $params.ld_window 50 0.5 \
      --make-bed --out pruned
  '''
}

process ASSOCIATION_TEST {
  tag "linear_or_logistic"
  container 'plink2:latest'
  
  input:
    tuple path(bed), path(bim), path(fam)
    path phenotype
    path covariate
  
  output:
    path 'associations.txt'
  
  script:
  def cov_flag = covariate ? "--covar $covariate" : ""
  '''
    plink2 --bed $bed --bim $bim --fam $fam \
      --pheno $phenotype \
      $cov_flag \
      --glm hide-covar --adjust \
      --out associations
  '''
}

process MANHATTAN_PLOT {
  container 'r-base:latest'
  
  input:
    path associations
  
  output:
    path 'manhattan.png'
  
  script:
  '''
    Rscript - <<EOF
    library(ggplot2)
    data <- read.table('$associations', header=TRUE)
    
    # Manhattan plot
    p <- ggplot(data, aes(x=BP, y=-log10(P))) +
      facet_wrap(~CHR) +
      geom_point() +
      theme_minimal()
    
    ggsave('manhattan.png', p, width=12, height=6)
    EOF
  '''
}

process QQ_PLOT {
  container 'r-base:latest'
  
  input:
    path associations
  
  output:
    path 'qq_plot.png'
  
  script:
  '''
    Rscript - <<EOF
    library(ggplot2)
    data <- read.table('$associations', header=TRUE)
    
    # QQ plot
    observed <- sort(data\$P)
    expected <- ppoints(length(observed))
    
    p <- ggplot(data.frame(expected=-log10(expected), observed=-log10(observed)),
                aes(x=expected, y=observed)) +
      geom_point() +
      geom_abline(slope=1, intercept=0, color='red') +
      theme_minimal()
    
    ggsave('qq_plot.png', p, width=6, height=6)
    EOF
  '''
}

workflow {
  vcf_files = channel.fromPath(params.vcf)
  
  // QC
  qc_vcfs = VCF_QC(vcf_files)
  
  // Convert to PLINK format
  plink_files = VCF_TO_PLINK(qc_vcfs)
  
  // LD pruning
  pruned_files = LD_PRUNE(plink_files)
  
  // Association testing
  pheno = file(params.phenotype)
  cov = params.covariate ? file(params.covariate) : null
  results = ASSOCIATION_TEST(pruned_files, pheno, cov)
  
  // Visualization
  MANHATTAN_PLOT(results)
  QQ_PLOT(results)
}
