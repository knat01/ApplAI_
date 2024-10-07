# resume_cover_letter_generation.py

import openai
import os
import logging
import time  # For sleep in generation functions
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_latex_resume_assistant(api_key: str):
    """
    Create a LaTeX Resume Content Integrator assistant using OpenAI's beta API.

    Args:
        api_key (str): OpenAI API key.

    Returns:
        assistant: The created assistant object.
    """
    try:
        client = openai.Client(
            api_key=api_key)  # Initialize OpenAI client with API key
        assistant = client.beta.assistants.create(
            model="gpt-4o-mini",
            name="LaTeX Resume Content Integrator",
            instructions=
            ("""Integrate the user's resume details into the 'latex_resume_end_template', adhering strictly to its structure and format.
Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
Focus on the Experience, Education, Projects, and Technical Skills sections, using the user's resume information.
Avoid any unicode characters and extra LaTeX commands not present in the template.
If specific data (like project dates) are absent in the user's resume, omit those elements from the template. 
Highlight in bold any resume content that matches key terms in the job description, particularly in the Experience and Projects sections. 
Tailor the resume to emphasize aspects relevant to the job description, without adding information not present in the user's resume.
The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete resume. 
Also, don't write 
latex at the start and
 at the end. 
Make sure to use only this apostrophe ' and only this dash - not any other ones."""
             ),
            tools=[])
        logger.info("[Info] LaTeX Resume Assistant created successfully.")
        return assistant
    except Exception as e:
        logger.exception(
            f"[Exception] Failed to create LaTeX Resume Assistant: {e}")
        return None


def create_latex_cover_letter_assistant(api_key: str):
    """
    Create a LaTeX Cover Letter Content Integrator assistant using OpenAI's beta API.

    Args:
        api_key (str): OpenAI API key.

    Returns:
        assistant: The created assistant object.
    """
    try:
        client = openai.Client(
            api_key=api_key)  # Initialize OpenAI client with API key
        assistant = client.beta.assistants.create(
            model="gpt-4o-mini",
            name="LaTeX Cover Letter Content Integrator",
            instructions=
            ("""Integrate the user's resume details and job description into the 'latex_cover_letter_end_template', adhering strictly to its structure and format.
Start from \\begin{document}, and ensure the content aligns with the provided LaTeX commands and sections.
Focus on creating a compelling introduction, highlighting relevant skills and experiences, and expressing enthusiasm for the position and company.
Avoid any unicode characters and extra LaTeX commands not present in the template.
If specific data is absent in the user's resume or job description, gracefully handle the omission. 
The output should form a one-page, fully formatted LaTeX document, ready to merge into a complete cover letter. 
Do not write 
latex at the start and
 at the end. 
Make sure to use only this apostrophe ' and only this dash - not any other ones."""
             ),
            tools=[])
        logger.info(
            "[Info] LaTeX Cover Letter Assistant created successfully.")
        return assistant
    except Exception as e:
        logger.exception(
            f"[Exception] Failed to create LaTeX Cover Letter Assistant: {e}")
        return None


