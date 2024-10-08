# main.py

import streamlit as st
import firebase_auth  # Custom module for Firebase authentication
import resume_processing  # Custom module for processing resumes
import job_scraper  # Custom module for scraping jobs
import resume_cover_letter_generation  # The module we defined above
import os
import logging
from io import BytesIO
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress excessive watchdog logs
logging.getLogger("watchdog.observers.inotify_buffer").setLevel(
    logging.WARNING)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None
if 'google_api_key' not in st.session_state:
    st.session_state['google_api_key'] = None
if 'google_cx' not in st.session_state:
    st.session_state['google_cx'] = None
if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = None
if 'job_listings' not in st.session_state:
    st.session_state['job_listings'] = []
if 'resume_assistant_id' not in st.session_state:
    st.session_state['resume_assistant_id'] = None
if 'cover_letter_assistant_id' not in st.session_state:
    st.session_state['cover_letter_assistant_id'] = None
if 'scrape_method' not in st.session_state:
    st.session_state['scrape_method'] = "Canada Job Bank Scrape"
if 'job_preferences' not in st.session_state:
    st.session_state['job_preferences'] = {}

st.title("Job Application AI Assistant")

# User Authentication
if not st.session_state['user']:
    st.header("Login / Sign Up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user = firebase_auth.login_user(email, password)
            if user:
                st.session_state['user'] = user
                st.success("Logged in successfully!")
                logger.info(f"[Info] User {email} logged in.")
            else:
                st.error("Invalid credentials or user does not exist.")
                logger.warning(f"[Warning] Failed login attempt for {email}.")
    with col2:
        if st.button("Sign Up"):
            user = firebase_auth.create_user(email, password)
            if user:
                st.session_state['user'] = user
                st.success("Account created successfully!")
                logger.info(f"[Info] User {email} signed up successfully.")
            else:
                st.error(
                    "Failed to create account. Email might already be in use.")
                logger.warning(f"[Warning] Failed signup attempt for {email}.")

# Main Application
if st.session_state['user']:
    st.write(f"Welcome, {st.session_state['user'].email}")

    # OpenAI API Key Input
    st.header("OpenAI API Key")
    api_key_input = st.text_input("Enter your OpenAI API Key", type="password")
    if st.button("Save OpenAI API Key"):
        if api_key_input:
            st.session_state['api_key'] = api_key_input
            st.success("OpenAI API Key saved successfully!")
            logger.info("[Info] OpenAI API Key saved.")

            # Initialize LaTeX Templates
            resume_template_start = "templates/latex_resume_format_start.tex"
            resume_template_end = "templates/latex_resume_format_end.tex"
            cover_letter_template_start = "templates/latex_cover_letter_format_start.tex"
            cover_letter_template_end = "templates/latex_cover_letter_format_end.tex"

            # Check if templates exist
            missing_templates = []
            for path in [
                    resume_template_start, resume_template_end,
                    cover_letter_template_start, cover_letter_template_end
            ]:
                if not os.path.exists(path):
                    missing_templates.append(path)
            if missing_templates:
                st.error(
                    f"Missing template files: {', '.join(missing_templates)}")
                logger.error(
                    f"[Error] Missing template files: {', '.join(missing_templates)}"
                )
            else:
                # Create assistants if not already created
                if not st.session_state['resume_assistant_id']:
                    assistant = resume_cover_letter_generation.create_latex_resume_assistant(
                        api_key_input)
                    if assistant:
                        st.session_state['resume_assistant_id'] = assistant.id
                        logger.info(
                            f"[Info] LaTeX Resume Assistant ID: {assistant.id}"
                        )
                    else:
                        st.error("Failed to create LaTeX Resume Assistant.")
                        logger.error(
                            "[Error] Failed to create LaTeX Resume Assistant.")

                if not st.session_state['cover_letter_assistant_id']:
                    assistant = resume_cover_letter_generation.create_latex_cover_letter_assistant(
                        api_key_input)
                    if assistant:
                        st.session_state[
                            'cover_letter_assistant_id'] = assistant.id
                        logger.info(
                            f"[Info] LaTeX Cover Letter Assistant ID: {assistant.id}"
                        )
                    else:
                        st.error(
                            "Failed to create LaTeX Cover Letter Assistant.")
                        logger.error(
                            "[Error] Failed to create LaTeX Cover Letter Assistant."
                        )

                st.success(
                    "All templates are in place and assistants are ready.")
        else:
            st.error("Please enter a valid OpenAI API Key.")
            logger.warning("[Warning] Empty OpenAI API Key provided.")

    # Google Custom Search API Key Input
    st.header("Google Custom Search API")
    google_api_key_input = st.text_input(
        "Enter your Google Custom Search API Key", type="password")
    google_cx_input = st.text_input(
        "Enter your Google Custom Search Engine ID (CX)")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Save Google Custom Search API Key"):
            if google_api_key_input and google_cx_input:
                st.session_state['google_api_key'] = google_api_key_input
                st.session_state['google_cx'] = google_cx_input
                st.success(
                    "Google Custom Search API Key and CX ID saved successfully!"
                )
                logger.info(
                    "[Info] Google Custom Search API Key and CX ID saved.")
            else:
                st.error("Please enter both Google API Key and CX ID.")
                logger.warning(
                    "[Warning] Incomplete Google API credentials provided.")
    with col4:
        if st.button("Test Google Custom Search API"):
            if st.session_state['google_api_key'] and st.session_state[
                    'google_cx']:
                with st.spinner('Testing Google Custom Search API...'):
                    is_valid, message = job_scraper.test_google_custom_search_api(
                        api_key=st.session_state['google_api_key'],
                        cx=st.session_state['google_cx'])
                if is_valid:
                    st.success(
                        "Google Custom Search API Key and CX ID are valid!")
                    logger.info(
                        "[Info] Google Custom Search API credentials are valid."
                    )
                else:
                    st.error(
                        f"Google Custom Search API test failed: {message}")
                    logger.error(
                        f"[Error] Google Custom Search API test failed: {message}"
                    )
            else:
                st.error(
                    "Please enter and save your Google API Key and CX ID first."
                )
                logger.warning(
                    "[Warning] Google API test attempted without credentials.")

    # Resume Upload
    st.header("Upload Your Resume")
    uploaded_file = st.file_uploader("Choose your resume file",
                                     type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        resume_text = resume_processing.extract_text_from_resume(uploaded_file)
        if resume_text:
            st.session_state['resume_text'] = resume_text
            firebase_auth.save_user_data(st.session_state['user'].uid,
                                         {"resume_text": resume_text})
            st.success("Resume uploaded and processed successfully!")
            logger.info("[Info] Resume uploaded and text extracted.")

            # Retrieve updated user data (without API key)
            user_data = firebase_auth.get_user_data(
                st.session_state['user'].uid)
            if user_data:
                st.session_state['resume_text'] = user_data.get('resume_text')
                st.write("Retrieved resume text from user data.")
                logger.debug("[Debug] Resume text retrieved from user data.")
            else:
                st.error(
                    "Failed to retrieve user data after uploading resume.")
                logger.error(
                    "[Error] Failed to retrieve user data after resume upload."
                )
        else:
            st.error("Failed to extract text from the uploaded resume.")
            logger.error("[Error] Resume text extraction failed.")

    # Job Application Preferences Form
    st.header("Job Application Preferences")
    job_title = st.text_input("Desired Job Title")
    location = st.text_input("Preferred Location")
    salary_expectations = st.text_input("Salary Expectations")
    availability = st.text_input("Availability")

    if st.button("Save Job Preferences"):
        if job_title and location and salary_expectations and availability:
            preferences = {
                "job_title": job_title,
                "location": location,
                "salary_expectations": salary_expectations,
                "availability": availability
            }
            firebase_auth.save_user_data(st.session_state['user'].uid,
                                         {"preferences": preferences})
            st.success("Job preferences saved successfully!")
            logger.info("[Info] Job preferences saved.")

            # Retrieve updated user data
            user_data = firebase_auth.get_user_data(
                st.session_state['user'].uid)
            if user_data:
                st.session_state['job_preferences'] = user_data.get(
                    'preferences')
                st.write("Retrieved job preferences from user data.")
                logger.debug(
                    "[Debug] Job preferences retrieved from user data.")
            else:
                st.error(
                    "Failed to retrieve user data after saving job preferences."
                )
                logger.error(
                    "[Error] Failed to retrieve user data after saving job preferences."
                )
        else:
            st.error("Please fill out all job preference fields.")
            logger.warning(
                "[Warning] Incomplete job preference fields provided.")

    # Select Job Scraping Method
    st.header("Select Job Scraping Method")
    scrape_method = st.selectbox(
        "Choose a job scraping method:",
        ["Canada Job Bank Scrape", "Google Search Scrape"])
    st.session_state['scrape_method'] = scrape_method
    logger.info(f"[Info] User selected scraping method: {scrape_method}")

    # Job Scraping
    st.header("Job Scraping")
    if st.button("Scrape Job Listings"):
        if st.session_state['resume_text'] and st.session_state['api_key']:
            api_key = st.session_state['api_key']
            resume_text = st.session_state['resume_text']
            if st.session_state['scrape_method'] == "Canada Job Bank Scrape":
                with st.spinner(
                        'Scraping job listings from Canada Job Bank...'):
                    job_listings = job_scraper.scrape_jobs(resume_text)
                st.session_state['job_listings'] = job_listings
                st.success(
                    f"Scraped {len(job_listings)} job listings from Canada Job Bank!"
                )
                logger.info(
                    f"[Info] Scraped {len(job_listings)} job listings from Canada Job Bank."
                )
            elif st.session_state['scrape_method'] == "Google Search Scrape":
                if st.session_state['google_api_key'] and st.session_state[
                        'google_cx']:
                    with st.spinner(
                            'Scraping job listings using Google Search...'):
                        job_listings = job_scraper.google_search_scrape(
                            resume_text=resume_text,
                            location=st.session_state['job_preferences'].get(
                                'location', ''),
                            api_key=st.session_state['api_key'],
                            google_api_key=st.session_state['google_api_key'],
                            google_cx=st.session_state['google_cx'])
                    st.session_state['job_listings'] = job_listings
                    st.success(
                        f"Scraped {len(job_listings)} job listings using Google Search!"
                    )
                    logger.info(
                        f"[Info] Scraped {len(job_listings)} job listings using Google Search."
                    )
                else:
                    st.error(
                        "Please enter your Google API Key and CX ID first.")
                    logger.warning(
                        "[Warning] Google Search attempted without API credentials."
                    )
        else:
            st.error(
                "Please upload your resume and enter your OpenAI API Key first."
            )
            logger.warning(
                "[Warning] Job scraping attempted without resume or API Key.")

    # Display Job Listings and Generate Resume/Cover Letter
    if st.session_state['job_listings']:
        st.header("Job Listings")
        for idx, job in enumerate(st.session_state['job_listings']):
            with st.expander(
                    f"Job {idx+1}: {job.get('job_title', 'N/A')} at {job.get('company_name', 'N/A')}"
            ):
                # Enhanced formatting and display
                st.markdown(f"**🗺️ Location:** {job.get('location', 'N/A')}")
                st.markdown(f"**📝 Job Description:**")
                st.write(job.get('full_job_description', 'N/A'))
                st.markdown(f"**🔗 [Job URL]({job.get('job_url', '#')})**")

                # Separate sections for generating resume and cover letter
                st.markdown("---")
                st.markdown("### Generate Documents:")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Generate Resume for Job {idx+1}",
                                 key=f"generate_resume_{idx}"):
                        if st.session_state['api_key']:
                            # Paths to LaTeX templates
                            resume_start_template = "templates/latex_resume_format_start.tex"
                            resume_end_template = "templates/latex_resume_format_end.tex"

                            # Check if template files exist
                            if not os.path.exists(resume_start_template):
                                st.error(
                                    f"Resume start template not found at {resume_start_template}."
                                )
                                logger.error(
                                    f"[Error] Resume start template not found at {resume_start_template}."
                                )
                                continue
                            if not os.path.exists(resume_end_template):
                                st.error(
                                    f"Resume end template not found at {resume_end_template}."
                                )
                                logger.error(
                                    f"[Error] Resume end template not found at {resume_end_template}."
                                )
                                continue

                            # Check if assistant IDs are set
                            if not st.session_state['resume_assistant_id']:
                                st.error(
                                    "LaTeX Resume Assistant is not initialized. Please re-enter your API Key."
                                )
                                logger.error(
                                    "[Error] LaTeX Resume Assistant ID is not set."
                                )
                                continue

                            with st.spinner('Generating LaTeX resume...'):
                                # Generate LaTeX resume
                                result = resume_cover_letter_generation.generate_latex_resume(
                                    user_resume=st.
                                    session_state['resume_text'],
                                    job_description=job.get(
                                        'full_job_description', ''),
                                    template_start_path=resume_start_template,
                                    template_end_path=resume_end_template,
                                    assistant_id=st.
                                    session_state['resume_assistant_id'],
                                    api_key=st.session_state['api_key'])
                            if 'tex_content' in result:
                                tex_content = result['tex_content']
                                tex_filename = f"resume_{idx+1}.tex"

                                # Create a downloadable .tex file
                                st.download_button(
                                    label="Download Resume .tex File",
                                    data=tex_content,
                                    file_name=tex_filename,
                                    mime="application/x-tex",
                                )
                                st.success(
                                    "LaTeX resume generated successfully! Download the .tex file below and upload it to Overleaf."
                                )
                                logger.info(
                                    f"[Info] LaTeX resume generated: {tex_filename}"
                                )

                                # Provide a link to open Overleaf in a new tab
                                overleaf_url = "https://www.overleaf.com/"
                                st.markdown(
                                    f"[**Open Overleaf**]({overleaf_url}) to compile your resume."
                                )
                            else:
                                st.error(
                                    f"Failed to generate resume: {result.get('error', 'Unknown error')}"
                                )
                                logger.error(
                                    f"[Error] Resume generation failed: {result.get('error', 'Unknown error')}"
                                )
                        else:
                            st.error("Please enter your OpenAI API Key first.")
                            logger.warning(
                                "[Warning] Resume generation attempted without API Key."
                            )

                with col2:
                    if st.button(f"Generate Cover Letter for Job {idx+1}",
                                 key=f"generate_cover_letter_{idx}"):
                        if st.session_state['api_key']:
                            # Paths to LaTeX templates
                            cover_letter_start_template = "templates/latex_cover_letter_format_start.tex"
                            cover_letter_end_template = "templates/latex_cover_letter_format_end.tex"

                            # Check if template files exist
                            if not os.path.exists(cover_letter_start_template):
                                st.error(
                                    f"Cover letter start template not found at {cover_letter_start_template}."
                                )
                                logger.error(
                                    f"[Error] Cover letter start template not found at {cover_letter_start_template}."
                                )
                                continue
                            if not os.path.exists(cover_letter_end_template):
                                st.error(
                                    f"Cover letter end template not found at {cover_letter_end_template}."
                                )
                                logger.error(
                                    f"[Error] Cover letter end template not found at {cover_letter_end_template}."
                                )
                                continue

                            # Check if assistant IDs are set
                            if not st.session_state[
                                    'cover_letter_assistant_id']:
                                st.error(
                                    "LaTeX Cover Letter Assistant is not initialized. Please re-enter your API Key."
                                )
                                logger.error(
                                    "[Error] LaTeX Cover Letter Assistant ID is not set."
                                )
                                continue

                            with st.spinner(
                                    'Generating LaTeX cover letter...'):
                                # Generate LaTeX cover letter
                                result = resume_cover_letter_generation.generate_latex_cover_letter(
                                    user_resume=st.
                                    session_state['resume_text'],
                                    job_description=job.get(
                                        'full_job_description', ''),
                                    template_start_path=
                                    cover_letter_start_template,
                                    template_end_path=cover_letter_end_template,
                                    assistant_id=st.
                                    session_state['cover_letter_assistant_id'],
                                    api_key=st.session_state['api_key'])
                            if 'tex_content' in result:
                                tex_content = result['tex_content']
                                tex_filename = f"cover_letter_{idx+1}.tex"

                                # Create a downloadable .tex file
                                st.download_button(
                                    label="Download Cover Letter .tex File",
                                    data=tex_content,
                                    file_name=tex_filename,
                                    mime="application/x-tex",
                                )
                                st.success(
                                    "LaTeX cover letter generated successfully! Download the .tex file below and upload it to Overleaf."
                                )
                                logger.info(
                                    f"[Info] LaTeX cover letter generated: {tex_filename}"
                                )

                                # Provide a link to open Overleaf in a new tab
                                overleaf_url = "https://www.overleaf.com/"
                                st.markdown(
                                    f"[**Open Overleaf**]({overleaf_url}) to compile your cover letter."
                                )
                            else:
                                st.error(
                                    f"Failed to generate cover letter: {result.get('error', 'Unknown error')}"
                                )
                                logger.error(
                                    f"[Error] Cover Letter generation failed: {result.get('error', 'Unknown error')}"
                                )
                        else:
                            st.error("Please enter your OpenAI API Key first.")
                            logger.warning(
                                "[Warning] Cover Letter generation attempted without API Key."
                            )

    # Logout Button
    if st.button("Logout"):
        st.session_state['user'] = None
        st.session_state['api_key'] = None
        st.session_state['google_api_key'] = None
        st.session_state['google_cx'] = None
        st.session_state['resume_text'] = None
        st.session_state['job_listings'] = []
        st.session_state['resume_assistant_id'] = None
        st.session_state['cover_letter_assistant_id'] = None
        st.success("Logged out successfully!")
        logger.info("[Info] User logged out.")
        st.experimental_rerun()

    # Optional: Allow downloading all generated documents as a ZIP
    if st.session_state['job_listings']:
        st.header("Download All Generated Documents")
        if st.button("Download All as ZIP"):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                generated_folder = "generated_documents"
                for root, dirs, files in os.walk(generated_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, generated_folder)
                        zip_file.write(file_path, arcname=arcname)
            zip_buffer.seek(0)
            st.download_button(
                label="Download All Documents ZIP",
                data=zip_buffer,
                file_name="job_application_documents.zip",
                mime="application/zip",
            )
            st.success("ZIP file created successfully!")
            logger.info("[Info] ZIP file of generated documents created.")
