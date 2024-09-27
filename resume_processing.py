# resume_processing.py

import PyPDF2
import io


def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = ""
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        if not text.strip():
            print("No text extracted from the PDF.")
            return None
        print("Text extracted from PDF successfully.")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
