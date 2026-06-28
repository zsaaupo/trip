const PACKAGE_ID = document.querySelector('[data-package-id]').dataset.packageId;
let packageData = null;

function renderHeader(pkg) {
  const rating = pkg.avg_rating != null ? `<span class="rating-pill">★ ${pkg.avg_rating}</span>` : '<span class="muted">No ratings yet</span>';
  document.getElementById('package-header').innerHTML = `
    <div class="page-title-row">
      <div>
        <h1>${escapeHtml(pkg.name)}</h1>
        <p class="muted">📍 ${escapeHtml(pkg.location)} &nbsp;|&nbsp; ${escapeHtml(pkg.duration)} &nbsp;|&nbsp; Starts ${formatDate(pkg.date)} &nbsp; ${rating}</p>
      </div>
    </div>
    <img src="${pkg.photo}" alt="${escapeHtml(pkg.name)}" style="border-radius:var(--radius-md);max-height:320px;width:100%;object-fit:cover;margin-bottom:18px;">
    ${pkg.hotel_detail ? `<p><strong>Hotel included:</strong> ${escapeHtml(pkg.hotel_detail.name)}, ${escapeHtml(pkg.hotel_detail.location)}</p>` : ''}
    ${pkg.transport_label ? `<p><strong>Transport included:</strong> ${escapeHtml(pkg.transport_label)}</p>` : ''}`;

  document.getElementById('inclusions-exclusions').innerHTML = `
    <p><strong>Inclusions</strong></p>
    <p class="muted">${escapeHtml(pkg.inclusions || 'Not specified')}</p>
    <p><strong>Exclusions</strong></p>
    <p class="muted">${escapeHtml(pkg.exclusions || 'Not specified')}</p>`;

  updateSummary();
}

function updateSummary() {
  const people = Math.max(1, Number(document.getElementById('b-people').value || 1));
  document.getElementById('summary-total').textContent = formatMoney(packageData.price * people);
}

async function loadPackage() {
  try {
    packageData = await apiRequest(`/packages/${PACKAGE_ID}/`);
    renderHeader(packageData);
  } catch (err) {
    document.getElementById('package-header').innerHTML = `<p class="muted">Couldn't load this package: ${escapeHtml(err.message)}</p>`;
  }
}

async function loadReviews() {
  const container = document.getElementById('review-list');
  try {
    const reviews = await apiRequest(`/reviews/?service_type=package&service_id=${PACKAGE_ID}`);
    if (!reviews.length) { container.innerHTML = `<p class="muted">No reviews yet.</p>`; return; }
    container.innerHTML = reviews.map(r => `
      <div class="review-item">
        <span class="review-item__rating">★ ${r.rating}</span>
        <strong>${escapeHtml(r.customer_name || 'Customer')}</strong>
        <p>${escapeHtml(r.comment || '')}</p>
      </div>`).join('');
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load reviews.</p>`;
  }
}

document.getElementById('b-people').addEventListener('input', updateSummary);

document.getElementById('confirm-btn').addEventListener('click', async () => {
  const btn = document.getElementById('confirm-btn');
  if (!document.getElementById('terms').checked) { showToast('Please accept the Terms & Conditions.', 'error'); return; }

  const payload = {
    package: Number(PACKAGE_ID),
    num_people: Number(document.getElementById('b-people').value || 1),
    payment_method: document.querySelector('input[name=payment]:checked').value,
    coupon_code: document.getElementById('coupon').value.trim(),
    service_date: document.getElementById('package-booking-date').value,
    terms_accepted: true,
  };

  btn.disabled = true; btn.textContent = 'Booking...';
  try {
    const booking = await apiRequest('/packages/bookings/', { method: 'POST', body: payload });
    showToast(`Booked! Invoice ${booking.invoice_id}`, 'success');
    setTimeout(() => window.location.href = '/bookings/', 900);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Confirm booking';
  }
});

loadPackage();
loadReviews();
