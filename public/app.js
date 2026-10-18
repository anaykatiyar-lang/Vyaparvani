const $ = (id) => document.getElementById(id);
const form = { product: $('product'), amount: $('amount'), paid: $('paid'), unit: $('unit'), free: $('free') };
const photoInput = $('photo');
const cameraDialog = $('cameraDialog');
let previewUrl = null;
let cameraStream = null;
let activePhoto = null;
let imageOcrEnabled = false;
function imageReaderLabel() { return 'Google Cloud Vision'; }

function currentFields() {
  return { product: form.product.value, net_amount_paid: form.amount.value,
    paid_quantity: form.paid.value, quantity_unit: form.unit.value,
    free_cartons: form.free.value };
}

function setFields(fields, replace = false) {
  if (replace) {
    Object.values(form).forEach(input => { input.value = input === form.unit ? 'unknown' : ''; });
    $('evidenceNote').hidden = true;
  }
  if (fields.product != null) form.product.value = fields.product;
  if (fields.net_amount_paid != null) form.amount.value = fields.net_amount_paid;
  if (fields.paid_quantity != null) form.paid.value = fields.paid_quantity;
  if (fields.quantity_unit) form.unit.value = fields.quantity_unit;
  if (fields.free_cartons != null) form.free.value = fields.free_cartons;
}

function money(value) {
  return Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function render(result) {
  $('emptyResult').hidden = true;
  const target = $('result');
  target.hidden = false;
  const clear = result.status === 'CLEAR';
  const confirm = result.status === 'CONFIRM';
  const tone = clear ? 'clear' : confirm ? 'confirm' : 'error';
  $('reviewNotice').className = `notice ${tone}`;
  $('reviewNotice').textContent = clear
    ? 'The required details are confirmed. Here is the carton calculation.'
    : confirm
      ? 'Please resolve the details below. No price is shown until they are confirmed.'
      : 'A required value is missing or invalid. Fill it in to continue.';
  const messages = result.issues.map(issue => `<div>${escapeHtml(issue.message)}</div>`).join('');
  const breakdown = result.breakdown.map(line => `<div>${escapeHtml(line)}</div>`).join('');
  target.innerHTML = `<div class="price-result ${confirm ? 'confirm' : ''}"><div><div class="status">${escapeHtml(result.status)}</div><div class="price">${clear ? `₹${money(result.landing_price_per_carton)}` : '—'} <span class="price-unit">${clear ? '/ carton' : ''}</span></div><div class="result-product">${escapeHtml(result.product || 'Product not confirmed')}</div></div></div>${messages ? `<div class="result-message">${messages}</div>` : ''}${breakdown ? `<div class="breakdown"><div class="breakdown-title">Calculation breakdown</div>${breakdown}</div>` : ''}`;
  $('resultCard').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearResult() {
  $('result').hidden = true;
  $('emptyResult').hidden = false;
}

function showNotice(message, tone = 'confirm') {
  $('reviewNotice').className = `notice ${tone}`;
  $('reviewNotice').textContent = message;
}

async function postJson(path, value) {
  let response;
  try {
    response = await fetch(path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value)
    });
  } catch (_) {
    throw new Error('Could not reach the app server. Check your connection and try again.');
  }
  let payload;
  try {
    payload = await response.json();
  } catch (_) {
    throw new Error(response.status === 504
      ? 'The image reader took too long to respond. Try again or enter the details manually.'
      : 'The app server returned an unreadable response. Please try again.');
  }
  if (!response.ok) throw new Error(payload.error || 'The request could not be completed.');
  return payload;
}

function stopCamera() {
  if (cameraStream) cameraStream.getTracks().forEach(track => track.stop());
  cameraStream = null;
  $('cameraVideo').srcObject = null;
}

function showPhoto(file) {
  if (!file || !file.type.startsWith('image/')) {
    showNotice('Choose an image file such as JPG, PNG or WebP.', 'error');
    return;
  }
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  activePhoto = file;
  setFields({}, true);
  $('sourceText').value = '';
  previewUrl = URL.createObjectURL(file);
  $('previewImage').src = previewUrl;
  $('photoName').textContent = file.name || 'Camera capture';
  $('photoSize').textContent = `${(file.size / 1024).toFixed(0)} KB · preview only`;
  $('photoPreview').hidden = false;
  clearResult();
  showNotice(imageOcrEnabled
    ? `Photo ready. Choose “Read photo with ${imageReaderLabel()}” to extract the invoice fields.`
    : 'Photo added. Google Cloud Vision photo reading is not configured yet; enter the printed values below.');
}

async function compressedImageDataUrl(file) {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 1400 / Math.max(bitmap.width, bitmap.height));
  const canvas = $('captureCanvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.72));
  if (!blob) throw new Error('Could not prepare the photo. Choose it again and retry.');
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Could not read the photo. Choose it again and retry.'));
    reader.readAsDataURL(blob);
  });
}

function showEvidence(evidence) {
  const target = $('evidenceNote');
  const entries = Object.entries(evidence || {}).filter(([, value]) => typeof value === 'string' && value.trim());
  if (!entries.length) { target.hidden = true; return; }
  target.innerHTML = `<strong>From the invoice</strong>${entries.map(([key, value]) => `<div><span>${escapeHtml(key.replaceAll('_', ' '))}</span>${escapeHtml(value)}</div>`).join('')}`;
  target.hidden = false;
}

