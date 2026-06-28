function packageCardHtml(p) {
  const rating = p.avg_rating != null ? `<span class="rating-pill">★ ${p.avg_rating}</span>` : '';
  return `
    <a href="/packages/${p.id}/" class="listing-card" style="text-decoration:none;color:inherit;">
      <img class="listing-card__image" src="${p.photo}" alt="${escapeHtml(p.name)}">
      <div class="listing-card__body">
        <h3 class="listing-card__title">${escapeHtml(p.name)}</h3>
        <div class="listing-card__meta">
          <span>📍 ${escapeHtml(p.location)}</span>
          <span style="text-transform:capitalize;">${escapeHtml(p.type)}</span>
        </div>
        <div class="listing-card__meta"><span>${escapeHtml(p.duration)}</span> <span>${formatDate(p.date)}</span> ${rating}</div>
        <div class="listing-card__footer">
          <span class="listing-card__price">${formatMoney(p.price)} / person</span>
          <span class="btn btn--ghost btn--small">View details</span>
        </div>
      </div>
    </a>`;
}

async function loadPackages() {
  const container = document.getElementById('package-results');
  container.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams();
  const location = document.getElementById('f-location').value.trim();
  const type = document.getElementById('f-type').value;
  const sort = document.getElementById('f-sort').value;
  if (location) params.set('location', location);
  if (type) params.set('type', type);
  if (sort) params.set('sort', sort);

  try {
    const packages = await apiRequest('/packages/?' + params.toString());
    if (!packages.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🗺️</div><p>No packages match your search yet.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="grid grid--3">${packages.map(packageCardHtml).join('')}</div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load packages: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('filter-form').addEventListener('submit', (e) => { e.preventDefault(); loadPackages(); });
loadPackages();
