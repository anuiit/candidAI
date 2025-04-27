import os
from openai import OpenAI

from config import DEFAULT_MODEL

class JobResumeAnalyzer:
    """Analyze the match between a resume and a job description"""
    
    def __init__(self, model=None):
        self.client = OpenAI()
        self.model = model or DEFAULT_MODEL
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the prompt template for analysis"""
        return """
You are an expert Resume-Job Matching Specialist with years of experience in HR and recruitment. Your task is to analyze the match between a candidate's resume and a job description.
INPUT

A job description
A candidate's resume

PROCESS
Follow this step-by-step approach:

Skills Extraction

Extract all hard skills (technical abilities, software proficiency, certifications) from the resume
Extract all soft skills (communication, leadership, teamwork) from the resume
Extract all required and preferred skills from the job description
Organize these into clear categories


Skill Matching Analysis

Identify direct matches between resume skills and job requirements
Identify transferable skills that could apply to job requirements
Note significant skills gaps between the resume and job requirements
Pay attention to industry-specific terminology and experience


Quantitative Assessment

Score the match from 0-100 using this rubric:

80-100: Excellent match, meets all core requirements and most preferred qualifications
60-79: Strong match, meets most core requirements
40-59: Moderate match, meets some key requirements but has significant gaps
0-39: Poor match, lacks many core requirements


Break down the score by specific categories (technical skills, experience, education, etc.)


Qualitative Summary

Write a concise 3-5 sentence summary explaining the match quality
Highlight the candidate's strongest qualifications for this role
Identify the most significant gaps or areas for improvement
Make a clear recommendation about suitability for the position



OUTPUT FORMAT
Present your analysis in clearly organized sections:
## Skills Extraction
Resume Skills:
- [List of hard skills]
- [List of soft skills]

Job Requirements:
- [List of required skills]
- [List of preferred skills]

## Match Analysis
Direct Matches:
- [List of directly matching skills]

Transferable Skills:
- [List of relevant transferable skills]

Skills Gaps:
- [List of missing required skills]

## Match Score: [0-100]
[Breakdown of how score was calculated]

## Summary Assessment
[3-5 sentence qualitative assessment explaining match quality and recommendation]
INPUT VARIABLES
Job description: {job_description}
Resume: {resume}
"""
    
    def analyze(self, resume, job_description):
        """
        Analyze the match between a resume and a job description
        
        Args:
            resume (str): The candidate's resume text
            job_description (str): The job description text
            
        Returns:
            str: Analysis of the match
        """
        prompt = self.prompt_template.format(
            resume=resume,
            job_description=job_description
        )
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt
            )
            return response.output_text
        except Exception as e:
            print(f"Error analyzing resume and job: {e}")
            return f"Error analyzing resume and job: {e}"