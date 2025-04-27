import os
from openai import OpenAI

from config import DEFAULT_MODEL

class CoverLetterGenerator:
    """Generate cover letters based on resume, job description, and analysis"""
    
    def __init__(self, model=None):
        self.client = OpenAI()
        self.model = model or DEFAULT_MODEL
        
        # Load prompt templates
        self.writer_template = self._load_writer_template()
        self.reviewer_template = self._load_reviewer_template()
    
    def _load_writer_template(self):
        """Load the prompt template for cover letter writing"""
        return """
You are an expert Cover Letter Writer with extensive experience in professional writing and recruitment. Your mission is to craft a tailored, compelling cover letter that effectively positions the candidate for their target role.
INPUT
Job description
- Candidate's resume
- Resume-job match analysis
- Additional candidate information

APPROACH
1. Strategic Content Analysis
- Identify 3-5 key selling points from the resume that directly align with the job requirements
- Note specific achievements with quantifiable results that demonstrate relevant skills
- Identify unique qualifications or experiences that set the candidate apart
- Consider gaps identified in the analysis and how to address them positively

2. Company & Role Assessment
- Analyze the job description to identify:
    - Core values and company culture indicators
    - Key priorities for the role
    - Industry-specific language and terminology
    - Level of formality in the description

3. Cover Letter Composition
- Craft a personalized greeting (avoid "To Whom It May Concern" when possible)
- Write a compelling opening that shows enthusiasm and states intent
- Develop 2-3 focused paragraphs highlighting relevant experiences and skills
- Directly connect candidate strengths to job requirements with specific examples
- Include a confident closing with clear next steps
- Keep total length between 200-300 words

4. Tone Calibration
- Match writing style to the company's apparent culture:
    - Traditional/formal for corporate, financial, legal roles
    - Balanced professional/personable for most business roles
    - More conversational for creative, startup, or innovation-focused roles
- Maintain professionalism while showcasing the candidate's personality
- Use active voice and confident language throughout

5. Authentic Language Requirements
- Avoid generic buzzwords and clichés that appear in most cover letters
- Use natural language that a human would actually say in conversation
- Replace vague claims ("I am passionate about...") with specific evidence
- When expressing interest, tie it to concrete experiences or projects
- Never use the phrase "passionate about [industry/skill]" - instead describe specific work that shows genuine engagement

OUTPUT FORMAT
- Deliver a complete, ready-to-use cover letter with:

Professional greeting
- Opening paragraph
- 2-3 body paragraphs
- Closing paragraph
- Professional sign-off
- No placeholders or instructions within the final letter

CONSTRAINTS
- Maximum 300 words total
- No generic language that could apply to any job
- No exaggeration of candidate qualifications
- No overly formal phrases like "I wish to apply" or "Please find attached"
- No mentions of the cover letter being AI-generated

INPUT VARIABLES
Job description: {job_description}
Resume: {resume}
Match analysis: {analysis}
Additional candidate info: {extra_information}
"""
    
    def _load_reviewer_template(self):
        """Load the prompt template for cover letter reviewing"""
        return """
You are an experienced Cover Letter Review Specialist with expertise in professional writing, hiring practices, and job application optimization. Your role is to provide constructive, actionable feedback to improve a candidate's cover letter.
INPUT

Job description
Candidate's resume
Candidate's draft cover letter

PROCESS
Follow this systematic review approach:

Initial Alignment Assessment

Evaluate how well the cover letter addresses the specific job requirements
Check if the candidate's most relevant qualifications are highlighted
Assess whether the letter demonstrates understanding of the company/role


Content Analysis

Review the introduction for engagement and clear statement of intent
Evaluate body paragraphs for specific, relevant examples and achievements
Assess the conclusion for appropriate call-to-action and next steps
Check for coverage of key skills and experiences from the resume that match the job


Writing Quality Review

Identify any grammar, spelling, or punctuation errors
Assess sentence structure and paragraph flow
Check for appropriate formal/informal tone based on company culture
Evaluate for conciseness and impact (optimal length 200-300 words)


Impact Enhancement

Identify areas where stronger language could be used
Suggest specific quantifiable achievements that could be added
Recommend improvements to personalization for the specific company
Suggest ways to address any qualification gaps positively


Formatting Check

Review overall presentation and layout
Check for appropriate business letter formatting
Ensure contact information is included appropriately



OUTPUT FORMAT
Provide your review in these clear sections:
## Overall Assessment
[1-2 sentences summarizing the cover letter's effectiveness for this specific job]

## Strengths
- [3-5 bullet points highlighting what works well]

## Areas for Improvement
- [3-5 specific, actionable suggestions with examples]

## Language and Tone Recommendations
[Feedback on writing style, tone, and word choice]

## Specific Revision Suggestions
[2-3 concrete examples of sentences or sections that could be improved, with before/after examples]

## Final Recommendations
[3-5 bullet points summarizing the most important changes to make]
INPUT VARIABLES
Job description: {job_description}
Resume: {resume}
Cover letter: {cover_letter}
"""
    
    def generate(self, resume, job_description, analysis, extra_information=""):
        """
        Generate a cover letter based on resume, job description, and analysis
        
        Args:
            resume (str): The candidate's resume text
            job_description (str): The job description text
            analysis (str): The job-resume match analysis
            extra_information (str): Additional candidate information
            
        Returns:
            str: Generated cover letter
        """
        # Generate initial cover letter
        prompt = self.writer_template.format(
            resume=resume,
            job_description=job_description,
            analysis=analysis,
            extra_information=extra_information
        )
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt
            )
            cover_letter = response.output_text
            
            # Review and improve the cover letter
            review_prompt = self.reviewer_template.format(
                resume=resume,
                job_description=job_description,
                cover_letter=cover_letter
            )
            
            review_response = self.client.responses.create(
                model=self.model,
                input=review_prompt
            )
            
            # Generate final cover letter based on the review
            final_prompt = self.writer_template.format(
                resume=resume,
                job_description=job_description,
                analysis=review_response.output_text,
                extra_information=extra_information
            )
            
            final_response = self.client.responses.create(
                model=self.model,
                input=final_prompt
            )
            
            return final_response.output_text
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return f"Error generating cover letter: {e}"