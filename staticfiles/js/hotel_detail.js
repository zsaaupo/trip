const HOTEL_ID = document.querySelector('[data-hotel-id]').dataset.hotelId;
let currentHotel = null;

function amenitiesHtml(amenities) {
  return amenities.map(a => `<span class="amenity-tag">${escapeHtml(a.name)}</span>`).join('');
}

function roomCardHtml(room) {
  const available = room.available_units;
  const soldOut = available <= 0;
  return `
    <div class="listing-card">
      <img class="listing-card__image" src="${room.photo}" alt="Room">
      <div class="listing-card__body">
        <h3 class="listing-card__title">${room.bed_type === 'double' ? 'Double Room' : 'Single Room'}</h3>
        <div class="listing-card__meta">
          <span>${room.climate_control === 'ac' ? '❄️ AC' : 'Non-AC'}</span>
          <span>👥 Up to ${room.max_guests} guests</span>
          <span>${available} available</span>
        </div>
        <div>${amenitiesHtml(room.amenities)}</div>
        <div class="listing-card__footer">
          <span class="listing-card__price">${formatMoney(room.price_per_night)} / night</span>
          <button class="btn btn--primary btn--small" ${soldOut ? 'disabled' : ''} onclick="openBookingModal(${room.id})">
            ${soldOut ? 'Sold out' : 'Book this room'}
          </button>
        </div>
      </div>
    </div>`;
}

function renderHeader(hotel) {
  const rating = hotel.avg_rating != null ? `<span class="rating-pill">★ ${hotel.avg_rating}</span>` : '<span class="muted">No ratings yet</span>';
  document.getElementById('hotel-header').innerHTML = `
    <div class="page-title-row">
      <div>
        <h1>${escapeHtml(hotel.name)}</h1>
        <p class="muted">📍 ${escapeHtml(hotel.location)} &nbsp; ${rating}</p>
      </div>
    </div>
    <p>${escapeHtml(hotel.description || '')}</p>`;
}

function renderRooms(hotel) {
  const list = document.getElementById('room-list');
  if (!hotel.rooms.length) {
    list.innerHTML = `<p class="muted">No rooms listed yet.</p>`;
    return;
  }
  list.innerHTML = hotel.rooms.map(roomCardHtml).join('');
}

async function loadHotel() {
  const checkin = document.getElementById('d-checkin').value;
  const checkout = document.getElementById('d-checkout').value;
  const params = new URLSearchParams();
  if (checkin && checkout) { params.set('check_in', checkin); params.set('check_out', checkout); }

  try {
    const hotel = await apiRequest(`/hotels/${HOTEL_ID}/?${params.toString()}`);
    currentHotel = hotel;
    renderHeader(hotel);
    renderRooms(hotel);
  } catch (err) {
    document.getElementById('hotel-header').innerHTML = `<p class="muted">Couldn't load this hotel: ${escapeHtml(err.message)}</p>`;
  }
}

async function loadReviews() {
  const container = document.getElementById('review-list');
  try {
    const reviews = await apiRequest(`/reviews/?service_type=hotel&service_id=${HOTEL_ID}`);
    if (!reviews.length) {
      container.innerHTML = `<p class="muted">No reviews yet.</p>`;
      return;
    }
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

function openBookingModal(roomId) {
  document.getElementById('room-id').value = roomId;
  const checkin = document.getElementById('d-checkin').value;
  const checkout = document.getElementById('d-checkout').value;
  if (checkin) document.getElementById('b-checkin').value = checkin;
  if (checkout) document.getElementById('b-checkout').value = checkout;
  document.getElementById('booking-modal').classList.add('modal-overlay--open');
}
function closeBookingModal() {
  document.getElementById('booking-modal').classList.remove('modal-overlay--open');
}

document.getElementById('close-modal-btn').addEventListener('click', closeBookingModal);
document.getElementById('booking-modal').addEventListener('click', (e) => {
  if (e.target.id === 'booking-modal') closeBookingModal();
});

document.getElementById('check-availability-btn').addEventListener('click', loadHotel);

document.getElementById('booking-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('confirm-booking-btn');
  const payload = {
    room: Number(document.getElementById('room-id').value),
    check_in_date: document.getElementById('b-checkin').value,
    check_out_date: document.getElementById('b-checkout').value,
    guests: Number(document.getElementById('b-guests').value),
    payment_method: document.querySelector('input[name=payment]:checked').value,
    coupon_code: document.getElementById('b-coupon').value.trim(),
    terms_accepted: document.getElementById('b-terms').checked,
  };

  btn.disabled = true; btn.textContent = 'Booking...';
  try {
    const booking = await apiRequest('/hotels/bookings/', { method: 'POST', body: payload });
    showToast(`Booked! Invoice ${booking.invoice_id}`, 'success');
    closeBookingModal();
    setTimeout(() => window.location.href = '/bookings/', 900);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Confirm booking';
  }
});

loadHotel();
loadReviews();
