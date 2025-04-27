import streamlit as st
from services.analyzer import JobResumeAnalyzer
from services.generator import CoverLetterGenerator
from utils.pdf_generator import convert_response_to_pdf

def show_manual_input():
    """Display the manual job input page with integrated results."""
    st.header("Manually Input Job Description")
    
    # Check if resume exists
    if not st.session_state.current_resume:
        st.warning("Please add your resume in the Profile tab before analyzing jobs.")
        return
    
    # Use columns to organize the layout
    input_col, results_col = st.columns([1, 1])
    
    with input_col:
        # Form for manual job input
        with st.form("manual_job_form"):
            job_title = st.text_input("Job Title")
            company = st.text_input("Company Name")
            location = st.text_input("Location")
            job_description = st.text_area("Job Description", height=300)
            
            submit_button = st.form_submit_button("Analyze Job")
        
        if submit_button:
            if not job_description:
                st.warning("Please enter a job description.")
            else:
                process_manual_job(job_title, company, location, job_description)

    # Show results in the right column if available
    with results_col:
        if st.session_state.analysis_result and st.session_state.cover_letter and st.session_state.selected_job:
            display_manual_results()

def process_manual_job(job_title, company, location, job_description):
    """Process a manually entered job."""
    # Create a job object
    manual_job = {
        "title": job_title,
        "company": company,
        "location": location,
        "text": job_description,
        "link": None  # No link for manually entered jobs
    }
    st.session_state.selected_job = manual_job
    
    analyzer = JobResumeAnalyzer()
    generator = CoverLetterGenerator()
    
    with st.spinner("Analyzing job and resume..."):
        analysis = analyzer.analyze(
            st.session_state.current_resume, 
            job_description
        )
        st.session_state.analysis_result = analysis
    
    with st.spinner("Generating cover letter..."):
        cover_letter = generator.generate(
            st.session_state.current_resume,
            job_description,
            st.session_state.analysis_result,
            st.session_state.extra_info
        )
        st.session_state.cover_letter = cover_letter
    
    st.success("Analysis and cover letter generated!")

def display_manual_results():
    """Display the analysis results and cover letter for manually entered jobs."""
    st.header("Analysis Results")
    
    job_title = st.session_state.selected_job.get("title", "Job")
    
    tabs = st.tabs(["Job Analysis", "Cover Letter", "Download PDF"])
    
    with tabs[0]:
        st.subheader(f"Analysis for: {job_title}")
        st.markdown(st.session_state.analysis_result)
    
    with tabs[1]:
        st.subheader("Generated Cover Letter")
        st.markdown(st.session_state.cover_letter)
        
        if st.button("Regenerate Cover Letter", key="regenerate_manual"):
            regenerate_cover_letter()
    
    with tabs[2]:
        st.subheader("Download as PDF")
        
        if st.button("Generate PDF", key="generate_pdf_manual"):
            generate_pdf(job_title)

def regenerate_cover_letter():
    """Regenerate the cover letter."""
    with st.spinner("Generating new cover letter..."):
        generator = CoverLetterGenerator()
        new_cover_letter = generator.generate(
            st.session_state.current_resume,
            st.session_state.selected_job["text"],
            st.session_state.analysis_result,
            st.session_state.extra_info
        )
        st.session_state.cover_letter = new_cover_letter

def generate_pdf(job_title):
    """Generate a PDF of the cover letter and analysis."""
    with st.spinner("Generating PDF..."):
        try:
            response_dict = {
                "analysis": st.session_state.analysis_result,
                "final_cover_letter": st.session_state.cover_letter
            }
            pdf_file = convert_response_to_pdf(response_dict, "job_application_package.pdf")
            
            with open(pdf_file, "rb") as file:
                st.download_button(
                    label="Download PDF",
                    data=file,
                    file_name=f"Cover_Letter_{job_title.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")