document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('upload-form');
  const suggestForm = document.getElementById('suggest-form');
  const composeForm = document.getElementById('compose-form');
  const results = document.getElementById('results');
  const compositeResult = document.getElementById('composite-result');

  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(uploadForm);
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    if (response.ok) {
      const data = await response.json();
      showSuggestions(data.suggestions, data.image_url);
    } else {
      let message = 'Request failed';
      try {
        const err = await response.json();
        if (err.error) message = err.error;
      } catch (e) {
        // ignore
      }
      showError(results, message);
    }
  });

  suggestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(suggestForm);
    const response = await fetch('/suggest', {
      method: 'POST',
      body: formData
    });
    if (response.ok) {
      const data = await response.json();
      showSuggestions(data.suggestions, data.image_url);
    } else {
      let message = 'Request failed';
      try {
        const err = await response.json();
        if (err.error) message = err.error;
      } catch (e) {
        // ignore
      }
      showError(results, message);
    }
  });

  composeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(composeForm);
    const response = await fetch('/compose', {
      method: 'POST',
      body: formData
    });
    if (response.ok) {
      const data = await response.json();
      showComposite(data.suggestions, data.composite_url);
    } else {
      let message = 'Request failed';
      try {
        const err = await response.json();
        if (err.error) message = err.error;
      } catch (e) {
        // ignore
      }
      showError(compositeResult, message);
    }
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

  function showComposite(suggestions, compositeUrl) {
    compositeResult.textContent = '';

    if (compositeUrl) {
      const img = document.createElement('img');
      img.src = compositeUrl;
      img.alt = 'Composite outfit';
      compositeResult.appendChild(img);
    }

    if (suggestions && suggestions.length) {
      const heading = document.createElement('h3');
      heading.textContent = 'Suggestions:';
      compositeResult.appendChild(heading);

      const list = document.createElement('ul');
      suggestions.forEach(s => {
        const item = document.createElement('li');
        item.textContent = s;
        list.appendChild(item);
      });
      compositeResult.appendChild(list);
    }
  }

  function showError(container, message) {
    container.textContent = `Error: ${message}`;
  }
});
