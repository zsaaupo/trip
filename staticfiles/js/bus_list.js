function busCardHtml(b) {
  const rating = b.avg_rating != null ? `<span class="rating-pill">★ ${b.avg_rating}</span>` : '';
  return `
    <a href="/transport/buses/${b.id}/" class="listing-card" style="text-decoration:none;color:inherit;">
      <img class="listing-card__image" src="${b.photo}" alt="${escapeHtml(b.name)}">
      <div class="listing-card__body">
        <h3 class="listing-card__title">${escapeHtml(b.name)}</h3>
        <div class="listing-card__meta">
          <span>${escapeHtml(b.route_origin)} → ${escapeHtml(b.route_destination)}</span>
        </div>
        <div class="listing-card__meta">
          <span>${formatDate(b.trip_date)}</span>
          <span>${b.climate_control === 'ac' ? '❄️ AC' : 'Non-AC'}</span>
          <span>${b.available_seats.length} seats left</span>
          ${rating}
        </div>
        <div class="listing-card__footer">
          <span class="listing-card__price">${formatMoney(b.price_per_seat)} / seat</span>
          <span class="btn btn--ghost btn--small">Select seats</span>
        </div>
      </div>
    </a>`;
}

async function loadBuses() {
  const container = document.getElementById('bus-results');
  container.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams();
  const location = document.getElementById('f-location').value.trim();
  const date = document.getElementById('f-date').value;
  const sort = document.getElementById('f-sort').value;
  if (location) params.set('location', location);
  if (date) params.set('trip_date', date);
  if (sort) params.set('sort', sort);

  try {
    const buses = await apiRequest('/transport/buses/?' + params.toString());
    if (!buses.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🚌</div><p>No buses match your search yet.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="grid grid--3">${buses.map(busCardHtml).join('')}</div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load buses: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('filter-form').addEventListener('submit', (e) => { e.preventDefault(); loadBuses(); });
loadBuses();
