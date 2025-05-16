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
    showSuggestions(data.suggestions, data.image_url);
  });

  suggestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(suggestForm);
    const response = await fetch('/suggest', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    showSuggestions(data.suggestions, data.image_url);
  });

  function showSuggestions(suggestions, imageUrl) {
    results.textContent = '';

    const heading = document.createElement('h3');
    heading.textContent = 'Suggestions:';
    results.appendChild(heading);

    const list = document.createElement('ul');
    suggestions.forEach(s => {
      const item = document.createElement('li');
      item.textContent = s;
      list.appendChild(item);
    });

    results.appendChild(list);

    if (imageUrl) {
      const img = document.createElement('img');
      img.src = imageUrl;
      img.alt = 'Outfit suggestion';
      results.appendChild(img);
    }
  }
});
