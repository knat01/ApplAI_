// Background script for Job Application Auto-Fill extension

// Function to fetch user data from the Streamlit app
async function fetchUserData() {
  try {
    const response = await fetch('http://localhost:5000/api/user_data');
    if (!response.ok) {
      throw new Error('Failed to fetch user data');
    }
    const userData = await response.json();
    return userData;
  } catch (error) {
    console.error('Error fetching user data:', error);
    return null;
  }
}

// Listen for messages from the popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getUserData') {
    fetchUserData().then(userData => {
      sendResponse({ userData: userData });
    });
    return true; // Indicates that the response is asynchronous
  }
});
