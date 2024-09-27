# main.py

import streamlit as st
from firebase_auth import save_user_data, get_user_data
import resume_processing
import resume_cover_letter_generation
import job_scraper

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = None

if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {}

# Page title
st.title('Job Application Assistant')

# User login or sign up
st.header('Login / Sign Up')
user_id = st.text_input('Enter your user ID (email)')
if st.button('Login'):
    st.session_state['user_id'] = user_id
    st.success(f'Logged in as {user_id}')

# Enter OpenAI API Key
st.header('Enter OpenAI API Key')
api_key = st.text_input('OpenAI API Key', type='password')
if st.button('Save API Key'):
    st.session_state['api_key'] = api_key
    st.success('API Key saved successfully')

# Upload Resume
st.header('Upload Your Resume')
uploaded_file = st.file_uploader('Choose your resume PDF file', type=['pdf'])
if uploaded_file is not None:
    resume_text = resume_processing.extract_text_from_pdf(uploaded_file)
    st.session_state['resume_text'] = resume_text
    st.success('Resume uploaded and processed successfully')

# Fill out Job Application Form
st.header('Job Application Preferences')
job_title = st.text_input('Desired Job Title')
location = st.text_input('Preferred Location')
salary_expectations = st.text_input('Salary Expectations')
availability = st.text_input('Availability')

if st.button('Save Job Preferences'):
    user_data = {
        'job_title': job_title,
        'location': location,
        'salary_expectations': salary_expectations,
        'availability': availability,
        'api_key': st.session_state['api_key']
    }
    st.session_state['user_data'] = user_data
    if 'user_id' in st.session_state:
        save_user_data(st.session_state['user_id'], user_data)
    st.success('Job preferences saved successfully')

# Scrape Job Listings
if st.button('Scrape Job Listings'):
    if st.session_state['resume_text'] and st.session_state['user_data']:
        job_listings = job_scraper.scrape_jobs(st.session_state['resume_text'], st.session_state['user_data'])
        st.session_state['job_listings'] = job_listings
        st.success('Job listings scraped successfully')
    else:
        st.error('Please upload your resume and fill out the job preferences form first')

# Display Job Listings
if 'job_listings' in st.session_state:
    st.header('Job Listings')
    job_list = st.session_state['job_listings']
    for idx, job in enumerate(job_list):
        st.subheader(f"Job {idx+1}")
        st.write(f"**Company:** {job['company_name']}")
        st.write(f"**Position:** {job['position']}")
        st.write(f"**Location:** {job['location']}")
        st.write(f"**Pay:** {job['pay']}")
        st.write(f"**Job Link:** {job['job_link']}")
        if st.button(f"Generate Resume and Cover Letter for Job {idx+1}", key=idx):
            # Generate resume and cover letter
            resume_pdf, cover_letter_pdf = resume_cover_letter_generation.generate_resume_and_cover_letter(
                st.session_state['resume_text'], job['job_description'], st.session_state['api_key']
            )
            if resume_pdf:
                st.download_button('Download Resume', resume_pdf, file_name='resume.tex')
            else:
                st.error('Failed to generate resume.')

            if cover_letter_pdf:
                st.download_button('Download Cover Letter', cover_letter_pdf, file_name='cover_letter.tex')
            else:
                st.error('Failed to generate cover letter.')
