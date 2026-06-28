const CAR_ID = document.querySelector('[data-car-id]').dataset.carId;
let carData = null;

const TRIP_TYPE_LABELS = {
  hourly: 'Hourly',
  intercity_one_way: 'Intercity One-Way',
  intercity_round_trip: 'Intercity Round Trip',
};

function renderHeader(car) {
  const rating = car.avg_rating != null ? `<span class="rating-pill">★ ${car.avg_rating}</span>` : '<span class="muted">No ratings yet</span>';
  document.getElementById('car-header').innerHTML = `
    <div class="page-title-row">
      <div>
        <h1>${escapeHtml(car.name)}</h1>
        <p class="muted">${TRIP_TYPE_LABELS[car.trip_type] || car.trip_type} &nbsp; ${rating}</p>
      </div>
    </div>`;
  document.getElementById('summary-total').textContent = formatMoney(car.price);

  document.getElementById('car-meta').innerHTML = `
<!--    <div class="summary-row"><span>Departure</span><span>${formatDateTime(car.trip_date)}</span></div>-->
    <div class="summary-row"><span>Capacity</span><span>${car.capacity} seats</span></div>
    <div class="summary-row"><span>Climate control</span><span>${car.climate_control === 'ac' ? 'AC' : 'Non-AC'}</span></div>`;

  // const confirmBtn = document.getElementById('confirm-btn');
  // if (car.is_booked) {
  //   confirmBtn.disabled = true;
  //   document.getElementById('booked-note').style.display = 'block';
  // }
}

async function loadCar() {
  try {
    carData = await apiRequest(`/transport/cars/${CAR_ID}/`);
    renderHeader(carData);
  } catch (err) {
    document.getElementById('car-header').innerHTML = `<p class="muted">Couldn't load this car: ${escapeHtml(err.message)}</p>`;
  }
}

async function loadReviews() {
  const container = document.getElementById('review-list');
  try {
    const reviews = await apiRequest(`/reviews/?service_type=car&service_id=${CAR_ID}`);
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
  if (!document.getElementById('terms').checked) { showToast('Please accept the Terms & Conditions.', 'error'); return; }

  const payload = {
    car: Number(CAR_ID),
    payment_method: document.querySelector('input[name=payment]:checked').value,
    coupon_code: document.getElementById('coupon').value.trim(),
    trip_date: document.getElementById('car-trip-date').value,
    terms_accepted: true,
  };

  console.log(payload)
  console.log(document.getElementById('car-trip-date').value)

  btn.disabled = true; btn.textContent = 'Booking...';
  try {
    const booking = await apiRequest('/transport/car-bookings/', { method: 'POST', body: payload });
    showToast(`Booked! Invoice ${booking.invoice_id}`, 'success');
    setTimeout(() => window.location.href = '/bookings/', 900);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Confirm booking';
  }
});

loadCar();
loadReviews();
