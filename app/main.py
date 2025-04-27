import streamlit as st
import os

# Import components and pages
from components.job_search import show_job_search
from components.manual_input import show_manual_input
from components.settings import show_settings
from components.profile import show_profile
from state import initialize_session_state
from config import config

if config.DEBUG_MODE:
    import logging
    import sys

    # Set up logging to console
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("Debugging mode is ON.")

if config.DEV_MODE:
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

# Check for API key
if os.getenv("OPENAI_API_KEY") is None:
    st.error("OpenAI API key not found. Please add it to your .env file.")
    st.stop()

def main():
    # Configure the page
    st.set_page_config(
        page_title="CandidAI - Job Application Assistant",
        page_icon="📝",
        layout="wide"
    )

    # App title and description
    st.title("CandidAI - Job Application Assistant")
    st.markdown("""
    This app helps you find job listings, analyze them against your resume, 
    and generate tailored cover letters using AI.
    """)

    # Initialize session state
    initialize_session_state()
    
    # Navigation tabs
    tabs = st.tabs(["Profile", "Job Search", "Manual Job Input", "Settings"])
    
    # Display the selected page
    with tabs[0]:
        show_profile()
    with tabs[1]:
        show_job_search()
    with tabs[2]:
        show_manual_input()
    with tabs[3]:
        show_settings()

if __name__ == "__main__":
    main()