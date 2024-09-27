chrome.runtime.onInstalled.addListener(function() {
  console.log("Job Application Auto-Fill extension installed.");
  
  // Fetch user data from the Streamlit app
  fetchUserData();
});

function fetchUserData() {
  // In a real-world scenario, you'd need to implement proper authentication
  // and securely store the user_id. This is a simplified example.
  const user_id = "example_user_id";
  const apiUrl = `http://localhost:5001/api/user_data?user_id=${user_id}`;

  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error("Error fetching user data:", data.error);
      } else {
        // Store user data in Chrome storage
        chrome.storage.sync.set(data, function() {
          console.log("User data stored in extension storage.");
        });
      }
    })
    .catch(error => {
      console.error("Error fetching user data:", error);
    });
}

// Periodically update user data (e.g., every hour)
setInterval(fetchUserData, 3600000);
