import streamlit as st
from PIL import Image

# Page configuration
# st.set_page_config(page_title="ShadowLog - Home", page_icon="📊", layout="wide")

# Main page with logo
try:
    logo = Image.open("assets/logo_large.png")
    st.image(logo, use_container_width=True)
except FileNotFoundError:
    st.error("Logo not found. Please check the path: assets/logo_large.png")

# Main content
st.title("Welcome to ShadowLog")
st.markdown("### Your Advanced Log Analysis Platform")

# Introduction
st.write("""
ShadowLog is a powerful tool designed to simplify and enhance log file analysis. 
Whether you're debugging an application, monitoring system performance, or investigating security incidents,
ShadowLog provides the tools you need to efficiently process and extract insights from your log data.
""")

# Features section
st.header("Key Features")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Log File Upload")
    st.write("""
    Upload log files in various formats including text, JSON, CSV, and more.
    Support for compressed files (.zip, .gz) is also available.
    """)

    st.subheader("🔍 Advanced Parsing")
    st.write("""
    Automatically detect log formats or configure custom parsing rules.
    Extract timestamp, log level, and message content with ease.
    """)

with col2:
    st.subheader("📊 Visual Analysis")
    st.write("""
    Generate insightful visualizations based on your log data.
    Track patterns, anomalies, and trends to quickly identify issues.
    """)

    st.subheader("🔎 Search & Filter")
    st.write("""
    Powerful search functionality to find specific events or errors.
    Filter logs by time, severity, source, or custom attributes.
    """)

# Getting started section
st.header("Getting Started")
st.write("""
To begin analyzing your log files:
1. Navigate to the 'Upload' page using the sidebar
2. Upload your log file or select a sample file
3. Configure parsing options if needed
4. Explore the generated analysis and visualizations

Check out the documentation for more detailed instructions and advanced features.
""")
