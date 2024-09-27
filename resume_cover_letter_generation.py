# resume_cover_letter_generation.py

import openai
import base64
import urllib.parse
import time
import streamlit as st
import subprocess
import os


def create_latex_resume_assistant(api_key: str):
    """
    Create a LaTeX Resume Content Integrator assistant using OpenAI's beta API.

    Args:
        api_key (str): OpenAI API key.

    Returns:
        assistant: The created assistant object.
    """
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    assistant = client.beta.assistants.create(
        model="gpt-4-1106-preview",
        name="LaTeX Resume Content Integrator",
        instructions=
        """Integrate the user's resume details into the 'latex_end_template', adhering strictly to its structure and format.
Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
Focus on the Experience, Education, Projects, and Technical Skills sections, using the user's resume information.
Avoid any unicode characters and extra LaTeX commands not present in the template.
If specific data (like project dates) are absent in the user's resume, omit those elements from the template. Highlight in bold any resume content that matches key terms in the job description,
particularly in the Experience and Projects sections. Tailor the resume to emphasize aspects relevant to the job description, without adding information not present in the user's resume.
The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete resume. also dont write ```latex at the start and ``` at the end. Make sure to use only this apostrophe ' and only this dash - not any other ones.""",
        tools=[])
    return assistant


def create_latex_cover_letter_assistant(api_key: str):
    """
    Create a LaTeX Cover Letter Content Integrator assistant using OpenAI's beta API.

    Args:
        api_key (str): OpenAI API key.

    Returns:
        assistant: The created assistant object.
    """
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    assistant = client.beta.assistants.create(
        model="gpt-4-1106-preview",
        name="LaTeX Cover Letter Content Integrator",
        instructions=
        """Integrate the user's resume details and job description into the 'latex_cover_letter_end_template', adhering strictly to its structure and format.
Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
Focus on creating a compelling introduction, highlighting relevant skills and experiences, and expressing enthusiasm for the position and company.
Avoid any unicode characters and extra LaTeX commands not present in the template.
If specific data is absent in the user's resume or job description, gracefully handle the omission. 
The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete cover letter. 
Do not write ```latex at the start and ``` at the end. Make sure to use only this apostrophe ' and only this dash - not any other ones.""",
        tools=[])
    return assistant


def generate_latex_resume(user_resume: str, job_description: str,
                          latex_end_template: str, assistant_id: str,
                          api_key: str) -> str:
    """
    Generate a tailored LaTeX resume based on the user's resume and job description.

    Args:
        user_resume (str): The user's resume text.
        job_description (str): The job description text.
        latex_end_template (str): The ending part of the LaTeX resume template.
        assistant_id (str): The ID of the created assistant.
        api_key (str): OpenAI API key.

    Returns:
        str: The generated LaTeX resume as a data URL or Overleaf project URL.
    """
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    print("[Debug] Creating a thread for conversation...")
    thread = client.beta.threads.create()
    thread_id = thread.id
    print(f"[Debug] Thread created with ID: {thread_id}")

    print("[Debug] Adding messages to the thread...")
    messages = [{
        "role": "user",
        "content": user_resume
    }, {
        "role": "user",
        "content": job_description
    }, {
        "role": "user",
        "content": latex_end_template
    }]
    for message in messages:
        print(f"[Debug] Adding message with role '{message['role']}'")
        client.beta.threads.messages.create(thread_id=thread_id,
                                            role=message["role"],
                                            content=message["content"])

    print("[Debug] Running the assistant with the created thread...")
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    while run.status in ['queued', 'in_progress']:
        print(f"[Debug] Waiting for run to complete... Status: {run.status}")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                run_id=run.id)

    print(f"[Debug] Run status after completion: {run.status}")
    if run.status == 'completed':
        print("[Debug] Run completed. Fetching messages...")
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Log all the messages to inspect what's being returned
        for message in messages.data:
            print(f"[Debug] Message role: {message.role}")
            print(f"[Debug] Message content: {message.content}")
            if message.role == "assistant":
                print(
                    "[Debug] Assistant message found. Checking for LaTeX content..."
                )

                # Iterate through the list of content parts
                if isinstance(message.content, list):
                    for part in message.content:
                        if hasattr(part, 'text'):
                            text_obj = part.text
                            if hasattr(text_obj, 'value'):
                                response_text = text_obj.value
                                print(
                                    f"[Debug] Assistant LaTeX response: {response_text}"
                                )
                                if response_text.strip():
                                    # Compile LaTeX to PDF and get download link
                                    pdf_path = compile_latex_to_pdf(
                                        response_text, "Generated Resume")
                                    if pdf_path:
                                        return pdf_path
                                    else:
                                        # Fallback to data URL if compilation fails
                                        return combine_and_save_latex_resume(
                                            latex_end_template, response_text)
                elif hasattr(message.content, 'text'):
                    text_obj = message.content.text
                    if hasattr(text_obj, 'value'):
                        response_text = text_obj.value
                        print(
                            f"[Debug] Assistant LaTeX response: {response_text}"
                        )
                        if response_text.strip():
                            pdf_path = compile_latex_to_pdf(
                                response_text, "Generated Resume")
                            if pdf_path:
                                return pdf_path
                            else:
                                return combine_and_save_latex_resume(
                                    latex_end_template, response_text)
                else:
                    print(
                        "[Debug] No valid LaTeX content found in assistant message."
                    )
    else:
        print(
            f"[Debug] Run did not complete successfully. Status: {run.status}")

    print(
        "[Debug] No valid LaTeX content found or run did not complete successfully."
    )
    return None


