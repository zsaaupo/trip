const BUS_ID = document.querySelector('[data-bus-id]').dataset.busId;
let busData = null;
let selectedSeats = new Set();

function renderHeader(bus) {
  const rating = bus.avg_rating != null ? `<span class="rating-pill">★ ${bus.avg_rating}</span>` : '<span class="muted">No ratings yet</span>';
  document.getElementById('bus-header').innerHTML = `
    <div class="page-title-row">
      <div>
        <h1>${escapeHtml(bus.name)}</h1>
        <p class="muted">${escapeHtml(bus.route_origin)} → ${escapeHtml(bus.route_destination)} &nbsp;|&nbsp; ${formatDateTime(bus.trip_date)} &nbsp; ${rating}</p>
      </div>
    </div>`;
  document.getElementById('summary-price').textContent = formatMoney(bus.price_per_seat);
}

function renderSeatMap(bus) {
  const map = document.getElementById('seat-map');
  const occupied = new Set(bus.occupied_seats);
  let html = '';
  for (let i = 1; i <= bus.total_seats; i++) {
    const isOccupied = occupied.has(i);
    const isSelected = selectedSeats.has(i);
    const cls = isOccupied ? 'seat seat--occupied' : (isSelected ? 'seat seat--selected' : 'seat');
    html += `<div class="${cls}" data-seat="${i}" ${isOccupied ? '' : 'onclick="toggleSeat(' + i + ')"'}>${i}</div>`;
    if (i % 4 === 2) html += `<div class="seat-map__aisle-gap"></div>`;
  }
  map.innerHTML = html;
}

function toggleSeat(num) {
  if (selectedSeats.has(num)) selectedSeats.delete(num);
  else selectedSeats.add(num);
  renderSeatMap(busData);
  updateSummary();
}

function updateSummary() {
  const seats = Array.from(selectedSeats).sort((a, b) => a - b);
  document.getElementById('summary-seats').textContent = seats.length ? seats.join(', ') : 'None';
  const total = seats.length * Number(busData.price_per_seat);
  document.getElementById('summary-total').textContent = formatMoney(total);
}

async function loadBus() {
  try {
    busData = await apiRequest(`/transport/buses/${BUS_ID}/`);
    renderHeader(busData);
    renderSeatMap(busData);
    updateSummary();
  } catch (err) {
    document.getElementById('bus-header').innerHTML = `<p class="muted">Couldn't load this bus: ${escapeHtml(err.message)}</p>`;
  }
}

async function loadReviews() {
  const container = document.getElementById('review-list');
  try {
    const reviews = await apiRequest(`/reviews/?service_type=bus&service_id=${BUS_ID}`);
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

document.getElementById('confirm-btn').addEventListener('click', async () => {
  const btn = document.getElementById('confirm-btn');
  if (!selectedSeats.size) { showToast('Select at least one seat.', 'error'); return; }
  if (!document.getElementById('terms').checked) { showToast('Please accept the Terms & Conditions.', 'error'); return; }

  const payload = {
    bus: Number(BUS_ID),
    seat_numbers: Array.from(selectedSeats).join(','),
    payment_method: document.querySelector('input[name=payment]:checked').value,
    coupon_code: document.getElementById('coupon').value.trim(),
    terms_accepted: true,
  };

  btn.disabled = true; btn.textContent = 'Booking...';
  try {
    const booking = await apiRequest('/transport/bus-bookings/', { method: 'POST', body: payload });
    showToast(`Booked! Invoice ${booking.invoice_id}`, 'success');
    setTimeout(() => window.location.href = '/bookings/', 900);
  } catch (err) {
    showToast(err.message, 'error');
    loadBus();
    selectedSeats.clear();
  } finally {
    btn.disabled = false; btn.textContent = 'Confirm booking';
  }
});

loadBus();
loadReviews();