def save_latex_file(file_path: str, latex_content: str):
    """
    Saves the LaTeX content to a .tex file.

    Args:
        file_path (str): Path where the LaTeX file will be saved.
        latex_content (str): The LaTeX content to be written.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(latex_content)
        logger.info(f"LaTeX file saved successfully at {file_path}")
    except Exception as e:
        logger.exception(f"Error saving LaTeX file: {e}")


def generate_latex_resume(user_resume: str, job_description: str,
                          template_start_path: str, template_end_path: str,
                          assistant_id: str, api_key: str) -> Dict[str, str]:
    """
    Generate a tailored LaTeX resume based on the user's resume and job description.

    Args:
        user_resume (str): The user's resume text.
        job_description (str): The job description text.
        template_start_path (str): Path to the LaTeX resume start template.
        template_end_path (str): Path to the LaTeX resume end template.
        assistant_id (str): The ID of the created assistant.
        api_key (str): OpenAI API key.

    Returns:
        dict: Contains 'tex_path' and 'tex_content' if successful, else 'error'.
    """
    try:
        client = openai.Client(
            api_key=api_key)  # Initialize OpenAI client with API key
        logger.debug("[Debug] Creating a thread for resume generation...")
        thread = client.beta.threads.create()
        thread_id = thread.id
        logger.debug(f"[Debug] Thread created with ID: {thread_id}")

        logger.debug("[Debug] Adding messages to the thread...")
        messages = [{
            "role": "user",
            "content": user_resume
        }, {
            "role": "user",
            "content": job_description
        }]
        for message in messages:
            logger.debug(
                f"[Debug] Adding message with role '{message['role']}'")
            client.beta.threads.messages.create(thread_id=thread_id,
                                                role=message["role"],
                                                content=message["content"])

        logger.debug(
            "[Debug] Running the assistant with the created thread...")
        run = client.beta.threads.runs.create(thread_id=thread_id,
                                              assistant_id=assistant_id)

        while run.status in ['queued', 'in_progress']:
            logger.debug(
                f"[Debug] Waiting for run to complete... Status: {run.status}")
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                    run_id=run.id)

        logger.debug(f"[Debug] Run status after completion: {run.status}")
        if run.status == 'completed':
            logger.debug("[Debug] Run completed. Fetching messages...")
            messages = client.beta.threads.messages.list(thread_id=thread_id)

            for message in messages.data:
                logger.debug(f"[Debug] Message role: {message.role}")
                if message.role == "assistant":
                    logger.debug(
                        "[Debug] Assistant message found. Checking for LaTeX content..."
                    )
                    response_text = ""
                    if isinstance(message.content, list):
                        for part in message.content:
                            if hasattr(part, 'text') and hasattr(
                                    part.text, 'value'):
                                response_text += part.text.value
                    elif hasattr(message.content, 'text') and hasattr(
                            message.content.text, 'value'):
                        response_text = message.content.text.value

                    response_text = response_text.strip()
                    logger.debug(
                        f"[Debug] Assistant LaTeX response:\n{response_text}")

                    if response_text:
                        # Combine templates with generated content
                        full_latex = ""
                        try:
                            with open(template_start_path, 'r') as f:
                                full_latex += f.read() + "\n"
                            full_latex += response_text + "\n"
                            with open(template_end_path, 'r') as f:
                                full_latex += f.read()
                        except Exception as e:
                            logger.exception(
                                f"[Exception] Error reading templates: {e}")
                            return {"error": f"Error reading templates: {e}"}

                        # Save the LaTeX content to a file
                        output_dir = "generated_documents"
                        os.makedirs(output_dir, exist_ok=True)

                        # Determine the filename based on the template type
                        tex_filename = f"resume_{int(time.time())}.tex"
                        tex_file_path = os.path.join(output_dir, tex_filename)

                        # Save the combined LaTeX to a .tex file
                        save_latex_file(tex_file_path, full_latex)

                        # Read the .tex content to provide for download
                        try:
                            with open(tex_file_path, 'r') as f:
                                tex_content = f.read()

                            # Verify the content matches
                            if tex_content != full_latex:
                                logger.warning(
                                    "Mismatch detected between written and read LaTeX content."
                                )

                            return {
                                "tex_path": tex_file_path,
                                "tex_content": tex_content
                            }
                        except Exception as e:
                            logger.exception(
                                f"[Exception] Error reading saved LaTeX file: {e}"
                            )
                            return {
                                "error": f"Error reading saved LaTeX file: {e}"
                            }
        else:
            logger.debug(
                f"[Debug] Run did not complete successfully. Status: {run.status}"
            )

        logger.debug(
            "[Debug] No valid LaTeX content found or run did not complete successfully."
        )
        return {
            "error":
            "No LaTeX content generated or run did not complete successfully."
        }

    except Exception as e:
        logger.exception(
            f"[Exception] An error occurred during resume generation: {str(e)}"
        )
        return {"error": str(e)}


def generate_latex_cover_letter(user_resume: str, job_description: str,
                                template_start_path: str,
                                template_end_path: str, assistant_id: str,
                                api_key: str) -> Dict[str, str]:
    """
    Generate a tailored LaTeX cover letter based on the user's resume and job description.

    Args:
        user_resume (str): The user's resume text.
        job_description (str): The job description text.
        template_start_path (str): Path to the LaTeX cover letter start template.
        template_end_path (str): Path to the LaTeX cover letter end template.
        assistant_id (str): The ID of the created assistant.
        api_key (str): OpenAI API key.

    Returns:
        dict: Contains 'tex_path' and 'tex_content' if successful, else 'error'.
    """
    try:
        client = openai.Client(
            api_key=api_key)  # Initialize OpenAI client with API key
        logger.debug(
            "[Debug] Creating a thread for cover letter generation...")
        thread = client.beta.threads.create()
        thread_id = thread.id
        logger.debug(f"[Debug] Thread created with ID: {thread_id}")

        logger.debug("[Debug] Adding messages to the thread...")
        messages = [{
            "role": "user",
            "content": user_resume
        }, {
            "role": "user",
            "content": job_description
        }]
        for message in messages:
            logger.debug(
                f"[Debug] Adding message with role '{message['role']}'")
            client.beta.threads.messages.create(thread_id=thread_id,
                                                role=message["role"],
                                                content=message["content"])

        logger.debug(
            "[Debug] Running the assistant with the created thread...")
        run = client.beta.threads.runs.create(thread_id=thread_id,
                                              assistant_id=assistant_id)

        while run.status in ['queued', 'in_progress']:
            logger.debug(
                f"[Debug] Waiting for run to complete... Status: {run.status}")
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                    run_id=run.id)

        logger.debug(f"[Debug] Run status after completion: {run.status}")
        if run.status == 'completed':
            logger.debug("[Debug] Run completed. Fetching messages...")
            messages = client.beta.threads.messages.list(thread_id=thread_id)

            for message in messages.data:
                logger.debug(f"[Debug] Message role: {message.role}")
                if message.role == "assistant":
                    logger.debug(
                        "[Debug] Assistant message found. Checking for LaTeX content..."
                    )
                    response_text = ""
                    if isinstance(message.content, list):
                        for part in message.content:
                            if hasattr(part, 'text') and hasattr(
                                    part.text, 'value'):
                                response_text += part.text.value
                    elif hasattr(message.content, 'text') and hasattr(
                            message.content.text, 'value'):
                        response_text = message.content.text.value

                    response_text = response_text.strip()
                    logger.debug(
                        f"[Debug] Assistant LaTeX response:\n{response_text}")

                    if response_text:
                        # Combine templates with generated content
                        full_latex = ""
                        try:
                            with open(template_start_path, 'r') as f:
                                full_latex += f.read() + "\n"
                            full_latex += response_text + "\n"
                            with open(template_end_path, 'r') as f:
                                full_latex += f.read()
                        except Exception as e:
                            logger.exception(
                                f"[Exception] Error reading templates: {e}")
                            return {"error": f"Error reading templates: {e}"}

                        # Save the LaTeX content to a file
                        output_dir = "generated_documents"
                        os.makedirs(output_dir, exist_ok=True)

                        # Determine the filename based on the template type
                        tex_filename = f"cover_letter_{int(time.time())}.tex"
                        tex_file_path = os.path.join(output_dir, tex_filename)

                        # Save the combined LaTeX to a .tex file
                        save_latex_file(tex_file_path, full_latex)

                        # Read the .tex content to provide for download
                        try:
                            with open(tex_file_path, 'r') as f:
                                tex_content = f.read()

                            # Verify the content matches
                            if tex_content != full_latex:
                                logger.warning(
                                    "Mismatch detected between written and read LaTeX content."
                                )

                            return {
                                "tex_path": tex_file_path,
                                "tex_content": tex_content
                            }
                        except Exception as e:
                            logger.exception(
                                f"[Exception] Error reading saved LaTeX file: {e}"
                            )
                            return {
                                "error": f"Error reading saved LaTeX file: {e}"
                            }
        else:
            logger.debug(
                f"[Debug] Run did not complete successfully. Status: {run.status}"
            )

        logger.debug(
            "[Debug] No valid LaTeX content found or run did not complete successfully."
        )
        return {
            "error":
            "No LaTeX content generated or run did not complete successfully."
        }

    except Exception as e:
        logger.exception(
            f"[Exception] An error occurred during cover letter generation: {str(e)}"
        )
        return {"error": str(e)}