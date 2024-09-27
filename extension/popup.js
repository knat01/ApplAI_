// Popup script for Job Application Auto-Fill extension

document.addEventListener('DOMContentLoaded', function() {
  const autoFillBtn = document.getElementById('autoFillBtn');

  autoFillBtn.addEventListener('click', function() {
    chrome.runtime.sendMessage({ action: 'getUserData' }, function(response) {
      if (response.userData) {
        chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'autoFill', userData: response.userData });
        });
      } else {
        alert('Failed to fetch user data. Please make sure the Streamlit app is running.');
      }
    });
  });
});
