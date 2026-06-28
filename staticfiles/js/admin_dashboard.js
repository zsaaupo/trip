/* ============================== Tabs ============================== */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-btn--active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('tab-panel--active'));
    btn.classList.add('tab-btn--active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('tab-panel--active');
    loadPanel(btn.dataset.tab);
  });
});

const loadedPanels = new Set();
function loadPanel(name) {
  if (loadedPanels.has(name)) return;
  loadedPanels.add(name);
  ({
    overview: loadStats,
    hotels: loadHotels,
    buses: loadBuses,
    cars: loadCars,
    packages: loadPackages,
    bookings: loadAdminBookings,
    reviews: loadPendingReviews,
    coupons: loadCoupons,
  }[name] || (() => {}))();
}

function toggleForm(btnId, formId) {
  document.getElementById(btnId).addEventListener('click', () => {
    const form = document.getElementById(formId);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
  });
}
toggleForm('toggle-hotel-form', 'hotel-form');
toggleForm('toggle-bus-form', 'bus-form');
toggleForm('toggle-car-form', 'car-form');
toggleForm('toggle-package-form', 'package-form');
toggleForm('toggle-coupon-form', 'coupon-form');

/* ============================= Overview ============================= */
async function loadStats() {
  const container = document.getElementById('stats-grid');
  try {
    const s = await apiRequest('/dashboard/admin/stats/');
    const modules = ['hotel', 'bus', 'car', 'package'];
    const cards = [];
    cards.push(`<div class="stat-card"><div class="stat-card__value">${s.total_customers}</div><div class="stat-card__label">Total customers</div></div>`);
    cards.push(`<div class="stat-card"><div class="stat-card__value">${s.pending_reviews}</div><div class="stat-card__label">Pending reviews</div></div>`);
    modules.forEach(m => {
      cards.push(`<div class="stat-card"><div class="stat-card__value">${s.bookings_per_module[m]}</div><div class="stat-card__label">${m} bookings</div></div>`);
    });
    modules.forEach(m => {
      cards.push(`<div class="stat-card"><div class="stat-card__value">${s.pending_booking_approvals[m]}</div><div class="stat-card__label">${m} bookings pending approval</div></div>`);
    });
    modules.forEach(m => {
      cards.push(`<div class="stat-card"><div class="stat-card__value">${s.pending_listing_approvals[m]}</div><div class="stat-card__label">${m} listings pending approval</div></div>`);
    });
    container.innerHTML = `<div class="grid grid--4">${cards.join('')}</div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load stats: ${escapeHtml(err.message)}</p>`;
  }
}

/* ============================== Hotels ============================== */
let amenityCache = null;
async function getAmenities() {
  if (!amenityCache) amenityCache = await apiRequest('/hotels/amenities/');
  return amenityCache;
}

