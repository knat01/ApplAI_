from scrapegraphai.graphs import SmartScraperGraph

def scrape_jobs(resume_text, user_data):
    try:
        api_key = user_data.get('api_key')
        preferences = user_data.get('preferences', {})
        job_title = preferences.get('job_title', '')
        location = preferences.get('location', '')

        graph_config = {
            "llm": {
                "api_key": api_key,
                "model": "gpt-4o",
            },
            "verbose": True,
            "headless": True,
        }

        scraper = SmartScraperGraph(
            prompt=f"""Scrape job listings for {job_title} in {location} from popular job boards.
            For each job listing, extract:
            - Job Title
            - Company Name
            - Location
            - Job Description (full)
            - Job URL
            Return the results as a list of dictionaries.""",
            source="https://www.indeed.com",  # You can add more job boards here
            config=graph_config,
        )

        result = scraper.run()
        return result.get('job_listings', [])
    except Exception as e:
        print(f"Error scraping jobs: {e}")
        return []
