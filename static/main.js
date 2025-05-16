document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('upload-form');
  const suggestForm = document.getElementById('suggest-form');
  const results = document.getElementById('results');

  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(uploadForm);
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    showSuggestions(data.suggestions);
  });

  suggestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(suggestForm);
    const response = await fetch('/suggest', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    showSuggestions(data.suggestions);
  });

  function showSuggestions(suggestions) {
    results.innerHTML = '<h3>Suggestions:</h3>' +
      '<ul>' + suggestions.map(s => `<li>${s}</li>`).join('') + '</ul>';
  }
});
