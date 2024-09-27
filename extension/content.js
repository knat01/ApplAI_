chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "fillForm") {
    fillApplicationForm();
  }
});

function fillApplicationForm() {
  // This is a simplified example. In a real-world scenario, you'd need to
  // handle various form structures and field types.
  const fieldMappings = {
    'name': ['name', 'full-name', 'fullName'],
    'email': ['email', 'e-mail', 'emailAddress'],
    'phone': ['phone', 'telephone', 'phoneNumber'],
    'address': ['address', 'streetAddress'],
    'city': ['city', 'town'],
    'state': ['state', 'province'],
    'zip': ['zip', 'zipCode', 'postalCode'],
    'country': ['country'],
    'education': ['education', 'degree'],
    'experience': ['experience', 'workExperience'],
    'skills': ['skills', 'techSkills']
  };

  chrome.storage.sync.get(null, function(data) {
    for (let [key, possibleFields] of Object.entries(fieldMappings)) {
      if (data[key]) {
        for (let fieldName of possibleFields) {
          let field = document.querySelector(`input[name*="${fieldName}" i], textarea[name*="${fieldName}" i]`);
          if (field) {
            field.value = data[key];
            break;
          }
        }
      }
    }
  });
}
