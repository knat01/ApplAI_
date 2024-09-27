# job_scraper.py

import os
import openai
import requests
import json
import streamlit as st
from typing import List, Dict
import re


def get_job_link_from_resume(resume_text: str) -> str:
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
        response = requests.get(jina_url)
        response.raise_for_status()
        content = response.text

        # Use OpenAI to extract job listings from the content
        client = openai.Client(api_key=st.session_state['api_key'])
        prompt = """Extract ALL job postings from the provided content with the following details for each:
        - Job Title
        - Company Name
        - Job URL (direct link to the job posting)
        - Location
        - Full Job Description (Extract the complete job description)
        - Posting Date (if available)
        Return the results in a JSON format with a list of job postings."""

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

        # Access the content correctly from the completion object
        response_content = completion.choices[0].message.content

        # Remove code block markers and any leading/trailing whitespace
        json_content = re.sub(r'^```json\s*|\s*```$', '',
                              response_content.strip())

        result = json.loads(json_content)
        if isinstance(result, list):
            job_postings = result
        else:
            job_postings = result.get('job_postings', [])
        print(f"Scraped {len(job_postings)} job postings.")
        return job_postings

    except requests.RequestException as e:
        print(f"Error fetching content from Jina AI: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic content: {json_content}")
    except Exception as e:
        print(f"Error scraping job listings: {e}")

    return []


def scrape_jobs(resume_text: str) -> List[Dict]:
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
