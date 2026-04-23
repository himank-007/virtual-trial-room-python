/* ===============================
   VirtualFit - Frontend Logic
   =============================== */

// ---- State ----
let userImageBase64 = null;
let selectedClothing = null;
let selectedCategory = 'tops';
let catalog = {};
let cameraStream = null;

// ---- DOM References ----
const photoInput = document.getElementById('photoInput');
const dropZone = document.getElementById('dropZone');
const dropInner = document.getElementById('dropInner');
const userPreview = document.getElementById('userPreview');
const cameraFeed = document.getElementById('cameraFeed');
const captureBtn = document.getElementById('captureBtn');
const camBtn = document.getElementById('camBtn');

const clothingGrid = document.getElementById('clothingGrid');
const applyBtn = document.getElementById('applyBtn');
const resultPlaceholder = document.getElementById('resultPlaceholder');
const resultImage = document.getElementById('resultImage');
const loader = document.getElementById('loader');
const resultActions = document.getElementById('resultActions');
const selectedInfo = document.getElementById('selectedInfo');
const selectedName = document.getElementById('selectedName');

const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const debugBtn = document.getElementById('debugBtn');
const debugImage = document.getElementById('debugImage');

const uploadClothingBtn = document.getElementById('uploadClothingBtn');
const uploadStatus = document.getElementById('uploadStatus');

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  loadCatalog();
  setupTabs();
  setupDropZone();
  setupPhotoInput();
  setupCamera();
  setupApply();
  setupDownload();
  setupReset();
  setupDebug();
  setupUpload();
});

// ---- Catalog ----
async function loadCatalog() {
  try {
    const res = await fetch('/api/catalog');
    catalog = await res.json();
    renderCatalog(selectedCategory);
  } catch (e) {
    console.error('Failed to load catalog:', e);
  }
}

function renderCatalog(category) {
  const items = catalog[category] || [];
  clothingGrid.innerHTML = '';

  if (items.length === 0) {
    clothingGrid.innerHTML = `<div class="empty-catalog">
      <p>📂 No items in this category yet.</p>
      <p>Upload some clothing below!</p>
    </div>`;
    return;
  }

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'clothing-item';
    div.dataset.path = item.path;
    div.dataset.name = item.name;
    div.dataset.category = item.category;

    div.innerHTML = `
      <img src="${item.path}" alt="${item.name}" loading="lazy" />
      <div class="item-name">${item.name}</div>
    `;

    div.addEventListener('click', () => selectClothing(div, item));
    clothingGrid.appendChild(div);
  });
}

function selectClothing(el, item) {
  document.querySelectorAll('.clothing-item').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  selectedClothing = item;
  selectedInfo.classList.remove('hidden');
  selectedName.textContent = item.name;
  updateApplyBtn();
}

// ---- Tabs ----
function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      selectedCategory = tab.dataset.cat;
      selectedClothing = null;
      selectedInfo.classList.add('hidden');
      updateApplyBtn();
      renderCatalog(selectedCategory);
    });
  });
}

// ---- Drop Zone / Photo Input ----
function setupDropZone() {
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) loadUserPhoto(file);
  });
  dropZone.addEventListener('click', e => {
    if (e.target === dropZone || e.target === dropInner) {
      photoInput.click();
    }
  });
}

function setupPhotoInput() {
  photoInput.addEventListener('change', () => {
    if (photoInput.files[0]) loadUserPhoto(photoInput.files[0]);
  });
}

function loadUserPhoto(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    userImageBase64 = e.target.result;
    userPreview.src = userImageBase64;
    userPreview.classList.remove('hidden');
    dropInner.classList.add('hidden');
    stopCamera();
    updateApplyBtn();
  };
  reader.readAsDataURL(file);
}

// ---- Camera ----
function setupCamera() {
  camBtn.addEventListener('click', async () => {
    if (cameraStream) {
      stopCamera();
      return;
    }
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
      cameraFeed.srcObject = cameraStream;
      cameraFeed.classList.remove('hidden');
      captureBtn.classList.remove('hidden');
      dropInner.classList.add('hidden');
      userPreview.classList.add('hidden');
      camBtn.textContent = '✕ Stop Camera';
    } catch (e) {
      alert('Camera not available: ' + e.message);
    }
  });

  captureBtn.addEventListener('click', () => {
    const canvas = document.createElement('canvas');
    canvas.width = cameraFeed.videoWidth;
    canvas.height = cameraFeed.videoHeight;
    canvas.getContext('2d').drawImage(cameraFeed, 0, 0);
    userImageBase64 = canvas.toDataURL('image/jpeg', 0.92);
    userPreview.src = userImageBase64;
    userPreview.classList.remove('hidden');
    stopCamera();
    updateApplyBtn();
  });
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  cameraFeed.classList.add('hidden');
  captureBtn.classList.add('hidden');
  camBtn.textContent = 'Use Camera';
  if (userImageBase64) {
    dropInner.classList.add('hidden');
  } else {
    dropInner.classList.remove('hidden');
  }
}

