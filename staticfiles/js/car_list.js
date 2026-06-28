const TRIP_TYPE_LABELS = {
  hourly: 'Hourly',
  intercity_one_way: 'Intercity One-Way',
  intercity_round_trip: 'Intercity Round Trip',
};

function carCardHtml(c) {
  const rating = c.avg_rating != null ? `<span class="rating-pill">★ ${c.avg_rating}</span>` : '';
  return `
    <a href="/transport/cars/${c.id}/" class="listing-card" style="text-decoration:none;color:inherit;">
      <img class="listing-card__image" src="${c.photo}" alt="${escapeHtml(c.name)}">
      <div class="listing-card__body">
        <h3 class="listing-card__title">${escapeHtml(c.name)}</h3>
        <div class="listing-card__meta">
          <span>${TRIP_TYPE_LABELS[c.trip_type] || c.trip_type}</span>
          <span>${c.capacity} seats</span>
          <span>${c.climate_control === 'ac' ? '❄️ AC' : 'Non-AC'}</span>
        </div>
        <div class="listing-card__meta"><span>${formatDateTime(c.trip_date)}</span> ${rating}</div>
        <div class="listing-card__footer">
          <span class="listing-card__price">${formatMoney(c.price)}</span>
          <span class="btn btn--ghost btn--small">View & book</span>
        </div>
      </div>
    </a>`;
}

async function loadCars() {
  const container = document.getElementById('car-results');
  container.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams();
  const tripType = document.getElementById('f-trip-type').value;
  const capacity = document.getElementById('f-capacity').value;
  if (tripType) params.set('trip_type', tripType);
  if (capacity) params.set('capacity', capacity);

  try {
    const cars = await apiRequest('/transport/cars/?' + params.toString());
    if (!cars.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🚗</div><p>No cars match your search yet.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="grid grid--3">${cars.map(carCardHtml).join('')}</div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load cars: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('filter-form').addEventListener('submit', (e) => { e.preventDefault(); loadCars(); });
loadCars();