async function loadHotels() {
  const container = document.getElementById('hotels-table');
  try {
    const hotels = await apiRequest('/hotels/admin/');
    if (!hotels.length) { container.innerHTML = `<p class="muted">No hotels yet.</p>`; return; }
    const rows = hotels.map(h => `
      <tr>
        <td>${escapeHtml(h.name)}</td>
        <td>${escapeHtml(h.location)}</td>
        <td><span class="${statusBadgeClass(h.status)}">${escapeHtml(h.status)}</span></td>
        <td>
          ${h.status !== 'approved' ? `<button class="btn btn--small btn--primary" onclick="setHotelStatus(${h.id},'approved')">Approve</button>` : ''}
          ${h.status !== 'declined' ? `<button class="btn btn--small btn--danger" onclick="setHotelStatus(${h.id},'declined')">Decline</button>` : ''}
          <button class="btn btn--small btn--ghost" onclick="openRoomsModal(${h.id}, '${escapeHtml(h.name)}')">Rooms</button>
          <button class="btn btn--small btn--danger" onclick="deleteHotel(${h.id})">Delete</button>
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Name</th><th>Location</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load hotels: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('hotel-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    await apiRequest('/hotels/admin/', { method: 'POST', body: {
      name: document.getElementById('h-name').value,
      location: document.getElementById('h-location').value,
      description: document.getElementById('h-description').value,
    }});
    showToast('Hotel added.', 'success');
    e.target.reset(); e.target.style.display = 'none';
    loadedPanels.delete('hotels'); loadHotels();
  } catch (err) { showToast(err.message, 'error'); }
});

async function setHotelStatus(id, status) {
  try {
    await apiRequest(`/hotels/admin/${id}/status/${status}/`, { method: 'POST', body: {} });
    showToast(`Hotel ${status}.`, 'success');
    loadHotels();
  } catch (err) { showToast(err.message, 'error'); }
}
async function deleteHotel(id) {
  if (!confirm('Delete this hotel and all its rooms?')) return;
  try { await apiRequest(`/hotels/admin/${id}/`, { method: 'DELETE' }); showToast('Hotel deleted.', 'success'); loadHotels(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ------------------------------ Rooms ------------------------------ */
let currentRoomsHotelId = null;

async function openRoomsModal(hotelId, hotelName) {
  currentRoomsHotelId = hotelId;
  document.getElementById('rooms-modal-title').textContent = `Manage rooms — ${hotelName}`;
  document.getElementById('room-hotel-id').value = hotelId;
  await renderAmenityCheckboxes();
  await loadRooms();
  document.getElementById('rooms-modal').classList.add('modal-overlay--open');
}
document.getElementById('close-rooms-modal-btn').addEventListener('click', () => {
  document.getElementById('rooms-modal').classList.remove('modal-overlay--open');
});

async function renderAmenityCheckboxes() {
  const amenities = await getAmenities();
  document.getElementById('r-amenities').innerHTML = amenities.map(a => `
    <label style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;font-weight:400;">
      <input type="checkbox" value="${a.id}" class="r-amenity-cb"> ${escapeHtml(a.name)}
    </label>`).join('');
}

async function loadRooms() {
  const container = document.getElementById('rooms-list');
  try {
    const rooms = await apiRequest(`/hotels/admin/${currentRoomsHotelId}/rooms/`);
    if (!rooms.length) { container.innerHTML = `<p class="muted">No rooms yet for this hotel.</p>`; return; }
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Bed</th><th>Climate</th><th>Avail.</th><th>Price/night</th><th>Dates</th><th></th></tr></thead><tbody>
      ${rooms.map(r => `<tr>
        <td>${r.bed_type}</td><td>${r.climate_control}</td><td>${r.total_availability}</td>
        <td>${formatMoney(r.price_per_night)}</td><td>${r.check_in_date} → ${r.check_out_date}</td>
        <td><button class="btn btn--small btn--danger" onclick="deleteRoom(${r.id})">Delete</button></td>
      </tr>`).join('')}
    </tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load rooms: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('room-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('check_in_date', document.getElementById('r-checkin').value);
  formData.append('check_out_date', document.getElementById('r-checkout').value);
  formData.append('bed_type', document.getElementById('r-bed-type').value);
  formData.append('climate_control', document.getElementById('r-climate').value);
  formData.append('total_availability', document.getElementById('r-availability').value);
  formData.append('price_per_night', document.getElementById('r-price').value);
  formData.append('photo', document.getElementById('r-photo').files[0]);
  document.querySelectorAll('.r-amenity-cb:checked').forEach(cb => formData.append('amenity_ids', cb.value));

  try {
    await apiRequest(`/hotels/admin/${currentRoomsHotelId}/rooms/`, { method: 'POST', body: formData });
    showToast('Room added.', 'success');
    e.target.reset();
    loadRooms();
  } catch (err) { showToast(err.message, 'error'); }
});

async function deleteRoom(id) {
  if (!confirm('Delete this room?')) return;
  try { await apiRequest(`/hotels/admin/rooms/${id}/`, { method: 'DELETE' }); showToast('Room deleted.', 'success'); loadRooms(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Buses ============================== */
async function loadBuses() {
  const container = document.getElementById('buses-table');
  try {
    const buses = await apiRequest('/transport/admin/buses/');
    if (!buses.length) { container.innerHTML = `<p class="muted">No buses yet.</p>`; return; }
    const rows = buses.map(b => `
      <tr>
        <td>${escapeHtml(b.name)}</td>
        <td>${escapeHtml(b.route_origin)} → ${escapeHtml(b.route_destination)}</td>
        <td>${formatDateTime(b.trip_date)}</td>
        <td>${formatMoney(b.price_per_seat)}</td>
        <td><span class="${statusBadgeClass(b.status)}">${escapeHtml(b.status)}</span></td>
        <td>
          ${b.status !== 'approved' ? `<button class="btn btn--small btn--primary" onclick="setBusStatus(${b.id},'approved')">Approve</button>` : ''}
          ${b.status !== 'declined' ? `<button class="btn btn--small btn--danger" onclick="setBusStatus(${b.id},'declined')">Decline</button>` : ''}
          <button class="btn btn--small btn--danger" onclick="deleteBus(${b.id})">Delete</button>
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Name</th><th>Route</th><th>Trip date</th><th>Price/seat</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load buses: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('bus-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('name', document.getElementById('bus-name').value);
  formData.append('trip_date', document.getElementById('bus-trip-date').value);
  formData.append('route_origin', document.getElementById('bus-origin').value);
  formData.append('route_destination', document.getElementById('bus-destination').value);
  formData.append('climate_control', document.getElementById('bus-climate').value);
  formData.append('total_seats', document.getElementById('bus-seats').value);
  formData.append('price_per_seat', document.getElementById('bus-price').value);
  formData.append('photo', document.getElementById('bus-photo').files[0]);

  try {
    await apiRequest('/transport/admin/buses/', { method: 'POST', body: formData });
    showToast('Bus added.', 'success');
    e.target.reset(); e.target.style.display = 'none';
    loadBuses();
  } catch (err) { showToast(err.message, 'error'); }
});

async function setBusStatus(id, status) {
  try { await apiRequest(`/transport/admin/buses/${id}/status/${status}/`, { method: 'POST', body: {} }); showToast(`Bus ${status}.`, 'success'); loadBuses(); }
  catch (err) { showToast(err.message, 'error'); }
}
async function deleteBus(id) {
  if (!confirm('Delete this bus?')) return;
  try { await apiRequest(`/transport/admin/buses/${id}/`, { method: 'DELETE' }); showToast('Bus deleted.', 'success'); loadBuses(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Cars ============================== */
async function loadCars() {
  const container = document.getElementById('cars-table');
  try {
    const cars = await apiRequest('/transport/admin/cars/');
    if (!cars.length) { container.innerHTML = `<p class="muted">No cars yet.</p>`; return; }
    const rows = cars.map(c => `
      <tr>
        <td>${escapeHtml(c.name)}</td>
        <td>${c.trip_type}</td>
        <td>${c.capacity}</td>
<!--        <td>${formatDateTime(c.trip_date)}</td>-->
        <td>${formatMoney(c.price)}</td>
        <td><span class="${statusBadgeClass(c.status)}">${escapeHtml(c.status)}</span></td>
        <td>
          ${c.status !== 'approved' ? `<button class="btn btn--small btn--primary" onclick="setCarStatus(${c.id},'approved')">Approve</button>` : ''}
          ${c.status !== 'declined' ? `<button class="btn btn--small btn--danger" onclick="setCarStatus(${c.id},'declined')">Decline</button>` : ''}
          <button class="btn btn--small btn--danger" onclick="deleteCar(${c.id})">Delete</button>
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Name</th><th>Type</th><th>Capacity</th><th>Price</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load cars: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('car-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('name', document.getElementById('car-name').value);
  // formData.append('trip_date', document.getElementById('car-trip-date').value);
  formData.append('trip_type', document.getElementById('car-trip-type').value);
  // const returnDate = document.getElementById('car-return-date').value;
  // if (returnDate) formData.append('return_date', returnDate);
  formData.append('capacity', document.getElementById('car-capacity').value);
  formData.append('climate_control', document.getElementById('car-climate').value);
  formData.append('price', document.getElementById('car-price').value);
  formData.append('photo', document.getElementById('car-photo').files[0]);

  try {
    await apiRequest('/transport/admin/cars/', { method: 'POST', body: formData });
    showToast('Car added.', 'success');
    e.target.reset(); e.target.style.display = 'none';
    loadCars();
  } catch (err) { showToast(err.message, 'error'); }
});

async function setCarStatus(id, status) {
  try { await apiRequest(`/transport/admin/cars/${id}/status/${status}/`, { method: 'POST', body: {} }); showToast(`Car ${status}.`, 'success'); loadCars(); }
  catch (err) { showToast(err.message, 'error'); }
}
async function deleteCar(id) {
  if (!confirm('Delete this car?')) return;
  try { await apiRequest(`/transport/admin/cars/${id}/`, { method: 'DELETE' }); showToast('Car deleted.', 'success'); loadCars(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Packages ============================== */
async function populateHotelDropdown() {
  const sel = document.getElementById('p-hotel');
  try {
    const hotels = await apiRequest('/hotels/admin/');
    sel.innerHTML = '<option value="">None</option>' + hotels.map(h => `<option value="${h.id}">${escapeHtml(h.name)}</option>`).join('');
  } catch (e) { /* ignore */ }
}

async function populateTransportDropdown() {
  const type = document.getElementById('p-transport-type').value;
  const sel = document.getElementById('p-transport-id');
  if (!type) { sel.innerHTML = '<option value="">—</option>'; return; }
  try {
    const items = type === 'bus' ? await apiRequest('/transport/admin/buses/') : await apiRequest('/transport/admin/cars/');
    sel.innerHTML = '<option value="">—</option>' + items.map(i => `<option value="${i.id}">${escapeHtml(i.name)}</option>`).join('');
  } catch (e) { /* ignore */ }
}
document.getElementById('p-transport-type').addEventListener('change', populateTransportDropdown);

async function loadPackages() {
  populateHotelDropdown();
  const container = document.getElementById('packages-table');
  try {
    const packages = await apiRequest('/packages/admin/');
    if (!packages.length) { container.innerHTML = `<p class="muted">No packages yet.</p>`; return; }
    const rows = packages.map(p => `
      <tr>
        <td>${escapeHtml(p.name)}</td>
        <td>${escapeHtml(p.location)}</td>
        <td style="text-transform:capitalize;">${p.type}</td>
        <td>${formatDate(p.date)}</td>
        <td>${formatMoney(p.price)}</td>
        <td><span class="${statusBadgeClass(p.status)}">${escapeHtml(p.status)}</span></td>
        <td>
          ${p.status !== 'approved' ? `<button class="btn btn--small btn--primary" onclick="setPackageStatus(${p.id},'approved')">Approve</button>` : ''}
          ${p.status !== 'declined' ? `<button class="btn btn--small btn--danger" onclick="setPackageStatus(${p.id},'declined')">Decline</button>` : ''}
          <button class="btn btn--small btn--danger" onclick="deletePackage(${p.id})">Delete</button>
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Name</th><th>Location</th><th>Type</th><th>Date</th><th>Price</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load packages: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('package-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('name', document.getElementById('p-name').value);
  formData.append('location', document.getElementById('p-location').value);
  // formData.append('date', document.getElementById('p-date').value);
  formData.append('duration', document.getElementById('p-duration').value);
  formData.append('type', document.getElementById('p-type').value);
  const hotelId = document.getElementById('p-hotel').value;
  if (hotelId) formData.append('hotel', hotelId);
  const transportType = document.getElementById('p-transport-type').value;
  const transportId = document.getElementById('p-transport-id').value;
  if (transportType && transportId) {
    formData.append('transport_type', transportType);
    formData.append('transport_id', transportId);
  }
  formData.append('inclusions', document.getElementById('p-inclusions').value);
  formData.append('exclusions', document.getElementById('p-exclusions').value);
  formData.append('price', document.getElementById('p-price').value);
  formData.append('photo', document.getElementById('p-photo').files[0]);

  try {
    await apiRequest('/packages/admin/', { method: 'POST', body: formData });
    showToast('Package added.', 'success');
    e.target.reset(); e.target.style.display = 'none';
    loadPackages();
  } catch (err) { showToast(err.message, 'error'); }
});

async function setPackageStatus(id, status) {
  try { await apiRequest(`/packages/admin/${id}/status/${status}/`, { method: 'POST', body: {} }); showToast(`Package ${status}.`, 'success'); loadPackages(); }
  catch (err) { showToast(err.message, 'error'); }
}
async function deletePackage(id) {
  if (!confirm('Delete this package?')) return;
  try { await apiRequest(`/packages/admin/${id}/`, { method: 'DELETE' }); showToast('Package deleted.', 'success'); loadPackages(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Bookings ============================== */
const BOOKING_STATUS_URLS = {
  hotel: (id, status) => `/hotels/bookings/${id}/status/${status}/`,
  bus: (id, status) => `/transport/bus-bookings/${id}/status/${status}/`,
  car: (id, status) => `/transport/car-bookings/${id}/status/${status}/`,
  package: (id, status) => `/packages/bookings/${id}/status/${status}/`,
};

async function loadAdminBookings() {
  const container = document.getElementById('bookings-table');
  const typeFilter = document.getElementById('bk-type-filter').value;
  const statusFilter = document.getElementById('bk-status-filter').value;
  const params = statusFilter ? `?status=${statusFilter}` : '';
  try {
    let bookings = await apiRequest(`/dashboard/admin/all-bookings/${params}`);
    if (typeFilter) bookings = bookings.filter(b => b.booking_type === typeFilter);
    if (!bookings.length) { container.innerHTML = `<p class="muted">No bookings match this filter.</p>`; return; }
    const rows = bookings.map(b => `
      <tr>
        <td>${escapeHtml(b.invoice_id)}</td>
        <td style="text-transform:capitalize;">${b.booking_type}</td>
        <td>${escapeHtml(b.customer_name)}<div class="hint">${escapeHtml(b.customer_email)}</div></td>
        <td>${escapeHtml(b.service_name)}</td>
        <td>${formatDate(b.service_date)}</td>
        <td><span class="${statusBadgeClass(b.status)}">${escapeHtml(b.status_display)}</span></td>
        <td>${formatMoney(b.total_amount)}</td>
        <td>
          ${b.status === 'pending' ? `
            <button class="btn btn--small btn--primary" onclick="setBookingStatus('${b.booking_type}',${b.id},'confirmed')">Confirm</button>
            <button class="btn btn--small btn--danger" onclick="setBookingStatus('${b.booking_type}',${b.id},'declined')">Decline</button>` : ''}
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Invoice</th><th>Type</th><th>Customer</th><th>Service</th><th>Service date</th><th>Status</th><th>Total</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load bookings: ${escapeHtml(err.message)}</p>`;
  }
}
async function setBookingStatus(type, id, status) {
  try {
    await apiRequest(BOOKING_STATUS_URLS[type](id, status), { method: 'POST', body: {} });
    showToast(`Booking ${status}.`, 'success');
    loadAdminBookings();
  } catch (err) { showToast(err.message, 'error'); }
}
document.getElementById('bk-filter-btn').addEventListener('click', loadAdminBookings);

/* ============================== Reviews ============================== */
async function loadPendingReviews() {
  const container = document.getElementById('reviews-table');
  try {
    const reviews = await apiRequest('/reviews/pending/');
    if (!reviews.length) { container.innerHTML = `<p class="muted">No reviews waiting for moderation.</p>`; return; }
    const rows = reviews.map(r => `
      <tr>
        <td>${escapeHtml(r.customer_name || 'Customer')}</td>
        <td style="text-transform:capitalize;">${escapeHtml(r.booking_type || '')}</td>
        <td>${escapeHtml(r.service_name)}</td>
        <td>★ ${r.rating}</td>
        <td>${escapeHtml(r.comment || '')}</td>
        <td>
          <button class="btn btn--small btn--primary" onclick="moderateReview(${r.id},'approved')">Approve</button>
          <button class="btn btn--small btn--danger" onclick="moderateReview(${r.id},'declined')">Decline</button>
        </td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Customer</th><th>Type</th><th>Service</th><th>Rating</th><th>Comment</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load reviews: ${escapeHtml(err.message)}</p>`;
  }
}
async function moderateReview(id, status) {
  try {
    await apiRequest(`/reviews/${id}/moderate/`, { method: 'POST', body: { status } });
    showToast(`Review ${status}.`, 'success');
    loadPendingReviews();
  } catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Coupons ============================== */
async function loadCoupons() {
  const container = document.getElementById('coupons-table');
  try {
    const coupons = await apiRequest('/coupons/');
    if (!coupons.length) { container.innerHTML = `<p class="muted">No coupons yet.</p>`; return; }
    const rows = coupons.map(c => `
      <tr>
        <td><strong>${escapeHtml(c.code)}</strong></td>
        <td>${c.discount_type === 'percentage' ? c.discount_value + '%' : formatMoney(c.discount_value)}</td>
        <td>${formatDate(c.expiry_date)}</td>
        <td>${c.used_count} / ${c.max_usage_count}</td>
        <td>${c.is_global ? 'All customers' : 'Assigned only'}</td>
        <td><button class="btn btn--small btn--danger" onclick="deleteCoupon(${c.id})">Delete</button></td>
      </tr>`).join('');
    container.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr><th>Code</th><th>Discount</th><th>Expiry</th><th>Used</th><th>Audience</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (err) {
    container.innerHTML = `<p class="muted">Couldn't load coupons: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById('coupon-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    await apiRequest('/coupons/', { method: 'POST', body: {
      code: document.getElementById('c-code').value,
      discount_type: document.getElementById('c-discount-type').value,
      discount_value: document.getElementById('c-discount-value').value,
      expiry_date: document.getElementById('c-expiry').value,
      min_order_amount: document.getElementById('c-min-order').value || 0,
      max_usage_count: document.getElementById('c-max-usage').value || 1,
      is_global: document.getElementById('c-is-global').checked,
    }});
    showToast('Coupon added.', 'success');
    e.target.reset(); e.target.style.display = 'none';
    loadCoupons();
  } catch (err) { showToast(err.message, 'error'); }
});

async function deleteCoupon(id) {
  if (!confirm('Delete this coupon?')) return;
  try { await apiRequest(`/coupons/${id}/`, { method: 'DELETE' }); showToast('Coupon deleted.', 'success'); loadCoupons(); }
  catch (err) { showToast(err.message, 'error'); }
}

/* ============================== Init ============================== */
loadStats();
loadedPanels.add('overview');
