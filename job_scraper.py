#job_scraper.py

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


def get_job_link_from_resume(resume_text: str) -> str:
    """
    Generate a job search URL based on the user's resume using OpenAI's Chat API.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        str: A URL string for job searching on the Canada Job Bank.
    """
    client = openai.Client(api_key=st.session_state['api_key'])
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
    except RequestException as e:
        logger.error(f"RequestException while generating job search URL: {e}")
    except Exception as e:
        logger.error(f"Unexpected error generating job search URL: {e}")
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

        # Use OpenAI to extract job listings from the content
        client = openai.Client(api_key=st.session_state['api_key'])
        prompt = (
            """Extract ALL job postings from the provided content with the following details for each:
            - Job Title
            - Company Name
            - Job URL (direct link to the job posting)
            - Location
            - Full Job Description (Extract the complete job description)
            - Posting Date (if available)

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
            """)

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
        logger.debug(f"OpenAI Response for Job Listings: {response_content}")

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
    if 'api_key' not in st.session_state or not st.session_state['api_key']:
        logger.error("Error: OpenAI API key is missing in session state.")
        return []

    job_search_url = get_job_link_from_resume(resume_text)
    if not job_search_url:
        logger.error("Error: Failed to generate job search URL.")
        return []

    job_postings = scrape_job_listings(job_search_url)
    return job_postings


def generate_job_titles_from_resume(resume_text: str) -> List[str]:
    """
    Generate relevant job titles based on the user's resume using OpenAI's Chat API.

    Args:
        resume_text (str): The extracted text from the user's resume.

    Returns:
        List[str]: A list of job titles.
    """
    client = openai.Client(api_key=st.session_state['api_key'])
    prompt = (
        "Based on the following resume text, provide a list of 5 relevant job titles "
        "that the candidate is suitable for. Focus on common job titles that employers might use. "
        "Only return the list of job titles in JSON array format.")
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(model="gpt-3.5-turbo",
                                                      messages=[{
                                                          "role":
                                                          "system",
                                                          "content":
                                                          prompt
                                                      }, {
                                                          "role":
                                                          "user",
                                                          "content":
                                                          resume_text
                                                      }],
                                                      temperature=0.7)
            titles_text = response.choices[0].message.content.strip()

            # Log the raw OpenAI response for debugging
            logger.debug(f"OpenAI Response for Job Titles: {titles_text}")

            # Remove code block markers if present
            titles_text = re.sub(r'^```json\s*|\s*```$', '', titles_text)

            # Check if the response is empty
            if not titles_text:
                raise ValueError(
                    "OpenAI returned an empty response for job titles.")

            job_titles = json.loads(titles_text)
            logger.info(f"Generated job titles: {job_titles}")
            return job_titles
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from OpenAI response: {e}")
            logger.error(f"Problematic content: {titles_text}")
            break  # No point retrying if JSON is malformed
        except RequestException as e:
            logger.error(f"RequestException while generating job titles: {e}")
        except Exception as e:
            logger.error(f"Unexpected error generating job titles: {e}")

        # Exponential backoff before retrying
        sleep_time = backoff_factor**attempt
        logger.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)

    logger.error(
        "Error: Failed to generate job titles from resume after retries.")
    return []


def construct_google_search_queries(job_titles: List[str],
                                    location: str) -> List[str]:
    """
    Construct Google search queries based on job titles and location.

    Args:
        job_titles (List[str]): List of job titles.
        location (str): Preferred location.

    Returns:
        List[str]: List of search queries.
    """
    queries = []
    for title in job_titles:
        query = f'site:lever.co "{title}" -senior (junior OR ) "{location}"'
        queries.append(query)
        logger.debug(f"Constructed search query: {query}")
    return queries


def perform_google_searches(google_api_key: str, cx: str,
                            queries: List[str]) -> List[str]:
    """
    Perform Google searches for each query and collect URLs from the results.

    Args:
        google_api_key (str): Google API Key.
        cx (str): Google Custom Search Engine ID.
        queries (List[str]): List of search queries.

    Returns:
        List[str]: List of URLs collected from search results.
    """
    all_urls = []
    for query in queries:
        params = {
            "key": google_api_key,
            "cx": cx,
            "q": query,
            "num": 10  # Get up to 10 results per query
        }
        try:
            response = requests.get(
                "https://www.googleapis.com/customsearch/v1", params=params)
            response.raise_for_status()
            data = response.json()
            urls = [item['link'] for item in data.get('items', [])]
            all_urls.extend(urls)
            logger.info(f"Found {len(urls)} URLs for query '{query}'")
            time.sleep(1)  # Sleep to respect rate limits
        except RequestException as e:
            logger.error(
                f"RequestException performing search for query '{query}': {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error performing search for query '{query}': {e}")
    return all_urls


