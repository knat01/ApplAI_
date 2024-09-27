# resume_cover_letter_generation.py

import openai
import time
import os
import base64
import urllib.parse

# Paths to the LaTeX template files
start_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latex_resume_format_start.tex')
end_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latex_resume_format_end.tex')
cover_letter_start_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latex_cover_letter_format_start.tex')
cover_letter_end_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latex_cover_letter_format_end.tex')

with open(start_template_path, 'r') as file:
    start_template = file.read()

with open(end_template_path, 'r') as file:
    end_template = file.read()

with open(cover_letter_start_template_path, 'r') as file:
    cover_letter_start_template = file.read()

with open(cover_letter_end_template_path, 'r') as file:
    cover_letter_end_template = file.read()

# Function to create LaTeX resume assistant
def create_latex_resume_assistant(api_key):
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    assistant = client.beta.assistants.create(
        model='gpt-4-1106-preview',
        name='LaTeX Resume Content Integrator',
        instructions="""Integrate the user's resume details into the 'latex_end_template', adhering strictly to its structure and format.
        Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
        Focus on the Experience, Education, Projects, and Technical Skills sections, using the user's resume information.
        Avoid any unicode characters and extra LaTeX commands not present in the template.
        If specific data (like project dates) are absent in the user's resume, omit those elements from the template. Highlight in bold any resume content that matches key terms in the job description,
        particularly in the Experience and Projects sections. Tailor the resume to emphasize aspects relevant to the job description, without adding information not present in the user's resume.
        The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete resume. also dont write ```latex at the start and ``` at the end. Make sure to use only this apostrophe ' and only this dash - not any other ones.""",
        tools=[]
    )
    return assistant

# Function to create LaTeX cover letter assistant
def create_latex_cover_letter_assistant(api_key):
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    assistant = client.beta.assistants.create(
        model='gpt-4-1106-preview',
        name='LaTeX Cover Letter Content Integrator',
        instructions="""Integrate the user's resume details and job description into the 'latex_cover_letter_end_template', adhering strictly to its structure and format.
        Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
        Focus on creating a compelling introduction, highlighting relevant skills and experiences, and expressing enthusiasm for the position and company.
        Avoid any unicode characters and extra LaTeX commands not present in the template.
        If specific data is absent in the user's resume or job description, gracefully handle the omission. 
        The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete cover letter. 
        Do not write ```latex at the start and ``` at the end. Make sure to use only this apostrophe ' and only this dash - not any other ones.""",
        tools=[]
    )
    return assistant

# Function to generate LaTeX resume from input
def generate_latex_resume_from_input(user_resume, job_description, latex_end_template, assistant_id, api_key):
    client = openai.Client(api_key=api_key)
    thread = client.beta.threads.create()
    thread_id = thread.id

    messages = [
        {'role': 'user', 'content': user_resume},
        {'role': 'user', 'content': job_description},
        {'role': 'user', 'content': latex_end_template}
    ]
    for message in messages:
        client.beta.threads.messages.create(thread_id=thread_id, role=message['role'], content=message['content'])

    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    while run.status in ['queued', 'in_progress']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == 'assistant':
                if isinstance(message.content, list):
                    for part in message.content:
                        if isinstance(part, openai.types.beta.threads.message_content_text.MessageContentText):
                            response_text = part.text.value
                            if response_text.strip():
                                return response_text
                else:
                    print(f"[Debug] Unexpected content type received from the assistant {type(message.content)}")
    else:
        print(f"[Debug] Run did not complete successfully. Status {run.status}")

    return None

# Function to generate LaTeX cover letter from input
def generate_latex_cover_letter_from_input(user_resume, job_description, latex_cover_letter_end_template, assistant_id, api_key):
    client = openai.Client(api_key=api_key)
    thread = client.beta.threads.create()
    thread_id = thread.id

    messages = [
        {'role': 'user', 'content': user_resume},
        {'role': 'user', 'content': job_description},
        {'role': 'user', 'content': latex_cover_letter_end_template}
    ]
    for message in messages:
        client.beta.threads.messages.create(thread_id=thread_id, role=message['role'], content=message['content'])

    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    while run.status in ['queued', 'in_progress']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == 'assistant':
                if isinstance(message.content, list):
                    for part in message.content:
                        if isinstance(part, openai.types.beta.threads.message_content_text.MessageContentText):
                            response_text = part.text.value
                            if response_text.strip():
                                return response_text
                else:
                    print(f"[Debug] Unexpected content type received from the assistant {type(message.content)}")
    else:
        print(f"[Debug] Run did not complete successfully. Status {run.status}")

    return None

# Function to combine and save LaTeX resume
def combine_and_save_latex_resume(start_content, generated_content):
    combined_content = start_content + '\n' + generated_content

    # Encode LaTeX content to Base64 and URL-encode the result
    encoded_content = base64.b64encode(combined_content.encode('utf-8')).decode('utf-8')
    url_encoded_content = urllib.parse.quote(encoded_content)  # URL encode the Base64 string

    data_url = f"data:application/x-tex;base64,{url_encoded_content}"

    return data_url  # Return the data URL directly

# Function to combine and save LaTeX cover letter
def combine_and_save_latex_cover_letter(start_content, generated_content):
    combined_content = start_content + '\n' + generated_content

    # Encode LaTeX content to Base64 and URL-encode the result
    encoded_content = base64.b64encode(combined_content.encode('utf-8')).decode('utf-8')
    url_encoded_content = urllib.parse.quote(encoded_content)  # URL encode the Base64 string

    data_url = f"data:application/x-tex;base64,{url_encoded_content}"

    return data_url  # Return the data URL directly

# Function to generate resume and cover letter
def generate_resume_and_cover_letter(resume_text, job_description, api_key):
    # Generate LaTeX resume
    latex_resume_assistant = create_latex_resume_assistant(api_key)
    generated_resume_content = generate_latex_resume_from_input(
        resume_text, job_description, end_template, latex_resume_assistant.id, api_key
    )
    if generated_resume_content is None:
        print("Error: Failed to generate LaTeX resume")
        return None, None

    resume_data_url = combine_and_save_latex_resume(start_template, generated_resume_content)

    # Generate LaTeX cover letter
    latex_cover_letter_assistant = create_latex_cover_letter_assistant(api_key)
    generated_cover_letter_content = generate_latex_cover_letter_from_input(
        resume_text, job_description, cover_letter_end_template, latex_cover_letter_assistant.id, api_key
    )
    if generated_cover_letter_content is None:
        print("Error: Failed to generate LaTeX cover letter")
        return resume_data_url, None

    cover_letter_data_url = combine_and_save_latex_cover_letter(cover_letter_start_template, generated_cover_letter_content)

    return resume_data_url, cover_letter_data_url
