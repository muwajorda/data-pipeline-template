import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Title for the app
st.title("NGS Analysis Results Visualization")

# Upload Data
uploaded_file = st.file_uploader("Upload your NGS results CSV file", type=["csv"])

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    
    # Display data
    st.write("Data Overview")
    st.dataframe(data)

    # QC Metrics Visualization
    st.header("Quality Control Metrics")
    if 'qc_metric' in data.columns:
        plt.figure(figsize=(10, 5))
        plt.plot(data['qc_metric'])
        plt.title("QC Metrics")
        plt.xlabel("Sample")
        plt.ylabel("QC Metric Value")
        st.pyplot(plt)

    # Alignment Stats Visualization
    st.header("Alignment Statistics")
    if 'alignment_stat' in data.columns:
        plt.figure(figsize=(10, 5))
        plt.bar(data['sample'], data['alignment_stat'])
        plt.title("Alignment Statistics")
        plt.xlabel("Sample")
        plt.ylabel("Alignment Stat Value")
        st.pyplot(plt)
    
    # Expression Data Visualization
    st.header("Expression Data")
    if 'expression_data' in data.columns:
        st.line_chart(data.set_index('sample')['expression_data'])
