#!/usr/bin/env python3
"""
Downstream Analysis Module for ChIP-seq, RNA-seq, and TACSEQ

Includes differential analysis, volcano plots, GSEA, and machine learning.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DifferentialAnalysis:
    """
    Perform differential analysis for RNA-seq and ChIP-seq.
    """
    
    def __init__(self, fdr_threshold: float = 0.05, lfc_threshold: float = 1.0):
        self.fdr_threshold = fdr_threshold
        self.lfc_threshold = lfc_threshold
        self.results = None
    
    def rna_seq_deseq2_analysis(self, count_matrix: pd.DataFrame,
                               sample_groups: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Perform DESeq2-style differential expression analysis.
        
        Args:
            count_matrix: Count matrix (genes x samples)
            sample_groups: Dictionary of group assignments
            
        Returns:
            Differential expression results
        """
        logger.info("Performing RNA-seq differential expression analysis")
        
        # Get group assignments
        groups = []
        for col in count_matrix.columns:
            for group, samples in sample_groups.items():
                if col in samples:
                    groups.append(group)
                    break
        
        # Normalize (log2)
        normalized = np.log2(count_matrix + 1)
        
        # Calculate statistics
        results = []
        unique_groups = list(sample_groups.keys())
        
        if len(unique_groups) >= 2:
            group1_cols = [col for i, col in enumerate(count_matrix.columns) if groups[i] == unique_groups[0]]
            group2_cols = [col for i, col in enumerate(count_matrix.columns) if groups[i] == unique_groups[1]]
            
            for gene in count_matrix.index:
                g1_vals = normalized.loc[gene, group1_cols].values
                g2_vals = normalized.loc[gene, group2_cols].values
                
                # T-test
                t_stat, p_val = stats.ttest_ind(g1_vals, g2_vals)
                mean_g1 = g1_vals.mean()
                mean_g2 = g2_vals.mean()
                log2fc = mean_g1 - mean_g2
                
                results.append({
                    'gene': gene,
                    'baseMean': (mean_g1 + mean_g2) / 2,
                    'log2FoldChange': log2fc,
                    'pvalue': p_val,
                    'padj': p_val  # Placeholder for adjusted p-value
                })
        
        self.results = pd.DataFrame(results)
        
        # Adjust p-values (Benjamini-Hochberg)
        from scipy.stats import rankdata
        m = len(self.results)
        sorted_pvals = np.sort(self.results['pvalue'].values)
        adjusted = sorted_pvals * m / (rankdata(sorted_pvals))
        adjusted = np.minimum(adjusted, 1.0)
        
        self.results['padj'] = self.results['pvalue'].values.copy()
        for i, p in enumerate(self.results['pvalue']):
            idx = np.where(sorted_pvals == p)[0][0]
            self.results.loc[i, 'padj'] = adjusted[idx]
        
        logger.info(f"Analysis complete: {len(self.results)} genes tested")
        return self.results
    
    def chip_seq_peak_comparison(self, peaks_group1: pd.DataFrame,
                                peaks_group2: pd.DataFrame) -> pd.DataFrame:
        """
        Compare ChIP-seq peaks between groups.
        
        Args:
            peaks_group1: Peaks for group 1
            peaks_group2: Peaks for group 2
            
        Returns:
            Peak comparison results
        """
        logger.info("Comparing ChIP-seq peaks between groups")
        
        comparison = {
            'group1_peaks': len(peaks_group1),
            'group2_peaks': len(peaks_group2),
            'shared_peaks': len(set(peaks_group1.index) & set(peaks_group2.index)),
            'group1_unique': len(set(peaks_group1.index) - set(peaks_group2.index)),
            'group2_unique': len(set(peaks_group2.index) - set(peaks_group1.index))
        }
        
        return pd.DataFrame([comparison])