def extract_job_info_from_content(content: str, url: str) -> Dict:
    """
    Extract job information from the web page content using OpenAI's Chat API.

    Args:
        content (str): HTML content of the job page.
        url (str): URL of the job page.

    Returns:
        Dict: Dictionary containing job information.
    """
    client = openai.Client(api_key=st.session_state['api_key'])
    prompt = (
        "Extract the job posting details from the provided web page content. "
        "Return the following fields in JSON format: "
        "Job Title, Company Name, Location, Full Job Description. "
        "Use the URL provided as the Application Page Link.")
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(model='gpt-3.5-turbo',
                                                      messages=[{
                                                          "role":
                                                          "system",
                                                          "content":
                                                          prompt
                                                      }, {
                                                          "role":
                                                          "user",
                                                          "content":
                                                          content
                                                      }],
                                                      temperature=0.7)
            job_info_text = response.choices[0].message.content.strip()

            # Log the raw OpenAI response for debugging
            logger.debug(f"OpenAI Response for Job Info: {job_info_text}")

            # Remove code block markers if present
            job_info_text = re.sub(r'^```json\s*|\s*```$', '', job_info_text)

            # Check if the response is empty
            if not job_info_text:
                raise ValueError(
                    "OpenAI returned an empty response for job info.")

            job_info = json.loads(job_info_text)
            job_info['Application Page Link'] = url
            logger.info(f"Extracted job info from {url}")
            return job_info
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from OpenAI response: {e}")
            logger.error(f"Problematic content: {job_info_text}")
            break  # No point retrying if JSON is malformed
        except RequestException as e:
            logger.error(
                f"RequestException extracting job info from '{url}': {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error extracting job info from '{url}': {e}")

        # Exponential backoff before retrying
        sleep_time = backoff_factor**attempt
        logger.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)

    logger.error(
        f"Error: Failed to extract job info from '{url}' after retries.")
    return None


def extract_job_information(urls: List[str]) -> List[Dict]:
    """
    Extract job information from a list of URLs.

    Args:
        urls (List[str]): List of job URLs.

    Returns:
        List[Dict]: List of job postings.
    """
    job_postings = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            # Use OpenAI to extract job info
            job_info = extract_job_info_from_content(content, url)
            if job_info:
                job_postings.append(job_info)
            time.sleep(1)  # Sleep to respect rate limits
        except RequestException as e:
            logger.error(f"RequestException fetching URL '{url}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing URL '{url}': {e}")
    logger.info(f"Extracted job information from {len(job_postings)} URLs.")
    return job_postings


def google_search_scrape(resume_text: str, location: str, api_key: str,
                         google_api_key: str, google_cx: str) -> List[Dict]:
    """
    Main function to perform Google Search Scrape based on the user's resume.

    Args:
        resume_text (str): The extracted text from the user's resume.
        location (str): Preferred job location.
        api_key (str): OpenAI API Key.
        google_api_key (str): Google Custom Search API Key.
        google_cx (str): Google Custom Search Engine ID.

    Returns:
        List[Dict]: List of job postings.
    """
    if not api_key or not google_api_key or not google_cx:
        logger.error("Error: Missing API keys for OpenAI or Google.")
        return []

    # Generate job titles from resume
    job_titles = generate_job_titles_from_resume(resume_text)
    if not job_titles:
        logger.error("Error: Failed to generate job titles from resume.")
        return []

    # Construct search queries
    queries = construct_google_search_queries(job_titles, location)

    # Perform Google searches and collect URLs
    urls = perform_google_searches(google_api_key, google_cx, queries)
    if not urls:
        logger.error("Error: No URLs found from Google searches.")
        return []

    # Extract job information from URLs
    job_postings = extract_job_information(urls)
    logger.info(f"Extracted {len(job_postings)} job postings.")
    return job_postings


def test_google_custom_search_api(api_key: str, cx: str) -> (bool, str):
    """
    Test the Google Custom Search API credentials by performing a simple search.

    Args:
        api_key (str): Google Custom Search API key.
        cx (str): Custom Search Engine ID.

    Returns:
        tuple: (is_valid (bool), message (str))
    """
    test_query = "Software Developer"
    search_url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": api_key,
        "cx": cx,
        "q": test_query,
        "num": 1  # Limit to 1 result for testing
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            logger.info("Google Custom Search API credentials are valid.")
            return True, "API key and CX ID are valid."
        else:
            logger.warning("Google Custom Search API returned no results.")
            return False, "API key and CX ID are valid, but no results were returned."

    except RequestException as e:
        logger.error(f"RequestException testing Google API: {e}")
        return False, f"Request exception: {e}"
    except Exception as e:
        logger.error(f"Unexpected error testing Google API: {e}")
        return False, f"An unexpected error occurred: {e}"
