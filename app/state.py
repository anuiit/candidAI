import streamlit as st

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "jobs_df" not in st.session_state:
        st.session_state.jobs_df = None
    if "current_resume" not in st.session_state:
        st.session_state.current_resume = ""
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "cover_letter" not in st.session_state:
        st.session_state.cover_letter = None
    if "extra_info" not in st.session_state:
        st.session_state.extra_info = ""

def update_resume_text():
    """Update the resume text from the text area."""
    st.session_state.current_resume = st.session_state.resume_text

def update_extra_info():
    """Update the extra info from the text area."""
    st.session_state.extra_info = st.session_state.extra_info_input