class VolcanoPlot:
    """
    Generate volcano plots for visualization of differential analysis.
    """
    
    def __init__(self, fdr_threshold: float = 0.05, lfc_threshold: float = 1.0):
        self.fdr_threshold = fdr_threshold
        self.lfc_threshold = lfc_threshold
    
    def create_volcano_plot(self, de_results: pd.DataFrame,
                          output_path: str = None) -> Tuple[plt.Figure, Dict]:
        """
        Create volcano plot from DE results.
        
        Args:
            de_results: Differential expression results
            output_path: Path to save plot
            
        Returns:
            Figure and summary statistics
        """
        logger.info("Creating volcano plot")
        
        # Calculate -log10(padj)
        de_results['neg_log_padj'] = -np.log10(de_results['padj'] + 1e-300)
        
        # Categorize points
        de_results['color'] = 'gray'
        up_mask = (de_results['log2FoldChange'] > self.lfc_threshold) & (de_results['padj'] < self.fdr_threshold)
        down_mask = (de_results['log2FoldChange'] < -self.lfc_threshold) & (de_results['padj'] < self.fdr_threshold)
        de_results.loc[up_mask, 'color'] = 'red'
        de_results.loc[down_mask, 'color'] = 'blue'
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        scatter = ax.scatter(de_results['log2FoldChange'],
                           de_results['neg_log_padj'],
                           c=de_results['color'],
                           alpha=0.6,
                           s=30)
        
        ax.axhline(-np.log10(self.fdr_threshold), color='k', linestyle='--', alpha=0.3)
        ax.axvline(self.lfc_threshold, color='k', linestyle='--', alpha=0.3)
        ax.axvline(-self.lfc_threshold, color='k', linestyle='--', alpha=0.3)
        
        ax.set_xlabel('log2(Fold Change)')
        ax.set_ylabel('-log10(padj)')
        ax.set_title('Volcano Plot')
        ax.grid(True, alpha=0.3)
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Volcano plot saved to {output_path}")
        
        # Summary statistics
        summary = {
            'upregulated': up_mask.sum(),
            'downregulated': down_mask.sum(),
            'total_significant': (up_mask | down_mask).sum()
        }
        
        return fig, summary


class GSEAAnalysis:
    """
    Perform Gene Set Enrichment Analysis.
    """
    
    def __init__(self, gmt_file: str = None):
        self.gmt_file = gmt_file
        self.results = None
    
    def load_genesets(self, gmt_file: str = None) -> Dict[str, List[str]]:
        """
        Load gene sets from GMT file.
        
        Args:
            gmt_file: Path to GMT file
            
        Returns:
            Dictionary of gene sets
        """
        genesets = {}
        
        if gmt_file is None:
            gmt_file = self.gmt_file
        
        if gmt_file and Path(gmt_file).exists():
            with open(gmt_file) as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        geneset_name = parts[0]
                        genes = parts[2:]
                        genesets[geneset_name] = genes
        
        logger.info(f"Loaded {len(genesets)} gene sets")
        return genesets
    
    def hypergeometric_test(self, de_genes: List[str],
                          geneset: List[str],
                          background_size: int = 20000) -> Dict[str, float]:
        """
        Perform hypergeometric test for enrichment.
        
        Args:
            de_genes: List of differentially expressed genes
            geneset: Gene set to test
            background_size: Total number of genes
            
        Returns:
            Statistical results
        """
        overlap = len(set(de_genes) & set(geneset))
        
        # Hypergeometric test
        from scipy.stats import hypergeom
        
        M = background_size  # Total genes
        n = len(geneset)  # Genes in geneset
        N = len(de_genes)  # DE genes
        
        pvalue = hypergeom.sf(overlap - 1, M, n, N)
        
        return {
            'overlap': overlap,
            'pvalue': float(pvalue),
            'expected': float(n * N / M)
        }
    
    def run_gsea(self, de_results: pd.DataFrame,
                genesets: Dict[str, List[str]] = None) -> pd.DataFrame:
        """
        Run GSEA analysis.
        
        Args:
            de_results: Differential expression results
            genesets: Gene sets to test
            
        Returns:
            GSEA results
        """
        if genesets is None:
            genesets = self.load_genesets()
        
        logger.info(f"Running GSEA for {len(genesets)} gene sets")
        
        # Sort genes by fold change
        ranked_genes = de_results.sort_values('log2FoldChange', ascending=False)['gene'].tolist()
        
        results = []
        for geneset_name, genes in genesets.items():
            # Calculate enrichment score
            ranked_indices = [ranked_genes.index(g) if g in ranked_genes else len(ranked_genes)
                            for g in genes if g in ranked_genes]
            
            if ranked_indices:
                es = len(genes) / len(ranked_genes)  # Simplified ES
                pval = self.hypergeometric_test(de_results['gene'].tolist(), genes)['pvalue']
                
                results.append({
                    'geneset': geneset_name,
                    'size': len(genes),
                    'enrichment_score': es,
                    'pvalue': pval,
                    'padj': pval  # Placeholder
                })
        
        self.results = pd.DataFrame(results)
        return self.results


