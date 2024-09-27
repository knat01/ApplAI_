// Content script for Job Application Auto-Fill extension

// Function to auto-fill form fields
function autoFillForm(userData) {
  const fieldMappings = {
    'name': ['name', 'full-name', 'fullname'],
    'email': ['email', 'e-mail'],
    'phone': ['phone', 'telephone', 'mobile'],
    'address': ['address', 'street-address'],
    'city': ['city', 'town'],
    'state': ['state', 'province'],
    'zip': ['zip', 'postal-code', 'zipcode'],
    'job-title': ['job-title', 'position', 'desired-position'],
    'salary': ['salary', 'desired-salary', 'expected-salary'],
    'start-date': ['start-date', 'availability', 'available-start-date'],
    'resume': ['resume', 'cv', 'upload-resume']
  };

  for (const [key, selectors] of Object.entries(fieldMappings)) {
    for (const selector of selectors) {
      const field = document.querySelector(`input[name*="${selector}" i], textarea[name*="${selector}" i]`);
      if (field && userData[key]) {
        field.value = userData[key];
        field.dispatchEvent(new Event('change', { bubbles: true }));
        break;
      }
    }
  }
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'autoFill') {
    autoFillForm(request.userData);
    sendResponse({ success: true });
  }
});
