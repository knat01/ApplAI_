# job_scraper.py

import openai
from scrapegraphai.graphs import SmartScraperGraph


def get_job_link_from_resume(resume_text, api_key):
    """
    Generate a job search URL based on the user's resume using OpenAI's Chat API.

    Args:
        resume_text (str): The extracted text from the user's resume.
        api_key (str): The OpenAI API key.

    Returns:
        str: A URL string for job searching on the Canada Job Bank.
    """
    client = openai.Client(api_key=api_key)
    prompt = "You are a link creation bot. ONLY RESPOND WITH LINK. You will be making the link based on the resume that the user provides. Don't say here's the link or anything like that, just the link and only the link should be returned back. ONLY THE LINK NEEDS TO BE RETURNED. You will be responding only with Canada job bank links and nothing else. Here are some example links: This one is for a software developer in Toronto: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=software+developer&locationstring=toronto, This one is for a receptionist located in Alberta: https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=receptionist&locationstring=alberta . If the resume is of a certain major like industrial engineering, for example, provide me the link for possible positions that the industrial engineer might work as and not just industrial engineer in the link. Another example is if someone is a full stack developer provide jobs for software developers since it has more results."

    try:
        # Create chat completion using OpenAI's API
        completion = client.chat.completions.create(model='gpt-4o',
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

        # Extract and return the job search URL from the response
        job_search_url = completion.choices[0].message.content.strip()
        print(f"Generated Job Search URL: {job_search_url}")
        return job_search_url
    except openai.APIError as e:
        print(f"OpenAI API returned an API Error: {e}")
    except openai.APIConnectionError as e:
        print(f"Failed to connect to OpenAI API: {e}")
    except openai.RateLimitError as e:
        print(f"OpenAI API request exceeded rate limit: {e}")
    except Exception as e:
        print(f"Error generating job search URL: {e}")

    return None


def scrape_job_listings(job_search_url, api_key):
    """
    Scrape job listings from the Canada Job Bank using ScrapeGraph-AI.

    Args:
        job_search_url (str): The URL to scrape job listings from.
        api_key (str): The OpenAI API key.

    Returns:
        list: A list of dictionaries containing job postings.
    """
    graph_config = {
        "llm": {
            "api_key": api_key,
            "model": "gpt-4o",
        },
        "verbose": True,
        "headless": True,
    }

    scraper = SmartScraperGraph(
        prompt=
        """Extract the first 25 job postings from the Canada Job Bank with the following details for each:
        - Job Title
        - Company Name
        - Job URL (direct link to the job posting)
        - Location
        - Full Job Description (Extract the complete job description)
        - Posting Date (if available)
        Return the results in a JSON format with a list of job postings.""",
        source=job_search_url,
        config=graph_config,
    )

    try:
        result = scraper.run()
        job_postings = result.get('job_postings',
                                  [])[:25]  # Get the first 25 job postings
        print(f"Scraped {len(job_postings)} job postings.")
        return job_postings
    except Exception as e:
        print(f"Error scraping job listings: {e}")
        return []


def scrape_jobs(resume_text, api_key):
    """
    Main function to scrape jobs based on the user's resume and preferences.

    Args:
        resume_text (str): The extracted text from the user's resume.
        api_key (str): The OpenAI API key.

    Returns:
        list: A list of job postings with relevant details.
    """
    if not api_key:
        print("Error: OpenAI API key is missing.")
        return []

    # Generate job search URL from resume
    job_search_url = get_job_link_from_resume(resume_text, api_key)
    if not job_search_url:
        print("Error: Failed to generate job search URL.")
        return []

    # Scrape job listings using ScrapeGraph-AI
    job_postings = scrape_job_listings(job_search_url, api_key)
    return job_postings
