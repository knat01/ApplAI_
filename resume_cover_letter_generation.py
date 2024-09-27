import openai
import base64
import urllib.parse

def generate_resume_and_cover_letter(resume_text, job_description, api_key):
    openai.api_key = api_key

    try:
        # Generate resume
        resume_prompt = f"""
        Based on the following resume and job description, create a tailored LaTeX resume:

        Resume:
        {resume_text}

        Job Description:
        {job_description}

        Generate a LaTeX resume that highlights relevant skills and experiences for this job.
        """

        resume_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": resume_prompt}],
            max_tokens=1000
        )
        resume_latex = resume_response.choices[0].message.content

        # Generate cover letter
        cover_letter_prompt = f"""
        Based on the following resume and job description, create a tailored LaTeX cover letter:

        Resume:
        {resume_text}

        Job Description:
        {job_description}

        Generate a LaTeX cover letter that expresses interest in the position and highlights relevant qualifications.
        """

        cover_letter_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": cover_letter_prompt}],
            max_tokens=1000
        )
        cover_letter_latex = cover_letter_response.choices[0].message.content

        # Encode LaTeX content to Base64 and create data URLs
        resume_encoded = base64.b64encode(resume_latex.encode('utf-8')).decode('utf-8')
        cover_letter_encoded = base64.b64encode(cover_letter_latex.encode('utf-8')).decode('utf-8')

        resume_url = f"data:application/x-tex;base64,{urllib.parse.quote(resume_encoded)}"
        cover_letter_url = f"data:application/x-tex;base64,{urllib.parse.quote(cover_letter_encoded)}"

        return resume_url, cover_letter_url
    except Exception as e:
        print(f"Error generating resume and cover letter: {e}")
        return None, None
