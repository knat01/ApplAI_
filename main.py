# main.py

import streamlit as st
import firebase_auth
import resume_processing
import job_scraper
import resume_cover_letter_generation
import os

# Initialize session state
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None
if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = None
if 'job_listings' not in st.session_state:
    st.session_state['job_listings'] = []
if 'latex_resume_assistant_id' not in st.session_state:
    st.session_state['latex_resume_assistant_id'] = None
if 'latex_cover_letter_assistant_id' not in st.session_state:
    st.session_state['latex_cover_letter_assistant_id'] = None

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
            else:
                st.error("Invalid credentials or user does not exist.")
    with col2:
        if st.button("Sign Up"):
            user = firebase_auth.create_user(email, password)
            if user:
                st.session_state['user'] = user
                st.success("Account created successfully!")
            else:
                st.error(
                    "Failed to create account. Email might already be in use.")

# Main Application
if st.session_state['user']:
    st.write(f"Welcome, {st.session_state['user'].email}")

    # OpenAI API Key Input
    st.header("OpenAI API Key")
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if st.button("Save API Key"):
        if api_key:
            st.session_state['api_key'] = api_key
            st.success("API Key saved successfully!")
            # Optionally, create assistants here
            if not st.session_state.get('latex_resume_assistant_id'):
                assistant = resume_cover_letter_generation.create_latex_resume_assistant(api_key)
                st.session_state['latex_resume_assistant_id'] = assistant.id
            if not st.session_state.get('latex_cover_letter_assistant_id'):
                assistant = resume_cover_letter_generation.create_latex_cover_letter_assistant(api_key)
                st.session_state['latex_cover_letter_assistant_id'] = assistant.id
        else:
            st.error("Please enter a valid OpenAI API Key.")

    # Resume Upload
    st.header("Upload Your Resume")
    uploaded_file = st.file_uploader("Choose your resume file", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        resume_text = resume_processing.extract_text_from_resume(uploaded_file)
        if resume_text:
            st.session_state['resume_text'] = resume_text
            firebase_auth.save_user_data(st.session_state['user'].uid,
                                         {"resume_text": resume_text})
            st.success("Resume uploaded and processed successfully!")
            # Retrieve updated user data (without API key)
            user_data = firebase_auth.get_user_data(
                st.session_state['user'].uid)
            if user_data:
                st.session_state['resume_text'] = user_data.get('resume_text')
                st.write("Retrieved resume text from user data.")
            else:
                st.error(
                    "Failed to retrieve user data after uploading resume.")
        else:
            st.error("Failed to extract text from the uploaded resume.")

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
            # Retrieve updated user data
            user_data = firebase_auth.get_user_data(
                st.session_state['user'].uid)
            if user_data:
                st.session_state['job_preferences'] = user_data.get(
                    'preferences')
                st.write("Retrieved job preferences from user data.")
            else:
                st.error(
                    "Failed to retrieve user data after saving job preferences."
                )
        else:
            st.error("Please fill out all job preference fields.")

    # Job Scraping
    st.header("Job Scraping")
    if st.button("Scrape Job Listings"):
        if st.session_state['resume_text'] and st.session_state['api_key']:
            api_key = st.session_state['api_key']
            resume_text = st.session_state['resume_text']
            job_listings = job_scraper.scrape_jobs(resume_text)
            st.session_state['job_listings'] = job_listings
            st.success(f"Scraped {len(job_listings)} job listings!")
        else:
            st.error(
                "Please upload your resume and enter your OpenAI API Key first."
            )

    # Display Job Listings and Generate Resume/Cover Letter
    if st.session_state['job_listings']:
        st.header("Job Listings")
        for idx, job in enumerate(st.session_state['job_listings']):
            with st.expander(
                    f"Job {idx+1}: {job.get('Job Title', 'N/A')} at {job.get('Company Name', 'N/A')}"
            ):
                st.write(f"**Location:** {job.get('Location', 'N/A')}")
                st.write(
                    f"**Description:** {job.get('Full Job Description', 'N/A')[:200]}..."
                )
                st.write(f"**Job URL:** [Link]({job.get('Job URL', '#')})")

                # Display direct application link if available
                application_url = job.get('Application URL')
                if application_url:
                    st.write(f"**Apply directly:** [Apply Now]({application_url})")
                else:
                    st.write("Direct application link not available for this job.")

                # Separate buttons for generating resume and cover letter
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Generate Resume for Job {idx+1}"):
                        if st.session_state['api_key']:
                            latex_end_template = "Your LaTeX resume end template here."
                            resume_url = resume_cover_letter_generation.generate_latex_resume(
                                st.session_state['resume_text'],
                                job.get('Full Job Description', ''),
                                latex_end_template,
                                st.session_state['latex_resume_assistant_id'],
                                st.session_state['api_key']
                            )
                            if resume_url:
                                st.download_button("Download Resume",
                                                   resume_url,
                                                   file_name="resume.tex")
                            else:
                                st.error(
                                    "Failed to generate resume.")
                        else:
                            st.error("Please enter your OpenAI API Key first.")
                with col2:
                    if st.button(f"Generate Cover Letter for Job {idx+1}"):
                        if st.session_state['api_key']:
                            latex_cover_letter_end_template = "Your LaTeX cover letter end template here."
                            cover_letter_url = resume_cover_letter_generation.generate_latex_cover_letter(
                                st.session_state['resume_text'],
                                job.get('Full Job Description', ''),
                                latex_cover_letter_end_template,
                                st.session_state['latex_cover_letter_assistant_id'],
                                st.session_state['api_key']
                            )
                            if cover_letter_url:
                                st.download_button("Download Cover Letter",
                                                   cover_letter_url,
                                                   file_name="cover_letter.tex")
                            else:
                                st.error(
                                    "Failed to generate cover letter.")
                        else:
                            st.error("Please enter your OpenAI API Key first.")
                with col3:
                    if application_url:
                        if st.button(f"Apply to Job {idx+1}"):
                            st.write(f"Redirecting to application page: {application_url}")
                            # Note: In a real Streamlit app, you can't directly redirect.
                            # Instead, you might want to open the link in a new tab or provide instructions to the user.
                            st.markdown(f"[Click here to apply]({application_url})")
                    else:
                        st.write("Direct application not available")

    # Logout Button
    if st.button("Logout"):
        st.session_state['user'] = None
        st.session_state['api_key'] = None
        st.session_state['resume_text'] = None
        st.session_state['job_listings'] = []
        st.session_state['latex_resume_assistant_id'] = None
        st.session_state['latex_cover_letter_assistant_id'] = None
        st.success("Logged out successfully!")
        st.experimental_rerun()
