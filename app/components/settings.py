import streamlit as st
import os

def show_settings():
    """Display the settings page."""
    st.header("Settings")
    
    st.subheader("API Settings")
    api_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    model = st.selectbox("AI Model", ["gpt-4.1", "o3-mini"], index=0)
    
    if st.button("Save Settings"):
        # In a real app, you would save these settings securely
        # For simplicity, we're just updating the environment variables
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("Settings saved successfully!")
    
    st.subheader("Job Sources")
    st.info("Currently supported job sources: HelloWork and Welcome to the Jungle. More job sources will be added in future updates.")