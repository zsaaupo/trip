function hotelCardHtml(h) {
  const minPrice = h.min_price != null ? formatMoney(h.min_price) + ' / night' : 'Price unavailable';
  const rating = h.avg_rating != null ? `<span class="rating-pill">★ ${h.avg_rating}</span>` : '';
  return `
    <a href="/hotels/${h.id}/" class="listing-card" style="text-decoration:none;color:inherit;">
      <img class="listing-card__image" src="${h.rooms[0] ? h.rooms[0].photo : ''}" alt="${escapeHtml(h.name)}">
      <div class="listing-card__body">
        <h3 class="listing-card__title">${escapeHtml(h.name)}</h3>
        <div class="listing-card__meta"><span>📍 ${escapeHtml(h.location)}</span> ${rating}</div>
        <div class="listing-card__footer">
          <span class="listing-card__price">${minPrice}</span>
          <span class="btn btn--ghost btn--small">View rooms</span>
        </div>
      </div>
    </a>`;
}

async function loadHotels() {
  const container = document.getElementById('hotel-results');
  container.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams();
  const location = document.getElementById('f-location').value.trim();
  const checkin = document.getElementById('f-checkin').value;
  const checkout = document.getElementById('f-checkout').value;
  const sort = document.getElementById('f-sort').value;
  if (location) params.set('location', location);
  if (checkin && checkout) { params.set('check_in', checkin); params.set('check_out', checkout); }
  if (sort) params.set('sort', sort);

  try {
    const hotels = await apiRequest('/hotels/?' + params.toString());
    if (!hotels.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🏨</div><p>No hotels match your search yet.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="grid grid--3">${hotels.map(hotelCardHtml).join('')}</div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load hotels: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('filter-form').addEventListener('submit', (e) => { e.preventDefault(); loadHotels(); });
loadHotels();
