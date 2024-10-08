import os
import openai
import requests
import json
import streamlit as st
from typing import List, Dict
import re
import logging
import time
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress excessive watchdog logs
logging.getLogger("watchdog.observers.inotify_buffer").setLevel(
    logging.WARNING)

def get_openai_api_key():
    """
    Get the OpenAI API key from environment variables or session state.
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key and 'api_key' in st.session_state:
        api_key = st.session_state['api_key']
    return api_key

def get_job_link_from_resume(resume_text: str) -> str:
    """
    Generate a job search URL based on the user's resume using OpenAI's Chat API.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        str: A URL string for job searching on the Canada Job Bank.
    """
    api_key = get_openai_api_key()
    if not api_key:
        logger.error("OpenAI API key not found in environment variables or session state.")
        return None

    client = openai.Client(api_key=api_key)
    prompt = (
        "You are a link creation bot. ONLY RESPOND WITH LINK. You will be making the link based on the resume that the user provides. "
        "Don't say here's the link or anything like that, just the link and only the link should be returned back. "
        "ONLY THE LINK NEEDS TO BE RETURNED. You will be responding only with Canada job bank links and nothing else. "
        "Here are some example links: "
        "This one is for a software developer in Toronto: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=software+developer&locationstring=toronto, "
        "This one is for a receptionist located in Alberta: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=receptionist&locationstring=alberta. "
        "If the resume is of a certain major like industrial engineering, for example, provide me the link for possible positions that the industrial engineer might work as and not just industrial engineer in the link. "
        "Another example is if someone is a full stack developer provide jobs for software developers since it has more results."
    )

    try:
        completion = client.chat.completions.create(model='gpt-3.5-turbo',
                                                    messages=[{
                                                        "role": "system",
                                                        "content": prompt
                                                    }, {
                                                        "role":
                                                        "user",
                                                        "content":
                                                        resume_text
                                                    }],
                                                    temperature=0.7)

        job_search_url = completion.choices[0].message.content.strip()
        logger.info(f"Generated Job Search URL: {job_search_url}")
        return job_search_url
    except Exception as e:
        logger.error(f"Error generating job search URL: {e}")
        return None

def scrape_job_listings(job_search_url: str) -> List[Dict]:
    """
    Scrape job listings from the Canada Job Bank using Jina AI's Reader API.

    Args:
        job_search_url (str): The URL to scrape job listings from.

    Returns:
        list: A list of dictionaries containing job postings.
    """
    jina_url = f"https://r.jina.ai/{job_search_url}"

    try:
        # Fetch the job search page content
        response = requests.get(jina_url)
        response.raise_for_status()
        content = response.text
        logger.info(f"Successfully fetched content. Length: {len(content)} characters")

        # Use OpenAI to extract job listings from the content
        api_key = get_openai_api_key()
        if not api_key:
            logger.error("OpenAI API key not found in environment variables or session state.")
            return []

        client = openai.Client(api_key=api_key)
        prompt = (
            """Extract ALL job postings from the provided content with the following details for each:
            - Job Title
            - Company Name
            - Job URL (direct link to the job posting)
            - Location
            - Full Job Description (Extract the COMPLETE and DETAILED job description, including all requirements, responsibilities, and any additional information provided)
            - Posting Date (if available)

            IMPORTANT: Ensure that the 'full_job_description' field contains the entire job description, not just a summary. Include all details provided in the job posting.

            Provide the results in a JSON format with a list of job postings, e.g.:
            {
                "job_postings": [
                    {
                        "job_title": "...",
                        "company_name": "...",
                        "job_url": "...",
                        "location": "...",
                        "full_job_description": "...",
                        "posting_date": "..."
                    },
                    ...
                ]
            }
            """
        )

        # Make a request to OpenAI's API
        completion = client.chat.completions.create(model='gpt-3.5-turbo',
                                                    messages=[{
                                                        "role": "system",
                                                        "content": prompt
                                                    }, {
                                                        "role":
                                                        "user",
                                                        "content":
                                                        content
                                                    }],
                                                    temperature=0.7)

        # Access the response from the OpenAI completion
        response_content = completion.choices[0].message.content

        # Log the raw OpenAI response for debugging
        logger.debug(f"OpenAI Response for Job Listings: {response_content[:500]}...")

        # Remove code block markers and any leading/trailing whitespace
        json_content = re.sub(r'^```json\s*|\s*```$', '',
                              response_content.strip())

        if not json_content:
            raise ValueError(
                "OpenAI returned an empty response for job listings.")

        # Parse the JSON content
        result = json.loads(json_content)

        # Validate if the result is a dictionary with 'job_postings' key
        if isinstance(result, dict) and 'job_postings' in result:
            job_postings = result['job_postings']
        elif isinstance(result, list):
            # Fallback if the response is just a list of job postings
            job_postings = result
        else:
            job_postings = []

        logger.info(f"Scraped {len(job_postings)} job postings.")
        return job_postings

    except RequestException as e:
        logger.error(f"Error fetching content from Jina AI: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.error(f"Problematic content: {response_content}")
    except Exception as e:
        logger.error(f"Error scraping job listings: {e}")

    return []

def scrape_jobs(resume_text: str) -> List[Dict]:
    """
    Main function to scrape jobs based on the user's resume.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        list: A list of job postings with relevant details.
    """
    job_search_url = get_job_link_from_resume(resume_text)
    if not job_search_url:
        logger.error("Error: Failed to generate job search URL.")
        return []

    job_postings = scrape_job_listings(job_search_url)
    
    # Print the entire job_postings list
    print("Job Postings:")
    print(json.dumps(job_postings, indent=2))
    
    return job_postings

if __name__ == "__main__":
    logger.info("Starting job scraping test...")
    
    # Check if the OpenAI API key is set
    api_key = get_openai_api_key()
    if not api_key:
        logger.error("OpenAI API key not found in environment variables or session state. Please set the OPENAI_API_KEY environment variable or add it to the Streamlit session state.")
    else:
        logger.info("OpenAI API key found.")
    
    sample_resume = """
    John Doe
    Software Developer
    123 Main St, Toronto, ON M5V 1A1
    john.doe@email.com | (123) 456-7890

    Summary:
    Experienced software developer with 5 years of experience in full-stack web development.

    Skills:
    - Programming Languages: Python, JavaScript, Java
    - Web Technologies: React, Node.js, Django
    - Databases: PostgreSQL, MongoDB
    - DevOps: Docker, Kubernetes, AWS

    Experience:
    Senior Software Developer | TechCorp, Toronto, ON | 2018 - Present
    - Developed and maintained large-scale web applications
    - Led a team of 5 developers in Agile environment

    Education:
    Bachelor of Science in Computer Science | University of Toronto | 2014 - 2018
    """
    
    job_postings = scrape_jobs(sample_resume)
    logger.info(f"Number of job postings scraped: {len(job_postings)}")
    logger.info("Job scraping test completed.")
