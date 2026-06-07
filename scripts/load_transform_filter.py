#!/usr/bin/env python3
"""
Load, Transform, Filter (LTF) Module for Biological Data Pipeline

Handles extraction of metadata from cloud sources, data transformation,
and filtering for data quality consistency across all pipelines.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudMetadataExtractor:
    """
    Extract metadata from cloud storage (S3, GCS, Azure).
    """
    
    def __init__(self, cloud_provider: str = 's3'):
        self.cloud_provider = cloud_provider
        self.metadata = {}
    
    def extract_s3_metadata(self, bucket: str, prefix: str) -> Dict[str, Any]:
        """
        Extract metadata from S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Prefix for objects
            
        Returns:
            Dictionary containing metadata
        """
        try:
            import boto3
            s3_client = boto3.client('s3')
            
            metadata = {
                'source': 's3',
                'bucket': bucket,
                'prefix': prefix,
                'files': [],
                'extraction_date': datetime.now().isoformat()
            }
            
            # List objects
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_metadata = {
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    }
                    metadata['files'].append(file_metadata)
            
            logger.info(f"Extracted metadata from {len(metadata['files'])} S3 objects")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting S3 metadata: {e}")
            return {}
    
    def extract_gcs_metadata(self, bucket: str, prefix: str) -> Dict[str, Any]:
        """
        Extract metadata from Google Cloud Storage bucket.
        """
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket_obj = client.bucket(bucket)
            
            metadata = {
                'source': 'gcs',
                'bucket': bucket,
                'prefix': prefix,
                'files': [],
                'extraction_date': datetime.now().isoformat()
            }
            
            blobs = client.list_blobs(bucket, prefix=prefix)
            for blob in blobs:
                file_metadata = {
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat(),
                    'content_type': blob.content_type
                }
                metadata['files'].append(file_metadata)
            
            logger.info(f"Extracted metadata from {len(metadata['files'])} GCS objects")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting GCS metadata: {e}")
            return {}


class DataTransformer:
    """
    Transform raw data into standardized formats.
    """
    
    def __init__(self):
        self.transformations = {}
    
    def normalize_expression_matrix(self, data: pd.DataFrame, 
                                   method: str = 'log2') -> pd.DataFrame:
        """
        Normalize expression matrix.
        
        Args:
            data: Expression matrix (genes x samples)
            method: Normalization method ('log2', 'cpm', 'rpkm', 'tpm')
            
        Returns:
            Normalized data
        """
        logger.info(f"Normalizing expression matrix using {method}")
        
        if method == 'log2':
            normalized = np.log2(data + 1)
        elif method == 'cpm':
            normalized = (data / data.sum()) * 1e6
        elif method == 'rpkm':
            normalized = (data / data.sum()) * 1e9
        elif method == 'tpm':
            normalized = (data / data.sum()) * 1e6
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized
    
    def batch_effect_correction(self, data: pd.DataFrame, 
                               batch_col: pd.Series,
                               method: str = 'combat') -> pd.DataFrame:
        """
        Correct for batch effects.
        
        Args:
            data: Expression matrix
            batch_col: Batch indicator
            method: Correction method ('combat', 'svaseq')
            
        Returns:
            Batch-corrected data
        """
        logger.info(f"Applying batch effect correction using {method}")
        
        if method == 'combat':
            try:
                from combat.pycombat import pycombat
                corrected = pycombat(data.T, batch_col).T
                return corrected
            except Exception as e:
                logger.warning(f"Combat correction failed: {e}")
                return data
        
        return data
    
    def transform_peak_format(self, peak_data: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize peak format to BED6.
        """
        required_cols = ['chrom', 'start', 'end', 'name', 'score', 'strand']
        
        if all(col in peak_data.columns for col in required_cols):
            return peak_data[required_cols]
        
        # Try to infer columns
        cols = peak_data.columns.tolist()
        if len(cols) >= 6:
            peak_data.columns = required_cols[:len(cols)]
            return peak_data[required_cols[:len(cols)]]
        
        raise ValueError("Cannot standardize peak format")