def generate_latex_cover_letter(user_resume: str, job_description: str,
                                latex_cover_letter_end_template: str,
                                assistant_id: str, api_key: str) -> str:
    """
    Generate a tailored LaTeX cover letter based on the user's resume and job description.

    Args:
        user_resume (str): The user's resume text.
        job_description (str): The job description text.
        latex_cover_letter_end_template (str): The ending part of the LaTeX cover letter template.
        assistant_id (str): The ID of the created assistant.
        api_key (str): OpenAI API key.

    Returns:
        str: The generated LaTeX cover letter as a data URL or Overleaf project URL.
    """
    client = openai.Client(api_key=api_key)  # Pass api_key to the client
    print("[Debug] Creating a thread for conversation (cover letter)...")
    thread = client.beta.threads.create()
    thread_id = thread.id
    print(f"[Debug] Thread created with ID: {thread_id}")

    print("[Debug] Adding messages to the thread (cover letter)...")
    messages = [{
        "role": "user",
        "content": user_resume
    }, {
        "role": "user",
        "content": job_description
    }, {
        "role": "user",
        "content": latex_cover_letter_end_template
    }]
    for message in messages:
        print(f"[Debug] Adding message with role '{message['role']}'")
        client.beta.threads.messages.create(thread_id=thread_id,
                                            role=message["role"],
                                            content=message["content"])

    print(
        "[Debug] Running the assistant with the created thread (cover letter)..."
    )
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    while run.status in ['queued', 'in_progress']:
        print(f"[Debug] Waiting for run to complete... Status: {run.status}")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                run_id=run.id)

    print(f"[Debug] Run status after completion: {run.status}")
    if run.status == 'completed':
        print("[Debug] Run completed. Fetching messages...")
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Log all the messages to inspect what's being returned
        for message in messages.data:
            print(f"[Debug] Message role: {message.role}")
            print(f"[Debug] Message content: {message.content}")
            if message.role == "assistant":
                print(
                    "[Debug] Assistant message found. Checking for LaTeX content..."
                )

                # Iterate through the list of content parts
                if isinstance(message.content, list):
                    for part in message.content:
                        if hasattr(part, 'text'):
                            text_obj = part.text
                            if hasattr(text_obj, 'value'):
                                response_text = text_obj.value
                                print(
                                    f"[Debug] Assistant LaTeX response: {response_text}"
                                )
                                if response_text.strip():
                                    # Compile LaTeX to PDF and get download link
                                    pdf_path = compile_latex_to_pdf(
                                        response_text,
                                        "Generated Cover Letter")
                                    if pdf_path:
                                        return pdf_path
                                    else:
                                        # Fallback to data URL if compilation fails
                                        return combine_and_save_latex_cover_letter(
                                            latex_cover_letter_end_template,
                                            response_text)
                elif hasattr(message.content, 'text'):
                    text_obj = message.content.text
                    if hasattr(text_obj, 'value'):
                        response_text = text_obj.value
                        print(
                            f"[Debug] Assistant LaTeX response: {response_text}"
                        )
                        if response_text.strip():
                            pdf_path = compile_latex_to_pdf(
                                response_text, "Generated Cover Letter")
                            if pdf_path:
                                return pdf_path
                            else:
                                return combine_and_save_latex_cover_letter(
                                    latex_cover_letter_end_template,
                                    response_text)
                else:
                    print(
                        "[Debug] No valid LaTeX content found in assistant message."
                    )
    else:
        print(
            f"[Debug] Run did not complete successfully. Status: {run.status}")

    print(
        "[Debug] No valid LaTeX content found or run did not complete successfully."
    )
    return None


