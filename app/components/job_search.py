import streamlit as st
import pandas as pd
from scrapers.hellowork import HelloWorkScraper
from scrapers.wttj import WTTJScraper
from services.analyzer import JobResumeAnalyzer
from services.generator import CoverLetterGenerator
from utils.pdf_generator import convert_response_to_pdf

def show_job_search():
    """Display the job search page with integrated results."""
    st.header("Search for Jobs")
    
    # Initialize session state variables if they don't exist
    if "last_search" not in st.session_state:
        st.session_state.last_search = {"job_source": None, "job_title": None, "location": None, "job_type": None, "page": 1}
    
    # Check if resume exists
    if not st.session_state.current_resume:
        st.warning("Please add your resume in the Profile tab before searching for jobs.")
        return
    
    # Create two columns for the entire page layout
    search_col, analysis_col = st.columns([1, 1])
    
    with search_col:
        st.subheader("Search and Results")
        
        # Job search form
        with st.form("job_search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                job_source = st.selectbox("Job Source", ["HelloWork", "Welcome to the Jungle"], index=0)
                job_title = st.text_input("Job Title", "data scientist")
                page = st.number_input("Page Number", min_value=1, value=1, step=1, help="Specify which page of results to view")
            
            with col2:
                location = st.text_input("Location", "Athis-Mons 91200")
                job_type = st.selectbox("Job Type", ["All", "Internship", "Full-time", "Part-time"], index=0)
            
            search_button = st.form_submit_button("Search Jobs")
        
        if search_button:
            # Save the search parameters
            st.session_state.last_search = {
                "job_source": job_source,
                "job_title": job_title,
                "location": location,
                "job_type": job_type,
                "page": page
            }
            search_jobs(job_source, job_title, location, job_type, page=page)
        
        # Display search results in the left column
        if "jobs_df" in st.session_state and st.session_state.jobs_df is not None:
            if not st.session_state.jobs_df.empty:
                search_params = st.session_state.last_search
                st.subheader(f"Search Results (Page {search_params['page']})")
                
                # Display job listings
                filtered_df = st.session_state.jobs_df.copy()
                st.dataframe(filtered_df[["title", "company", "location", "link"]], height=300)
                
                # Job selection
                job_indices = filtered_df.index.tolist()
                
                job_index = st.selectbox(
                    "Select a job to analyze:",
                    options=job_indices,
                    format_func=lambda x: f"{filtered_df.loc[x, 'company']} - {filtered_df.loc[x, 'title']} - {filtered_df.loc[x, 'location']}"
                )
                
                if st.button("Analyze Selected Job"):
                    analyze_selected_job(filtered_df, job_index)
            else:
                st.warning("No jobs found on this page. Try a different page number or modify your search criteria.")
                
                # Provide some helpful suggestions
                st.info("Suggestions: \n"
                       "- Try a lower page number\n"
                       "- Use broader job title keywords\n"
                       "- Try a different location or expand your location radius\n"
                       "- Consider different job types")
    
    # Display analysis results in the right column if available
    with analysis_col:
        if "analysis_result" in st.session_state and st.session_state.analysis_result:
            st.subheader("Analysis Results")
            display_job_results()

def search_jobs(job_source, job_title, location, job_type, page=1):
    """Search for jobs using the selected job source with pagination."""
    with st.spinner(f"Searching for jobs on page {page}..."):
        scraper = None
        
        if job_source == "HelloWork":
            scraper = HelloWorkScraper()
        elif job_source == "Welcome to the Jungle":
            scraper = WTTJScraper()
        else:
            st.warning("This job source is not implemented yet.")
            st.session_state.jobs_df = pd.DataFrame()  # Initialize with empty DataFrame
            return
            
        try:
            jobs = scraper.search_jobs(job_title, location, job_type, page=page)
            if jobs:
                # Store results in the jobs_df
                df = pd.DataFrame(jobs)
                st.session_state.jobs_df = df
                st.success(f"Found {len(jobs)} jobs on page {page}!")
            else:
                # Store empty DataFrame
                empty_df = pd.DataFrame()
                st.session_state.jobs_df = empty_df
                st.warning(f"No jobs found on page {page}. Try different search terms or a different page.")
        except Exception as e:
            st.error(f"Error searching for jobs: {e}")
            st.session_state.jobs_df = pd.DataFrame()  # Initialize with empty DataFrame

def analyze_selected_job(filtered_df, job_index):
    """Analyze the selected job against the user's resume."""
    selected_job = filtered_df.loc[job_index]
    # Convert pandas Series to dictionary to avoid boolean evaluation issues
    st.session_state.selected_job = selected_job.to_dict()
    
    # Get the job source from last search
    job_source = st.session_state.last_search.get("job_source", "HelloWork")
    
    # If job content isn't already scraped, get it
    if pd.isna(selected_job.get('text')):
        with st.spinner("Retrieving job details..."):
            try:
                if job_source == "HelloWork":
                    scraper = HelloWorkScraper()
                elif job_source == "Welcome to the Jungle":
                    scraper = WTTJScraper()
                else:
                    st.error("Unsupported job source")
                    return
                    
                job_details = scraper.get_job_details(selected_job["link"])
                if job_details:
                    if isinstance(job_details, dict) and "cleaned_text" in job_details:
                        # For HelloWork format
                        st.session_state.selected_job["text"] = job_details["cleaned_text"]
                    else:
                        # For WTTJ or other formats that return text directly
                        st.session_state.selected_job["text"] = job_details
                    st.success("Job details retrieved successfully!")
                else:
                    st.error("Could not retrieve job details.")
            except Exception as e:
                st.error(f"Error retrieving job details: {e}")
    
    # Process the job if we have all requirements
    if st.session_state.current_resume and not pd.isna(st.session_state.selected_job.get('text')):
        process_job_and_resume()
    else:
        if not st.session_state.current_resume:
            st.warning("Please upload or paste your resume first.")
        if pd.isna(st.session_state.selected_job.get('text')):
            st.warning("No job details available to analyze.")

def process_job_and_resume():
    """Process the job and resume to generate analysis and cover letter."""
    analyzer = JobResumeAnalyzer()
    generator = CoverLetterGenerator()
    
    with st.spinner("Analyzing job and resume..."):
        analysis = analyzer.analyze(
            st.session_state.current_resume, 
            st.session_state.selected_job["text"]
        )
        st.session_state.analysis_result = analysis
    
    with st.spinner("Generating cover letter..."):
        cover_letter = generator.generate(
            st.session_state.current_resume,
            st.session_state.selected_job["text"],
            st.session_state.analysis_result,
            st.session_state.extra_info
        )
        st.session_state.cover_letter = cover_letter
    
    st.success("Analysis and cover letter generated!")

def display_job_results():
    """Display the analysis results and cover letter."""
    job_title = st.session_state.selected_job.get("title", "Job")
    st.write(f"**Selected Job:** {job_title}")
    
    tabs = st.tabs(["Job Analysis", "Cover Letter", "Download PDF"])
    
    with tabs[0]:
        st.markdown(st.session_state.analysis_result)
    
    with tabs[1]:
        st.markdown(st.session_state.cover_letter)
        
        if st.button("Regenerate Cover Letter", key="regenerate_job_search"):
            regenerate_cover_letter()
    
    with tabs[2]:
        if st.button("Generate PDF", key="generate_pdf_job_search"):
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