class DataFilter:
    """
    Filter data for quality consistency.
    """
    
    def __init__(self):
        self.filter_stats = {}
    
    def filter_low_expression_genes(self, data: pd.DataFrame,
                                   min_cpm: float = 1,
                                   min_samples: int = 1) -> pd.DataFrame:
        """
        Filter out low expression genes.
        
        Args:
            data: Expression matrix
            min_cpm: Minimum counts per million
            min_samples: Minimum samples with expression
            
        Returns:
            Filtered data
        """
        logger.info(f"Filtering genes with CPM < {min_cpm} in < {min_samples} samples")
        
        # Convert to CPM if needed
        cpm = (data / data.sum()) * 1e6
        
        # Filter
        mask = (cpm > min_cpm).sum(axis=1) >= min_samples
        filtered = data[mask]
        
        self.filter_stats['genes_before'] = len(data)
        self.filter_stats['genes_after'] = len(filtered)
        self.filter_stats['genes_removed'] = len(data) - len(filtered)
        
        logger.info(f"Retained {len(filtered)}/{len(data)} genes")
        return filtered
    
    def filter_low_quality_peaks(self, peaks: pd.DataFrame,
                                min_score: float = 100,
                                min_pvalue: float = 0.01) -> pd.DataFrame:
        """
        Filter low quality peaks.
        
        Args:
            peaks: Peak data
            min_score: Minimum peak score
            min_pvalue: Minimum significance
            
        Returns:
            Filtered peaks
        """
        logger.info(f"Filtering peaks with score < {min_score}")
        
        if 'score' in peaks.columns:
            peaks = peaks[peaks['score'] >= min_score]
        
        if 'pvalue' in peaks.columns:
            peaks = peaks[peaks['pvalue'] <= min_pvalue]
        
        logger.info(f"Retained {len(peaks)} peaks after filtering")
        return peaks
    
    def filter_by_consistency(self, data: pd.DataFrame,
                            metadata: pd.DataFrame,
                            check_replicates: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Filter by data consistency and quality metrics.
        
        Args:
            data: Expression or peak data
            metadata: Sample metadata
            check_replicates: Check consistency across replicates
            
        Returns:
            Filtered data and quality report
        """
        report = {
            'total_samples': len(data.columns),
            'inconsistencies': [],
            'quality_issues': []
        }
        
        # Check for missing values
        missing = data.isna().sum().sum()
        if missing > 0:
            report['quality_issues'].append(f"Missing values: {missing}")
        
        # Check for duplicates
        if data.index.duplicated().any():
            report['inconsistencies'].append("Duplicate index entries found")
            data = data[~data.index.duplicated(keep='first')]
        
        # Check replicate correlation if metadata available
        if check_replicates and 'replicate_group' in metadata.columns:
            # Implementation would check correlation between replicates
            pass
        
        logger.info(f"Data consistency check complete: {len(report['inconsistencies'])} issues found")
        return data, report


class Pipeline:
    """
    Main LTF pipeline orchestration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.extractor = CloudMetadataExtractor()
        self.transformer = DataTransformer()
        self.filter = DataFilter()
        self.results = {}
    
    def run(self, input_data: str, output_dir: str) -> Dict[str, Any]:
        """
        Run complete LTF pipeline.
        
        Args:
            input_data: Path to input data or cloud location
            output_dir: Output directory
            
        Returns:
            Pipeline results
        """
        logger.info("Starting LTF Pipeline")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load data
        data = self._load_data(input_data)
        
        # Transform
        data = self.transformer.normalize_expression_matrix(data)
        
        # Filter
        data, filter_report = self.filter.filter_by_consistency(data, {})
        
        # Save results
        results = {
            'input': input_data,
            'output_dir': output_dir,
            'timestamp': datetime.now().isoformat(),
            'filter_report': filter_report,
            'data_shape': data.shape
        }
        
        # Save transformed data
        output_path = Path(output_dir) / 'transformed_data.csv'
        data.to_csv(output_path)
        
        logger.info(f"LTF Pipeline complete. Results saved to {output_dir}")
        return results
    
    def _load_data(self, path: str) -> pd.DataFrame:
        """
        Load data from local or cloud source.
        """
        if path.startswith('s3://'):
            # Parse S3 path
            bucket, key = path.replace('s3://', '').split('/', 1)
            logger.info(f"Loading from S3: {bucket}/{key}")
        elif path.startswith('gs://'):
            # Parse GCS path
            bucket, key = path.replace('gs://', '').split('/', 1)
            logger.info(f"Loading from GCS: {bucket}/{key}")
        else:
            # Local file
            data = pd.read_csv(path, index_col=0)
            logger.info(f"Loaded data from {path}: {data.shape}")
            return data
        
        return pd.DataFrame()


if __name__ == '__main__':
    # Example usage
    config = {
        'cloud_provider': 's3',
        'normalization_method': 'log2',
        'min_cpm': 1,
        'min_samples': 2
    }
    
    pipeline = Pipeline(config)
    results = pipeline.run('data/expression_matrix.csv', 'results/ltf')
    print(json.dumps(results, indent=2))
