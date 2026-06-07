"""
Omics Results Visualization Dashboard
Visualizes results from WES, ChIP-seq, RNA-seq, and TACSEQ pipelines
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Omics Results Visualizer",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .omics-section {
        border-left: 5px solid;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }
    .wes-section { border-left-color: #1f77b4; background-color: #f0f4ff; }
    .chipseq-section { border-left-color: #ff7f0e; background-color: #fff5f0; }
    .rnaseq-section { border-left-color: #2ca02c; background-color: #f0fff0; }
    .tacseq-section { border-left-color: #d62728; background-color: #fff0f0; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results_dir' not in st.session_state:
    st.session_state.results_dir = Path("./results")

# Sidebar navigation
st.sidebar.title("🧬 Omics Visualizer")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select View",
    options=["Dashboard", "WES Analysis", "ChIP-seq Analysis", "RNA-seq Analysis", "TACSEQ Analysis", "Comparative Analysis"],
    help="Choose an omics analysis to visualize"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Settings")
results_dir = st.sidebar.text_input(
    "Results Directory",
    value=str(st.session_state.results_dir),
    help="Path to pipeline results"
)
st.session_state.results_dir = Path(results_dir)

show_raw_data = st.sidebar.checkbox("Show Raw Data", value=False)

# Helper functions
@st.cache_data
def load_sample_wes_data():
    """Load or generate sample WES data"""
    return pd.DataFrame({
        'Variant': [f'chr{i}_pos_{j}' for i in range(1, 23) for j in range(5)],
        'Chromosome': [f'chr{i}' for i in range(1, 23) for _ in range(5)],
        'Quality': np.random.choice([20, 25, 30, 35, 40], 110),
        'Depth': np.random.randint(10, 200, 110),
        'Allele_Freq': np.random.uniform(0, 1, 110),
        'Type': np.random.choice(['SNP', 'INDEL', 'SV'], 110)
    })

@st.cache_data
def load_sample_chipseq_data():
    """Load or generate sample ChIP-seq data"""
    return pd.DataFrame({
        'Peak_ID': [f'peak_{i}' for i in range(500)],
        'Chromosome': np.random.choice([f'chr{i}' for i in range(1, 23)], 500),
        'Start': np.random.randint(0, 3e8, 500),
        'End': np.random.randint(0, 3e8, 500),
        'Peak_Score': np.random.exponential(scale=100, size=500),
        'P_Value': np.random.uniform(1e-50, 1e-5, 500),
        'Fold_Change': np.random.exponential(scale=5, size=500)
    })

@st.cache_data
def load_sample_rnaseq_data():
    """Load or generate sample RNA-seq data"""
    np.random.seed(42)
    n_genes = 20000
    return pd.DataFrame({
        'Gene_ID': [f'ENSG{str(i).zfill(11)}' for i in range(n_genes)],
        'Gene_Name': [f'Gene_{i}' for i in range(n_genes)],
        'Log2FC': np.random.normal(0, 1.5, n_genes),
        'P_Value': np.random.exponential(scale=0.01, size=n_genes),
        'Adjusted_P_Value': np.random.exponential(scale=0.01, size=n_genes),
        'Base_Mean': np.random.exponential(scale=100, size=n_genes),
        'Expression_Level': np.random.choice(['Low', 'Medium', 'High'], n_genes)
    })

@st.cache_data
def load_sample_tacseq_data():
    """Load or generate sample TACSEQ data"""
    return pd.DataFrame({
        'Region_ID': [f'region_{i}' for i in range(1000)],
        'Chromosome': np.random.choice([f'chr{i}' for i in range(1, 23)], 1000),
        'Accessibility': np.random.uniform(0, 1, 1000),
        'Temporal_Score': np.random.normal(0, 0.5, 1000),
        'Dynamic_Change': np.random.choice(['Stable', 'Opening', 'Closing'], 1000),
        'Peak_Height': np.random.exponential(scale=50, size=1000)
    })

# Dashboard Page
if page == "Dashboard":
    st.title("🧬 Multi-Omics Results Dashboard")
    st.markdown("Comprehensive visualization of WES, ChIP-seq, RNA-seq, and TACSEQ pipeline results")
    
    # Create columns for overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h3>WES</h3>
        <p><strong>Whole Exome Sequencing</strong></p>
        <small>Variant Calling & Annotation</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h3>ChIP-seq</h3>
        <p><strong>ChIP Sequencing</strong></p>
        <small>Peak Calling & Motif Discovery</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h3>RNA-seq</h3>
        <p><strong>RNA Sequencing</strong></p>
        <small>Expression & Differential Analysis</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
        <h3>TACSEQ</h3>
        <p><strong>Temporal Accessibility</strong></p>
        <small>Chromatin Dynamics</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load sample data
    wes_data = load_sample_wes_data()
    chipseq_data = load_sample_chipseq_data()
    rnaseq_data = load_sample_rnaseq_data()
    tacseq_data = load_sample_tacseq_data()
    
    # Overview statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("WES Variants", len(wes_data), "variants called")
    with col2:
        st.metric("ChIP-seq Peaks", len(chipseq_data), "peaks detected")
    with col3:
        st.metric("RNA-seq Genes", len(rnaseq_data), "genes analyzed")
    with col4:
        st.metric("TACSEQ Regions", len(tacseq_data), "regions analyzed")

# WES Analysis Page
elif page == "WES Analysis":
    st.title("🧬 WES (Whole Exome Sequencing) Analysis")
    
    wes_data = load_sample_wes_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Variant Type Distribution")
        variant_counts = wes_data['Type'].value_counts()
        fig = px.pie(
            values=variant_counts.values,
            names=variant_counts.index,
            title="Variants by Type",
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Quality Score Distribution")
        fig = px.histogram(
            wes_data,
            x='Quality',
            nbins=20,
            title="Quality Score Distribution",
            labels={'Quality': 'QUAL Score'},
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Depth vs Allele Frequency")
        fig = px.scatter(
            wes_data,
            x='Depth',
            y='Allele_Freq',
            color='Type',
            title="Depth vs Allele Frequency",
            labels={'Depth': 'Read Depth', 'Allele_Freq': 'Allele Frequency'},
            hover_data=['Quality']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Variants by Chromosome")
        chrom_counts = wes_data['Chromosome'].value_counts().sort_index()
        fig = px.bar(
            x=chrom_counts.index,
            y=chrom_counts.values,
            title="Variant Count by Chromosome",
            labels={'x': 'Chromosome', 'y': 'Count'},
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if show_raw_data:
        st.subheader("Raw WES Data")
        st.dataframe(wes_data, use_container_width=True)

# ChIP-seq Analysis Page
elif page == "ChIP-seq Analysis":
    st.title("📊 ChIP-seq Analysis")
    
    chipseq_data = load_sample_chipseq_data()
    
    # Add -log10(p-value) for volcano plot
    chipseq_data['Log10_Pval'] = -np.log10(chipseq_data['P_Value'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Volcano Plot")
        # Color by fold change threshold
        colors = ['#d62728' if (fc > 2 and lp > -np.log10(0.05)) else '#1f77b4' 
                  for fc, lp in zip(chipseq_data['Fold_Change'], chipseq_data['Log10_Pval'])]
        
        fig = px.scatter(
            chipseq_data,
            x='Fold_Change',
            y='Log10_Pval',
            title="Volcano Plot",
            labels={'Fold_Change': 'Log2 Fold Change', 'Log10_Pval': '-log10(p-value)'},
            hover_data=['Peak_ID', 'Peak_Score']
        )
        fig.add_hline(y=-np.log10(0.05), line_dash="dash", line_color="red", annotation_text="p=0.05")
        fig.add_vline(x=2, line_dash="dash", line_color="red")
        fig.add_vline(x=-2, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Peak Score Distribution")
        fig = px.histogram(
            chipseq_data,
            x='Peak_Score',
            nbins=30,
            title="Peak Score Distribution",
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Peaks by Chromosome")
        chrom_counts = chipseq_data['Chromosome'].value_counts().sort_index()
        fig = px.bar(
            x=chrom_counts.index,
            y=chrom_counts.values,
            title="Peak Count by Chromosome",
            labels={'x': 'Chromosome', 'y': 'Count'},
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Fold Change vs P-Value")
        fig = px.scatter(
            chipseq_data,
            x='Fold_Change',
            y='P_Value',
            title="Fold Change vs P-Value",
            labels={'Fold_Change': 'Fold Change', 'P_Value': 'P-Value'},
            log_y=True,
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if show_raw_data:
        st.subheader("Raw ChIP-seq Data")
        st.dataframe(chipseq_data, use_container_width=True)

# RNA-seq Analysis Page
elif page == "RNA-seq Analysis":
    st.title("📈 RNA-seq Analysis")
    
    rnaseq_data = load_sample_rnaseq_data()
    
    # Add -log10(p-value) for volcano plot
    rnaseq_data['Log10_Padj'] = -np.log10(rnaseq_data['Adjusted_P_Value'] + 1e-300)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("MA Plot")
        fig = px.scatter(
            rnaseq_data,
            x='Base_Mean',
            y='Log2FC',
            title="MA Plot (M vs A)",
            labels={'Base_Mean': 'A: log2(mean expression)', 'Log2FC': 'M: log2(fold change)'},
            log_x=True,
            hover_data=['Gene_Name'],
            color_discrete_sequence=['#2ca02c']
        )
        fig.add_hline(y=1, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=-1, line_dash="dash", line_color="red", opacity=0.5)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Volcano Plot")
        fig = px.scatter(
            rnaseq_data,
            x='Log2FC',
            y='Log10_Padj',
            title="Volcano Plot",
            labels={'Log2FC': 'log2(Fold Change)', 'Log10_Padj': '-log10(Adjusted p-value)'},
            hover_data=['Gene_Name'],
            color_discrete_sequence=['#2ca02c']
        )
        fig.add_hline(y=-np.log10(0.05), line_dash="dash", line_color="red")
        fig.add_vline(x=1, line_dash="dash", line_color="red")
        fig.add_vline(x=-1, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expression Level Distribution")
        expr_counts = rnaseq_data['Expression_Level'].value_counts()
        fig = px.bar(
            x=expr_counts.index,
            y=expr_counts.values,
            title="Gene Expression Levels",
            labels={'x': 'Expression Level', 'y': 'Gene Count'},
            color_discrete_sequence=['#2ca02c']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Log2FC Distribution")
        fig = px.histogram(
            rnaseq_data,
            x='Log2FC',
            nbins=50,
            title="Log2 Fold Change Distribution",
            color_discrete_sequence=['#2ca02c']
        )
        fig.add_vline(x=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    if show_raw_data:
        st.subheader("Raw RNA-seq Data")
        st.dataframe(rnaseq_data.head(100), use_container_width=True)

# TACSEQ Analysis Page
elif page == "TACSEQ Analysis":
    st.title("🔍 TACSEQ (Temporal Accessibility) Analysis")
    
    tacseq_data = load_sample_tacseq_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Accessibility Score Distribution")
        fig = px.histogram(
            tacseq_data,
            x='Accessibility',
            nbins=30,
            title="Chromatin Accessibility Distribution",
            labels={'Accessibility': 'Accessibility Score'},
            color_discrete_sequence=['#d62728']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Dynamic Change Classification")
        dynamic_counts = tacseq_data['Dynamic_Change'].value_counts()
        fig = px.pie(
            values=dynamic_counts.values,
            names=dynamic_counts.index,
            title="Temporal Dynamics",
            color_discrete_sequence=['#d62728', '#1f77b4', '#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Accessibility vs Temporal Score")
        fig = px.scatter(
            tacseq_data,
            x='Accessibility',
            y='Temporal_Score',
            color='Dynamic_Change',
            title="Accessibility vs Temporal Score",
            labels={'Accessibility': 'Chromatin Accessibility', 'Temporal_Score': 'Temporal Score'},
            hover_data=['Region_ID']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Peak Height by Chromosome")
        chrom_heights = tacseq_data.groupby('Chromosome')['Peak_Height'].mean().sort_index()
        fig = px.bar(
            x=chrom_heights.index,
            y=chrom_heights.values,
            title="Mean Peak Height by Chromosome",
            labels={'x': 'Chromosome', 'y': 'Mean Peak Height'},
            color_discrete_sequence=['#d62728']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if show_raw_data:
        st.subheader("Raw TACSEQ Data")
        st.dataframe(tacseq_data.head(100), use_container_width=True)

# Comparative Analysis Page
elif page == "Comparative Analysis":
    st.title("🔄 Comparative Multi-Omics Analysis")
    
    wes_data = load_sample_wes_data()
    chipseq_data = load_sample_chipseq_data()
    rnaseq_data = load_sample_rnaseq_data()
    tacseq_data = load_sample_tacseq_data()
    
    st.subheader("Pipeline Summary Statistics")
    
    summary_data = {
        'Pipeline': ['WES', 'ChIP-seq', 'RNA-seq', 'TACSEQ'],
        'Total Features': [len(wes_data), len(chipseq_data), len(rnaseq_data), len(tacseq_data)],
        'Significant Features': [
            len(wes_data[wes_data['Quality'] > 30]),
            len(chipseq_data[chipseq_data['Fold_Change'] > 2]),
            len(rnaseq_data[rnaseq_data['Log2FC'].abs() > 1]),
            len(tacseq_data[tacseq_data['Accessibility'] > 0.5])
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            summary_df,
            x='Pipeline',
            y='Total Features',
            title="Total Features by Pipeline",
            labels={'Total Features': 'Feature Count'},
            color='Pipeline',
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            summary_df,
            x='Pipeline',
            y='Significant Features',
            title="Significant Features by Pipeline",
            labels={'Significant Features': 'Significant Count'},
            color='Pipeline',
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(summary_df, use_container_width=True)
    
    st.subheader("Cross-Omics Correlation")
    st.markdown("""
    This section would display correlations between features across different omics types:
    - Genes with ChIP-seq peaks
    - RNA expression vs chromatin accessibility
    - Temporal accessibility changes vs gene expression changes
    - Genetic variants in regulatory regions
    """)
    
    # Create a simple correlation heatmap simulation
    corr_matrix = np.random.uniform(0, 1, (4, 4))
    np.fill_diagonal(corr_matrix, 1)
    
    fig = px.imshow(
        corr_matrix,
        x=['WES', 'ChIP-seq', 'RNA-seq', 'TACSEQ'],
        y=['WES', 'ChIP-seq', 'RNA-seq', 'TACSEQ'],
        color_continuous_scale='RdBu_r',
        title="Multi-Omics Correlation Matrix",
        labels=dict(color="Correlation")
    )
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: small;">
    <p>Omics Results Visualizer | Multi-Omics Data Pipeline</p>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)