class MachineLearningAnalysis:
    """
    Machine learning for biomarker discovery and prediction.
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
    
    def feature_selection_rf(self, X: pd.DataFrame, y: pd.Series,
                            n_features: int = 100) -> Tuple[List[str], List[float]]:
        """
        Select features using Random Forest importance.
        
        Args:
            X: Feature matrix
            y: Target variable
            n_features: Number of features to select
            
        Returns:
            Selected features and importance scores
        """
        logger.info(f"Selecting {n_features} features using Random Forest")
        
        # Handle categorical target
        y_encoded = pd.factorize(y)[0] if y.dtype == 'object' else y
        
        # Train RF
        rf = RandomForestClassifier(n_estimators=100, random_state=self.random_state)
        rf.fit(X, y_encoded)
        
        # Get feature importance
        importances = rf.feature_importances_
        indices = np.argsort(importances)[::-1][:n_features]
        selected_features = X.columns[indices].tolist()
        scores = importances[indices]
        
        logger.info(f"Selected {len(selected_features)} features")
        return selected_features, scores
    
    def clustering_analysis(self, X: pd.DataFrame,
                          method: str = 'kmeans',
                          n_clusters: int = None) -> Tuple[np.ndarray, Dict]:
        """
        Perform clustering analysis.
        
        Args:
            X: Feature matrix
            method: Clustering method
            n_clusters: Number of clusters
            
        Returns:
            Cluster assignments and metrics
        """
        logger.info(f"Performing {method} clustering")
        
        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        if n_clusters is None:
            # Elbow method
            inertias = []
            for k in range(2, min(11, len(X))):
                km = KMeans(n_clusters=k, random_state=self.random_state)
                km.fit(X_scaled)
                inertias.append(km.inertia_)
            n_clusters = np.argmin(np.diff(inertias)) + 2
        
        # Cluster
        km = KMeans(n_clusters=n_clusters, random_state=self.random_state)
        clusters = km.fit_predict(X_scaled)
        
        metrics = {
            'n_clusters': int(n_clusters),
            'inertia': float(km.inertia_),
            'silhouette_score': float(np.mean([np.sum(clusters == i) for i in range(n_clusters)]))
        }
        
        return clusters, metrics
    
    def survival_prediction(self, X: pd.DataFrame,
                          survival_time: pd.Series,
                          event: pd.Series) -> Dict[str, Any]:
        """
        Build survival prediction model.
        
        Args:
            X: Feature matrix
            survival_time: Survival time
            event: Event indicator
            
        Returns:
            Model results
        """
        logger.info("Building survival prediction model")
        
        try:
            from lifelines import CoxPHFitter
            
            # Prepare data
            df = X.copy()
            df['T'] = survival_time
            df['E'] = event
            
            # Fit Cox model
            cph = CoxPHFitter()
            cph.fit(df, duration_col='T', event_col='E')
            
            # Extract results
            results = {
                'concordance_index': float(cph.concordance_index_),
                'covariate_count': len(cph.params_),
                'log_likelihood': float(cph.log_likelihood_)
            }
            
        except ImportError:
            logger.warning("Lifelines not installed, using simplified model")
            results = {'status': 'Survival analysis not available'}
        
        return results


class AnalysisPipeline:
    """
    Orchestrate complete downstream analysis.
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
    
    def run_complete_analysis(self, count_matrix: pd.DataFrame,
                            metadata: pd.DataFrame,
                            analysis_type: str = 'rnaseq') -> Dict[str, Any]:
        """
        Run complete downstream analysis pipeline.
        
        Args:
            count_matrix: Expression or count matrix
            metadata: Sample metadata
            analysis_type: Type of analysis (rnaseq, chipseq, tacseq)
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting {analysis_type} downstream analysis")
        
        # Differential analysis
        de_analyzer = DifferentialAnalysis()
        sample_groups = self._get_sample_groups(metadata)
        de_results = de_analyzer.rna_seq_deseq2_analysis(count_matrix, sample_groups)
        de_results.to_csv(self.output_dir / 'de_results.csv')
        
        # Volcano plot
        volcano = VolcanoPlot()
        fig, volcano_summary = volcano.create_volcano_plot(
            de_results,
            str(self.output_dir / 'volcano_plot.png')
        )
        plt.close(fig)
        
        # GSEA
        gsea = GSEAAnalysis()
        gsea_results = gsea.run_gsea(de_results)
        gsea_results.to_csv(self.output_dir / 'gsea_results.csv')
        
        # Machine learning
        ml = MachineLearningAnalysis()
        selected_features, importance_scores = ml.feature_selection_rf(
            count_matrix,
            metadata['condition'] if 'condition' in metadata.columns else pd.Series([0] * len(count_matrix.columns))
        )
        
        clusters, cluster_metrics = ml.clustering_analysis(
            count_matrix[selected_features]
        )
        
        # Compile results
        self.results = {
            'analysis_type': analysis_type,
            'de_summary': {
                'significant': (de_results['padj'] < 0.05).sum(),
                'upregulated': ((de_results['log2FoldChange'] > 1) & (de_results['padj'] < 0.05)).sum(),
                'downregulated': ((de_results['log2FoldChange'] < -1) & (de_results['padj'] < 0.05)).sum()
            },
            'volcano_summary': volcano_summary,
            'gsea_results_count': len(gsea_results),
            'ml_results': {
                'selected_features': len(selected_features),
                'clusters': cluster_metrics
            }
        }
        
        # Save results
        with open(self.output_dir / 'analysis_summary.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("Analysis complete")
        return self.results
    
    def _get_sample_groups(self, metadata: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Extract sample groups from metadata.
        """
        groups = {}
        
        if 'condition' in metadata.columns:
            for condition in metadata['condition'].unique():
                groups[condition] = metadata[metadata['condition'] == condition].index.tolist()
        
        return groups if groups else {'group1': metadata.index.tolist()}


if __name__ == '__main__':
    # Example usage
    output_dir = 'results/downstream'
    
    pipeline = AnalysisPipeline(output_dir)
    
    # Create sample data
    count_matrix = pd.DataFrame(
        np.random.randint(0, 100, (1000, 20)),
        columns=[f'sample_{i}' for i in range(20)],
        index=[f'gene_{i}' for i in range(1000)]
    )
    
    metadata = pd.DataFrame({
        'condition': ['control'] * 10 + ['treatment'] * 10
    }, index=[f'sample_{i}' for i in range(20)])
    
    results = pipeline.run_complete_analysis(count_matrix, metadata, 'rnaseq')
    print(json.dumps(results, indent=2))