// ---- Apply ----
function updateApplyBtn() {
  applyBtn.disabled = !(userImageBase64 && selectedClothing);
}

function setupApply() {
  applyBtn.addEventListener('click', async () => {
    if (!userImageBase64 || !selectedClothing) return;

    setLoading(true);
    debugImage.classList.add('hidden');

    try {
      const res = await fetch('/api/try-on', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_image: userImageBase64,
          clothing_path: selectedClothing.path,
          category: selectedClothing.category
        })
      });

      const data = await res.json();
      if (data.success && data.result_image) {
        showResult(data.result_image);
      } else {
        showError(data.error || 'Unknown error occurred.');
      }
    } catch (e) {
      showError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  });
}

function setLoading(on) {
  if (on) {
    loader.classList.remove('hidden');
    resultPlaceholder.classList.add('hidden');
    resultImage.classList.add('hidden');
    resultActions.classList.add('hidden');
    applyBtn.disabled = true;
    applyBtn.textContent = 'Fitting…';
  } else {
    loader.classList.add('hidden');
    applyBtn.disabled = false;
    applyBtn.textContent = '✨ Try It On';
    updateApplyBtn();
  }
}

function showResult(imgSrc) {
  resultImage.src = imgSrc;
  resultImage.classList.remove('hidden');
  resultPlaceholder.classList.add('hidden');
  resultActions.classList.remove('hidden');
}

function showError(msg) {
  resultPlaceholder.classList.remove('hidden');
  resultPlaceholder.innerHTML = `<div class="result-icon">⚠️</div><p style="color:#ff6b35">${msg}</p>`;
  resultImage.classList.add('hidden');
  resultActions.classList.add('hidden');
}

// ---- Download ----
function setupDownload() {
  downloadBtn.addEventListener('click', () => {
    if (!resultImage.src) return;
    const a = document.createElement('a');
    a.href = resultImage.src;
    a.download = 'virtualfit-tryon.png';
    a.click();
  });
}

// ---- Reset ----
function setupReset() {
  resetBtn.addEventListener('click', () => {
    userImageBase64 = null;
    selectedClothing = null;
    userPreview.src = '';
    userPreview.classList.add('hidden');
    dropInner.classList.remove('hidden');
    resultImage.classList.add('hidden');
    resultActions.classList.add('hidden');
    debugImage.classList.add('hidden');
    resultPlaceholder.classList.remove('hidden');
    resultPlaceholder.innerHTML = `<div class="result-icon">✨</div>
      <p>Select a photo &amp; clothing item<br />to see the magic</p>`;
    document.querySelectorAll('.clothing-item').forEach(c => c.classList.remove('selected'));
    selectedInfo.classList.add('hidden');
    updateApplyBtn();
    stopCamera();
  });
}

// ---- Debug Keypoints ----
function setupDebug() {
  debugBtn.addEventListener('click', async () => {
    if (!userImageBase64) {
      alert('Please upload a photo first.');
      return;
    }
    debugBtn.textContent = '🔍 Loading…';
    try {
      const res = await fetch('/api/keypoints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_image: userImageBase64 })
      });
      const data = await res.json();
      if (data.detected && data.debug_image) {
        debugImage.src = data.debug_image;
        debugImage.classList.remove('hidden');
        debugBtn.textContent = '🔍 Hide keypoints';
      } else {
        alert('No person detected in the image.');
        debugBtn.textContent = '🔍 Show pose keypoints';
      }
    } catch (e) {
      alert('Error: ' + e.message);
      debugBtn.textContent = '🔍 Show pose keypoints';
    }
  });

  debugImage.addEventListener('click', () => {
    debugImage.classList.add('hidden');
    debugBtn.textContent = '🔍 Show pose keypoints';
  });
}

// ---- Upload Clothing ----
function setupUpload() {
  uploadClothingBtn.addEventListener('click', async () => {
    const file = document.getElementById('clothingFileInput').files[0];
    const category = document.getElementById('uploadCategory').value;

    if (!file) {
      setUploadStatus('Please select a file.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    uploadClothingBtn.disabled = true;
    uploadClothingBtn.textContent = 'Uploading…';

    try {
      const res = await fetch('/api/upload-clothing', { method: 'POST', body: formData });
      const data = await res.json();

      if (data.success) {
        setUploadStatus(`✓ "${data.name}" uploaded successfully!`, 'success');
        await loadCatalog();
        // Switch to the uploaded category
        document.querySelectorAll('.tab').forEach(t => {
          t.classList.toggle('active', t.dataset.cat === category);
        });
        selectedCategory = category;
        renderCatalog(selectedCategory);
      } else {
        setUploadStatus(data.error || 'Upload failed.', 'error');
      }
    } catch (e) {
      setUploadStatus('Network error: ' + e.message, 'error');
    } finally {
      uploadClothingBtn.disabled = false;
      uploadClothingBtn.textContent = '⬆ Upload Item';
    }
  });
}

function setUploadStatus(msg, type) {
  uploadStatus.textContent = msg;
  uploadStatus.className = 'upload-status ' + type;
}
