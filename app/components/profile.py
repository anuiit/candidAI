import streamlit as st
from state import update_resume_text, update_extra_info

def show_profile():
    """Display the profile page where users can manage their resume and additional information."""
    # Create two columns for resume and additional info
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Your Resume")
        resume_file = st.file_uploader("Upload your resume", type=["txt", "pdf"])
        if resume_file:
            try:
                st.session_state.current_resume = resume_file.getvalue().decode("utf-8")
                st.success("Resume uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading resume: {e}")
        
        st.text_area(
            "Or paste your resume text here:", 
            value=st.session_state.current_resume, 
            height=300,
            key="resume_text",
            on_change=update_resume_text
        )
    
    with col2:
        st.subheader("Additional Information")
        st.markdown("""
        Add any additional information about yourself that might be relevant for job applications 
        but is not included in your resume. This could include:
        
        - Personal projects
        - Career goals
        - Job preferences
        - Skills you're developing
        - Other relevant details
        """)
        
        st.text_area(
            "Additional information about you:", 
            value=st.session_state.extra_info,
            height=300,
            key="extra_info_input",
            on_change=update_extra_info
        )
    
    # Display resume status
    if st.session_state.current_resume:
        word_count = len(st.session_state.current_resume.split())
        st.success(f"Your resume is ready! ({word_count} words)")
    else:
        st.warning("Please upload or paste your resume to start using the application.")