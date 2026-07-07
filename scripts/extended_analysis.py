#!/usr/bin/env python3
"""
Extended Analysis Module for Advanced Bioinformatics Analysis

Includes advanced statistical methods, multi-omics integration,
and machine learning pipelines.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path

try:
    import scanpy as sc
    import anndata
    HAS_SCANPY = True
except ImportError:
    HAS_SCANPY = False

try:
    from scipy.stats import spearmanr, pearsonr
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    HAS_ML = True
except ImportError:
    HAS_ML = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleCellAnalysis:
    """
    Analysis for single-cell RNA-seq data
    """
    
    def __init__(self, min_genes: int = 200, min_cells: int = 3, mt_threshold: float = 0.1):
        if not HAS_SCANPY:
            raise ImportError("scanpy required for single-cell analysis")
        
        self.min_genes = min_genes
        self.min_cells = min_cells
        self.mt_threshold = mt_threshold
        self.adata = None
    
    def load_h5ad(self, path: str) -> anndata.AnnData:
        """Load h5ad file"""
        logger.info(f"Loading {path}")
        self.adata = sc.read_h5ad(path)
        return self.adata
    
    def basic_qc(self) -> Dict[str, Any]:
        """Quality control for single cells"""
        logger.info("Running basic QC")
        
        adata = self.adata
        
        # Mitochondrial genes
        adata.var['mt'] = adata.var_names.str.startswith('MT-')
        
        # Calculate QC metrics
        sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)
        
        # Filter
        adata = adata[
            (adata.obs['n_genes_by_counts'] > self.min_genes) &
            (adata.obs['pct_counts_mt'] < self.mt_threshold * 100)
        ]
        
        logger.info(f"Cells after QC: {adata.n_obs}")
        self.adata = adata
        
        return {
            'n_cells': adata.n_obs,
            'n_genes': adata.n_vars,
            'mean_counts': float(adata.obs['total_counts'].mean())
        }
    
    def normalize_and_scale(self) -> None:
        """Normalize and scale data"""
        logger.info("Normalizing and scaling")
        
        sc.pp.normalize_total(self.adata, target_sum=1e4)
        sc.pp.log1p(self.adata)
        sc.pp.highly_variable_genes(self.adata)
        sc.pp.scale(self.adata, max_value=10)
    
    def dimensionality_reduction(self, n_comps: int = 50) -> None:
        """PCA and UMAP"""
        logger.info("Running PCA and UMAP")
        
        sc.tl.pca(self.adata, n_comps=n_comps)
        sc.pp.neighbors(self.adata, n_neighbors=15, n_pcs=n_comps)
        sc.tl.umap(self.adata)
    
    def clustering(self, resolution: float = 1.0) -> None:
        """Leiden clustering"""
        logger.info(f"Clustering with resolution {resolution}")
        sc.tl.leiden(self.adata, resolution=resolution)


class MultiOmicsIntegration:
    """
    Integrate multiple omics data types
    """
    
    def __init__(self):
        self.data = {}
    
    def add_omics(self, name: str, df: pd.DataFrame) -> None:
        """Add omics dataset"""
        logger.info(f"Adding {name}: {df.shape}")
        self.data[name] = df
    
    def find_common_samples(self) -> List[str]:
        """Find samples present in all datasets"""
        if not self.data:
            return []
        
        common = set(self.data[list(self.data.keys())[0]].index)
        for name, df in self.data.items():
            common = common.intersection(set(df.index))
        
        return list(common)
    
    def compute_correlations(self) -> pd.DataFrame:
        """Correlate features across omics types"""
        logger.info("Computing cross-omics correlations")
        
        # Get common samples
        common_samples = self.find_common_samples()
        
        correlations = []
        
        for omics1 in self.data.keys():
            for omics2 in self.data.keys():
                if omics1 >= omics2:
                    continue
                
                df1 = self.data[omics1].loc[common_samples]
                df2 = self.data[omics2].loc[common_samples]
                
                # Correlate
                for gene1 in df1.columns[:100]:  # Sample for speed
                    for gene2 in df2.columns[:100]:
                        corr, pval = pearsonr(df1[gene1], df2[gene2])
                        if abs(corr) > 0.7 and pval < 0.05:
                            correlations.append({
                                'feature1': gene1,
                                'omics1': omics1,
                                'feature2': gene2,
                                'omics2': omics2,
                                'correlation': corr,
                                'pvalue': pval
                            })
        
        return pd.DataFrame(correlations)


class AdvancedStatistics:
    """
    Advanced statistical analyses
    """
    
    @staticmethod
    def survival_analysis(time_to_event: pd.Series, event: pd.Series,
                         features: pd.DataFrame) -> Dict[str, Any]:
        """
        Survival analysis (requires lifelines)
        """
        try:
            from lifelines import CoxPHFitter
            
            df = features.copy()
            df['T'] = time_to_event
            df['E'] = event
            
            cph = CoxPHFitter()
            cph.fit(df, duration_col='T', event_col='E')
            
            return {
                'concordance_index': float(cph.concordance_index_),
                'log_likelihood': float(cph.log_likelihood_),
                'aic': float(cph.AIC_partial_),
                'summary': cph.summary.to_dict()
            }
        except ImportError:
            logger.warning("lifelines not installed")
            return {}
    
    @staticmethod
    def permutation_test(group1: np.ndarray, group2: np.ndarray,
                        n_permutations: int = 1000) -> Dict[str, float]:
        """
        Non-parametric permutation test
        """
        observed_diff = np.mean(group1) - np.mean(group2)
        combined = np.concatenate([group1, group2])
        
        perm_diffs = []
        for _ in range(n_permutations):
            perm = np.random.permutation(combined)
            perm_diffs.append(np.mean(perm[:len(group1)]) - np.mean(perm[len(group1):]))
        
        pvalue = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))
        
        return {
            'observed_difference': float(observed_diff),
            'pvalue': float(pvalue),
            'mean_permuted_diff': float(np.mean(perm_diffs))
        }


if __name__ == '__main__':
    # Example: Single-cell analysis
    if HAS_SCANPY:
        sc_analysis = SingleCellAnalysis()
        # sc_analysis.load_h5ad('data.h5ad')
        # sc_analysis.basic_qc()
        # sc_analysis.normalize_and_scale()
        # sc_analysis.dimensionality_reduction()
        # sc_analysis.clustering()
    
    # Example: Multi-omics integration
    integration = MultiOmicsIntegration()
    # integration.add_omics('rnaseq', rna_df)
    # integration.add_omics('proteomics', prot_df)
    # correlations = integration.compute_correlations()
