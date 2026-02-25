import pandas as pd
from transformers import pipeline

# Load the language model for summarization
summarizer = pipeline("summarization")

def summarize_pipeline_results(data_frame):
    """
    Takes a DataFrame containing pipeline results and returns a summarized analysis.
    """
    # Convert DataFrame to a string for the summarizer
    text = data_frame.to_string(index=False)
    # Generate summary using the language model
    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

# Example usage:
# df = pd.read_csv('results.csv') # Load your results DataFrame here
# print(summarize_pipeline_results(df))
