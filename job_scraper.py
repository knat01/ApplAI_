# job_scraper.py

import os
import openai
from scrapegraphai.graphs import SmartScraperGraph
import streamlit as st
import json


def get_job_link_from_resume(resume_text):
    """
    Generate a job search URL based on the user's resume using OpenAI's Chat API.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        str: A URL string for job searching on the Canada Job Bank.
    """
    client = openai.Client(api_key=st.session_state['api_key'])
    prompt = "You are a link creation bot. ONLY RESPOND WITH LINK. You will be making the link based on the resume that the user provides. Don't say here's the link or anything like that, just the link and only the link should be returned back. ONLY THE LINK NEEDS TO BE RETURNED. You will be responding only with Canada job bank links and nothing else. Here are some example links: This one is for a software developer in Toronto: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=software+developer&locationstring=toronto, This one is for a receptionist located in Alberta: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=receptionist&locationstring=alberta . If the resume is of a certain major like industrial engineering, for example, provide me the link for possible positions that the industrial engineer might work as and not just industrial engineer in the link. Another example is if someone is a full stack developer provide jobs for software developers since it has more results."

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
        print(f"Generated Job Search URL: {job_search_url}")
        return job_search_url
    except Exception as e:
        print(f"Error generating job search URL: {e}")
        return None


def scrape_job_listings(job_search_url):
    """
    Scrape job listings from the Canada Job Bank using ScrapeGraph-AI.

    Args:
        job_search_url (str): The URL to scrape job listings from.

    Returns:
        list: A list of dictionaries containing job postings.
    """
    graph_config = {
        "llm": {
            "api_key": st.session_state['api_key'],
            "model": "openai/gpt-3.5-turbo",
        },
        "verbose": True,
        "headless": True,
    }

    prompt = """Extract the first 25 job postings from the Canada Job Bank with the following details for each:
        - Job Title
        - Company Name
        - Job URL (direct link to the job posting)
        - Location
        - Full Job Description (Extract the complete job description)
        - Posting Date (if available)
        Return the results in a JSON format with a list of job postings."""

    try:
        # Set the OpenAI API key in the environment variable for ScrapeGraph-AI
        os.environ["OPENAI_API_KEY"] = st.session_state['api_key']

        scraper = SmartScraperGraph(
            prompt=prompt,
            source=job_search_url,
            config=graph_config,
        )

        result = scraper.run()

        if isinstance(result, str):
            result = json.loads(result)

        if not isinstance(result, dict):
            print(f"Unexpected result type: {type(result)}")
            return []

        job_postings = result.get('job_postings', [])[:25]
        print(f"Scraped {len(job_postings)} job postings.")
        return job_postings

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error scraping job listings: {e}")

    return []


def scrape_jobs(resume_text):
    """
    Main function to scrape jobs based on the user's resume.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        list: A list of job postings with relevant details.
    """
    if 'api_key' not in st.session_state or not st.session_state['api_key']:
        print("Error: OpenAI API key is missing in session state.")
        return []

    job_search_url = get_job_link_from_resume(resume_text)
    if not job_search_url:
        print("Error: Failed to generate job search URL.")
        return []

    job_postings = scrape_job_listings(job_search_url)
    return job_postings
