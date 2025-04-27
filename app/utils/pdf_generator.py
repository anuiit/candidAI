from fpdf import FPDF
import re
import os

def convert_response_to_pdf(response_dict, output_filename="job_application_package.pdf", 
                           signature_name="Candidate", 
                           signature_image=None):
    """
    Convert the GPT response dictionary to a formatted PDF with proper Unicode support
    and add a signature at the end
    
    Args:
        response_dict: Dictionary containing analysis and cover letter responses
        output_filename: Name of the output PDF file
        signature_name: Name to display as signature
        signature_image: Path to signature image file (optional)
    """
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Resume Analysis", ln=True, align="C")
    pdf.ln(5)
    
    # Content
    pdf.set_font("Arial", "", 11)
    
    # Split the analysis text into lines and sections
    analysis_lines = response_dict["analysis"].split('\n')
    
    for line in analysis_lines:
        # Replace all problematic Unicode characters
        cleaned_line = (line
                        .replace('\u2003', '  ')  # em space
                        .replace('\u2019', "'")   # right single quotation mark
                        .replace('\u2018', "'")   # left single quotation mark
                        .replace('\u201C', '"')   # left double quotation mark
                        .replace('\u201D', '"')   # right double quotation mark
                        .replace('\u2022', '-')   # bullet
                        .replace('\u2013', '-')   # en dash
                        .replace('\u2014', '-')   # em dash
                        .replace('\u00A0', ' ')   # non-breaking space
                        .replace('\u2026', '...') # ellipsis
                        .replace('–', '-')        # another en dash
                        .replace('—', '-')        # another em dash
                        .replace('•', '-')        # another bullet
                       )
        
        # Handle section headings
        if re.match(r'^#{1,2}\s', cleaned_line):
            pdf.set_font("Arial", "B", 14 if cleaned_line.startswith('##') else 16)
            pdf.cell(0, 10, re.sub(r'^#{1,2}\s', '', cleaned_line), ln=True)
            pdf.set_font("Arial", "", 11)
        # Handle bullet points
        elif cleaned_line.strip().startswith('-'):
            pdf.set_x(15)
            pdf.multi_cell(0, 8, "- " + cleaned_line.strip()[2:])  # Use hyphen instead of bullet
        # Regular text
        elif cleaned_line.strip():
            pdf.multi_cell(0, 8, cleaned_line)
        # Add a small space for empty lines
        else:
            pdf.ln(4)
    
    # Add cover letter page
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Cover Letter", ln=True, align="C")
    pdf.ln(5)
    
    # Content
    pdf.set_font("Arial", "", 11)
    
    # Format the cover letter text
    cover_letter_lines = response_dict["final_cover_letter"].split('\n')
    
    for line in cover_letter_lines:
        # Replace all problematic Unicode characters
        cleaned_line = (line
                        .replace('\u2003', '  ')  # em space
                        .replace('\u2019', "'")   # right single quotation mark
                        .replace('\u2018', "'")   # left single quotation mark
                        .replace('\u201C', '"')   # left double quotation mark
                        .replace('\u201D', '"')   # right double quotation mark
                        .replace('\u2022', '-')   # bullet
                        .replace('\u2013', '-')   # en dash
                        .replace('\u2014', '-')   # em dash
                        .replace('\u00A0', ' ')   # non-breaking space
                        .replace('\u2026', '...') # ellipsis
                        .replace('–', '-')        # another en dash
                        .replace('—', '-')        # another em dash
                        .replace('•', '-')        # another bullet
                       )
        
        if not cleaned_line.strip():
            pdf.ln(4)
        else:
            pdf.multi_cell(0, 8, cleaned_line)
    
    # Add signature at the end
    pdf.ln(20)  # Add space before signature
    
    # Add image signature if provided and file exists
    if signature_image and os.path.exists(signature_image):
        # Calculate reasonable signature size (adjust as needed)
        signature_width = 50  # mm
        pdf.image(signature_image, x=20, w=signature_width)
        pdf.ln(10)
    
    # Add text signature in any case
    pdf.set_font("Arial", "I", 12)  # Italic font for signature
    pdf.cell(0, 10, signature_name, ln=True)
    
    # Save the PDF
    pdf.output(output_filename)
    
    return output_filename