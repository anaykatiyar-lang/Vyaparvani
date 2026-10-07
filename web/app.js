const $ = (id) => document.getElementById(id);
const form = { product: $('product'), amount: $('amount'), paid: $('paid'), unit: $('unit'), free: $('free') };
let previewUrl = null;

function currentFields() {
  return { product: form.product.value, net_amount_paid: form.amount.value,
    paid_quantity: form.paid.value, quantity_unit: form.unit.value,
    free_cartons: form.free.value };
}

function setFields(fields) {
  if (fields.product != null) form.product.value = fields.product;
  if (fields.net_amount_paid != null) form.amount.value = fields.net_amount_paid;
  if (fields.paid_quantity != null) form.paid.value = fields.paid_quantity;
  if (fields.quantity_unit) form.unit.value = fields.quantity_unit;
  if (fields.free_cartons != null) form.free.value = fields.free_cartons;
}

function money(value) { return Number(value).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2}); }

function render(result) {
  $('emptyResult').hidden = true;
  const target = $('result'); target.hidden = false;
  const clear = result.status === 'CLEAR';
  const confirm = result.status === 'CONFIRM';
  const tone = clear ? 'clear' : confirm ? 'confirm' : 'error';
  $('reviewNotice').className = `notice ${tone}`;
  $('reviewNotice').textContent = clear ? 'Everything needed is clear. Here is the carton calculation.' :
    confirm ? 'Please confirm the highlighted details before using a carton price.' : 'A required value is missing or invalid. Fill it in to continue.';
  const messages = result.issues.map(issue => `<div>• ${escapeHtml(issue.message)}</div>`).join('');
  const breakdown = result.breakdown.map(line => `<div>${escapeHtml(line)}</div>`).join('');
  target.innerHTML = `<div class="price-result ${confirm?'confirm':''}"><div><div class="status">${escapeHtml(result.status)}</div><div class="price">${clear?'₹'+money(result.landing_price_per_carton):'—'} <span class="price-unit">${clear?'/ carton':''}</span></div><div class="result-product">${escapeHtml(result.product||'Product not confirmed')}</div></div></div>${messages?`<div class="result-message">${messages}</div>`:''}${breakdown?`<div class="breakdown"><div class="breakdown-title">Calculation breakdown</div>${breakdown}</div>`:''}`;
}

function escapeHtml(value) { return String(value).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

$('extractButton').addEventListener('click', async () => {
  const text = $('sourceText').value.trim();
  if (!text) { $('reviewNotice').className='notice confirm'; $('reviewNotice').textContent='Paste printed invoice text or enter the details in the review fields.'; form.product.focus(); return; }
  const response = await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
  const payload = await response.json();
  setFields(payload.fields || {});
  $('reviewNotice').className='notice confirm'; $('reviewNotice').textContent='Details read from the text. Review the quantity unit and free-carton count before calculating.';
  $('result').hidden=true; $('emptyResult').hidden=false;
});

$('calculateButton').addEventListener('click', async () => {
  const response = await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentFields())});
  render(await response.json());
});

$('photo').addEventListener('change', event => {
  const file = event.target.files[0]; if (!file) return;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file); $('previewImage').src=previewUrl;
  $('photoPreview').hidden=false; $('dropzone').hidden=true;
});
$('removePhoto').addEventListener('click',()=>{
  $('photo').value=''; $('photoPreview').hidden=true; $('dropzone').hidden=false;
  if (previewUrl) URL.revokeObjectURL(previewUrl); previewUrl=null;
});
fetch('/api/config').then(r=>r.json()).then(c=>{$('providerStatus').textContent=`Extraction: ${c.provider}`;});
