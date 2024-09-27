# Job Application AI Assistant

This project includes a Streamlit web application for managing job applications and a browser extension for auto-filling job application forms.

## Browser Extension Setup

To use the browser extension for auto-filling job applications, follow these steps:

1. Ensure that the Streamlit app is running and accessible.
2. Open your Chrome browser and navigate to `chrome://extensions`.
3. Enable "Developer mode" by toggling the switch in the top right corner.
4. Click on "Load unpacked" and select the `extension` folder from this project.
5. The Job Application Auto-Fill extension should now appear in your list of extensions.

## Using the Extension

1. Navigate to a job application form in your browser.
2. Click on the extension icon in your browser toolbar.
3. In the popup, click the "Fill Application Form" button.
4. The extension will attempt to auto-fill the form fields with your stored information.

Note: The extension uses a simplified form-filling logic and may not work perfectly on all websites. You may need to manually adjust some fields after auto-filling.

## Streamlit App

The Streamlit app allows you to:

1. Log in or create an account
2. Upload your resume
3. Enter job preferences
4. Scrape job listings
5. Generate tailored resumes and cover letters

To run the Streamlit app:

1. Ensure all required dependencies are installed.
2. Run `python main.py` in your terminal.
3. Open your browser and navigate to `http://localhost:5000`.

Remember to keep your personal information and API keys secure.
