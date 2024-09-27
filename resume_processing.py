import PyPDF2
import io
import docx
import os

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

def extract_text_from_docx(uploaded_file):
    try:
        doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        if not text.strip():
            print("No text extracted from the Word document.")
            return None
        print("Text extracted from Word document successfully.")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from Word document: {e}")
        return None

def extract_text_from_txt(uploaded_file):
    try:
        text = uploaded_file.getvalue().decode('utf-8')
        if not text.strip():
            print("No text extracted from the plain text file.")
            return None
        print("Text extracted from plain text file successfully.")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from plain text file: {e}")
        return None

def extract_resume_text(uploaded_file):
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(uploaded_file)
    elif file_extension == '.docx':
        return extract_text_from_docx(uploaded_file)
    elif file_extension == '.txt':
        return extract_text_from_txt(uploaded_file)
    else:
        print(f"Unsupported file format: {file_extension}")
        return None
