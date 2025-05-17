document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('upload-form');
  const suggestForm = document.getElementById('suggest-form');
  const composeForm = document.getElementById('compose-form');
  const results = document.getElementById('results');
  const compositeResult = document.getElementById('composite-result');
  const uploadPreview = document.getElementById('upload-preview');
  const composePreview = document.getElementById('compose-preview');
  const uploadLoading = document.getElementById('upload-loading');
  const suggestLoading = document.getElementById('suggest-loading');
  const composeLoading = document.getElementById('compose-loading');

  const uploadInput = uploadForm.querySelector('input[name="image"]');
  const bodyInput = composeForm.querySelector('input[name="body"]');
  const clothesInput = composeForm.querySelector('input[name="clothes"]');

  uploadInput.addEventListener('change', () => {
    previewFiles(uploadInput.files, uploadPreview, true);
  });

  bodyInput.addEventListener('change', () => {
    previewFiles(bodyInput.files, composePreview, true);
  });

  clothesInput.addEventListener('change', () => {
    previewFiles(clothesInput.files, composePreview, false);
  });

  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading(uploadLoading);
    const formData = new FormData(uploadForm);
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    hideLoading(uploadLoading);
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
    showLoading(suggestLoading);
    const formData = new FormData(suggestForm);
    const response = await fetch('/suggest', {
      method: 'POST',
      body: formData
    });
    hideLoading(suggestLoading);
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
    showLoading(composeLoading);
    const formData = new FormData(composeForm);
    const response = await fetch('/compose', {
      method: 'POST',
      body: formData
    });
    hideLoading(composeLoading);
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

  function previewFiles(files, container, replace) {
    if (replace) {
      container.textContent = '';
    }
    Array.from(files).forEach(file => {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      container.appendChild(img);
    });
  }

  function showLoading(el) {
    el.classList.add('active');
  }

  function hideLoading(el) {
    el.classList.remove('active');
  }

  function showError(container, message) {
    container.textContent = '';
    const p = document.createElement('p');
    p.className = 'error';
    p.textContent = `Error: ${message}`;
    container.appendChild(p);
  }
});
