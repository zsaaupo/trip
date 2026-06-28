const CANCEL_URLS = {
  hotel: (id) => `/hotels/bookings/${id}/cancel/`,
  bus: (id) => `/transport/bus-bookings/${id}/cancel/`,
  car: (id) => `/transport/car-bookings/${id}/cancel/`,
  package: (id) => `/packages/bookings/${id}/cancel/`,
};

let selectedRating = 0;

function bookingRowHtml(b) {
  const canCancel = b.status === 'pending' || b.status === 'confirmed';
  const canReview = b.status === 'confirmed' || b.status === 'completed';
  return `
    <tr>
      <td>${escapeHtml(b.invoice_id)}</td>
      <td style="text-transform:capitalize;">${escapeHtml(b.booking_type)}</td>
      <td>${escapeHtml(b.service_name)}</td>
      <td>${formatDate(b.service_date)}</td>
      <td><span class="${statusBadgeClass(b.status)}">${escapeHtml(b.status_display)}</span>${b.refund_percentage != null ? `<div class="hint">${b.refund_percentage}% refund</div>` : ''}</td>
      <td>${formatMoney(b.total_amount)}</td>
      <td>
        ${canCancel ? `<button class="btn btn--danger btn--small" onclick="cancelBooking('${b.booking_type}', ${b.id})">Cancel</button>` : ''}
        ${canReview ? `<button class="btn btn--ghost btn--small" onclick="openReviewModal('${b.booking_type}', ${b.id})">Review</button>` : ''}
      </td>
    </tr>`;
}

async function loadBookings() {
  const container = document.getElementById('bookings-list');
  container.innerHTML = '<div class="spinner"></div>';
  const status = document.getElementById('f-status').value;
  const params = status ? `?status=${status}` : '';

  try {
    const bookings = await apiRequest(`/dashboard/my-bookings/${params}`);
    if (!bookings.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🧳</div><p>No bookings found.</p></div>`;
      return;
    }
    container.innerHTML = `
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Invoice</th><th>Type</th><th>Service</th><th>Service date</th><th>Status</th><th>Total</th><th>Actions</th></tr></thead>
          <tbody>${bookings.map(bookingRowHtml).join('')}</tbody>
        </table>
      </div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load bookings: ${escapeHtml(err.message)}</p>`;
  }
}

async function cancelBooking(type, id) {
  if (!confirm('Cancel this booking? The refund amount depends on how close it is to the service date.')) return;
  try {
    const result = await apiRequest(CANCEL_URLS[type](id), { method: 'POST', body: {} });
    showToast(`Cancelled. Refund: ${result.refund_percentage}%`, 'success');
    loadBookings();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openReviewModal(type, id) {
  document.getElementById('review-booking-type').value = type;
  document.getElementById('review-booking-id').value = id;
  selectedRating = 0;
  renderStars();
  document.getElementById('review-comment').value = '';
  document.getElementById('review-modal').classList.add('modal-overlay--open');
}
function closeReviewModal() {
  document.getElementById('review-modal').classList.remove('modal-overlay--open');
}

function renderStars() {
  document.querySelectorAll('#star-input span').forEach(span => {
    span.classList.toggle('active', Number(span.dataset.value) <= selectedRating);
  });
}

document.getElementById('star-input').addEventListener('click', (e) => {
  if (e.target.dataset.value) {
    selectedRating = Number(e.target.dataset.value);
    renderStars();
  }
});

document.getElementById('close-review-modal-btn').addEventListener('click', closeReviewModal);
document.getElementById('review-modal').addEventListener('click', (e) => {
  if (e.target.id === 'review-modal') closeReviewModal();
});

document.getElementById('review-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!selectedRating) { showToast('Please select a star rating.', 'error'); return; }
  const btn = document.getElementById('submit-review-btn');
  const payload = {
    booking_type: document.getElementById('review-booking-type').value,
    booking_id: Number(document.getElementById('review-booking-id').value),
    rating: selectedRating,
    comment: document.getElementById('review-comment').value.trim(),
  };
  btn.disabled = true; btn.textContent = 'Submitting...';
  try {
    await apiRequest('/reviews/create/', { method: 'POST', body: payload });
    showToast('Thanks for your review! It will appear once approved.', 'success');
    closeReviewModal();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Submit review';
  }
});

document.getElementById('refresh-btn').addEventListener('click', loadBookings);
loadBookings();