$('extractButton').addEventListener('click', async () => {
  const text = $('sourceText').value.trim();
  if (!text) {
    showNotice('Paste the printed invoice text, or enter each detail in the fields to the right.');
    form.product.focus();
    return;
  }
  $('extractButton').disabled = true;
  $('extractButton').textContent = 'Reading details…';
  try {
    const payload = await postJson('/api/extract', { text });
    setFields(payload.fields || {}, true);
    showEvidence(payload.fields?.evidence);
    clearResult();
    showNotice('Details read from the text. Review the printed unit and confirm free cartons before calculating.');
    form.product.focus();
  } catch (error) {
    showNotice(error.message || 'Could not read the text. Please enter the details manually.', 'error');
  } finally {
    $('extractButton').disabled = false;
    $('extractButton').innerHTML = 'Read details <span aria-hidden="true">→</span>';
  }
});

$('calculateButton').addEventListener('click', async () => {
  const button = $('calculateButton');
  button.disabled = true;
  button.textContent = 'Checking details…';
  try {
    render(await postJson('/api/calculate', currentFields()));
  } catch (error) {
    showNotice(error.message || 'Could not calculate. Please try again.', 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = 'Calculate landing price <span aria-hidden="true">→</span>';
  }
});

photoInput.addEventListener('change', event => showPhoto(event.target.files[0]));
$('readPhotoButton').addEventListener('click', async () => {
  const captureFile = activePhoto;
  if (!captureFile) return;
  const button = $('readPhotoButton');
  button.disabled = true;
  button.textContent = 'Reading invoice…';
  try {
    const image_data_url = await compressedImageDataUrl(captureFile);
    const payload = await postJson('/api/extract-image', { image_data_url });
    setFields(payload.fields || {}, true);
    showEvidence(payload.fields?.evidence);
    if (payload.fields?.ocr_text) $('sourceText').value = payload.fields.ocr_text;
    clearResult();
    showNotice('Invoice text read with Google Cloud Vision. Check the photo and fill any details it could not identify; handwritten marks may also appear in the text.', 'confirm');
    if (!form.product.value || !form.amount.value || !form.paid.value) form.product.focus();
  } catch (error) {
    showNotice(error.message || 'Could not read this photo. Enter the details manually.', 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = `Read photo with ${imageReaderLabel()} <span aria-hidden="true">→</span>`;
  }
});
$('removePhoto').addEventListener('click', () => {
  photoInput.value = '';
  activePhoto = null;
  $('photoPreview').hidden = true;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  clearResult();
});

$('openCamera').addEventListener('click', async () => {
  $('cameraError').hidden = true;
  $('capturePhoto').disabled = false;
  cameraDialog.showModal();
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('Camera access is not available in this browser. Use Upload a photo instead.');
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
    $('cameraVideo').srcObject = cameraStream;
  } catch (error) {
    $('cameraError').textContent = error.name === 'NotAllowedError'
      ? 'Camera permission was declined. Allow access in your browser settings or upload a photo instead.'
      : error.message || 'Could not open the camera. Upload a photo instead.';
    $('cameraError').hidden = false;
    $('capturePhoto').disabled = true;
  }
});

$('capturePhoto').addEventListener('click', () => {
  const video = $('cameraVideo');
  if (!video.videoWidth || !video.videoHeight) return;
  const canvas = $('captureCanvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  canvas.toBlob(blob => {
    if (!blob) return;
    const file = new File([blob], `invoice-${new Date().toISOString().slice(0, 10)}.jpg`, { type: 'image/jpeg' });
    try { photoInput.files = new DataTransfer().files; } catch (_) { /* Preview still works without assigning the input. */ }
    showPhoto(file);
    stopCamera();
    cameraDialog.close();
  }, 'image/jpeg', 0.9);
});

$('closeCamera').addEventListener('click', () => cameraDialog.close());
cameraDialog.addEventListener('close', stopCamera);
Object.values(form).forEach(input => input.addEventListener('input', () => {
  clearResult();
  showNotice('Details changed. Check them and calculate again.');
}));
form.unit.addEventListener('change', () => {
  clearResult();
  showNotice('Details changed. Check them and calculate again.');
});

fetch('/api/config').then(response => response.json()).then(config => {
  imageOcrEnabled = Boolean(config.image_ocr);
  $('readPhotoButton').hidden = !imageOcrEnabled;
  $('readPhotoButton').innerHTML = `Read photo with ${imageReaderLabel()} <span aria-hidden="true">→</span>`;
  $('providerStatus').textContent = imageOcrEnabled ? `Photo reading: ${imageReaderLabel()}` : 'Manual review';
  $('privacyNote').innerHTML = imageOcrEnabled
    ? '<span class="lock-icon" aria-hidden="true">◈</span> Nothing is sent until you choose Read photo. The resized image is sent to Google Cloud Vision for text recognition.'
    : '<span class="lock-icon" aria-hidden="true">◈</span> Add GOOGLE_VISION_API_KEY to the server environment to enable photo reading.';
}).catch(() => {
  $('providerStatus').textContent = 'Manual review';
  $('privacyNote').innerHTML = '<span class="lock-icon" aria-hidden="true">◈</span> Could not check photo-reading setup. You can still enter details manually.';
});