def combine_and_save_latex_resume(start_content: str,
                                  generated_content: str) -> str:
    """
    Combine the start and generated LaTeX content for the resume and encode it.

    Args:
        start_content (str): The starting LaTeX template content.
        generated_content (str): The generated LaTeX content from OpenAI.

    Returns:
        str: The combined LaTeX content as a data URL.
    """
    combined_content = start_content + '\n' + generated_content

    # Save to a .tex file
    resume_tex_path = "generated_resume.tex"
    with open(resume_tex_path, 'w') as f:
        f.write(combined_content)

    # Compile LaTeX to PDF
    pdf_path = compile_latex_to_pdf(combined_content, "Generated Resume")

    return pdf_path  # Return the PDF path


def combine_and_save_latex_cover_letter(start_content: str,
                                        generated_content: str) -> str:
    """
    Combine the start and generated LaTeX content for the cover letter and encode it.

    Args:
        start_content (str): The starting LaTeX template content.
        generated_content (str): The generated LaTeX content from OpenAI.

    Returns:
        str: The combined LaTeX content as a data URL.
    """
    combined_content = start_content + '\n' + generated_content

    # Save to a .tex file
    cover_letter_tex_path = "generated_cover_letter.tex"
    with open(cover_letter_tex_path, 'w') as f:
        f.write(combined_content)

    # Compile LaTeX to PDF
    pdf_path = compile_latex_to_pdf(combined_content, "Generated Cover Letter")

    return pdf_path  # Return the PDF path


def compile_latex_to_pdf(latex_content: str, document_name: str) -> str:
    """
    Compile LaTeX content to PDF.

    Args:
        latex_content (str): The LaTeX content to compile.
        document_name (str): The name of the document (used for the PDF file).

    Returns:
        str: The path to the compiled PDF file or None if compilation fails.
    """
    try:
        # Save LaTeX content to a temporary .tex file
        tex_file = f"{document_name}.tex"
        with open(tex_file, 'w') as f:
            f.write(latex_content)

        # Compile the .tex file to PDF using pdflatex
        compile_command = ["pdflatex", "-interaction=nonstopmode", tex_file]
        subprocess.run(compile_command,
                       check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Check if PDF was created
        pdf_file = f"{document_name}.pdf"
        if os.path.exists(pdf_file):
            print(f"[Debug] PDF compiled successfully: {pdf_file}")
            return pdf_file
        else:
            print(f"[Error] PDF compilation failed for {tex_file}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"[Error] LaTeX compilation error: {e.stderr.decode()}")
        return None
    finally:
        # Clean up auxiliary files generated by pdflatex
        for ext in ['aux', 'log', 'out']:
            aux_file = f"{document_name}.{ext}"
            if os.path.exists(aux_file):
                os.remove(aux_file)
