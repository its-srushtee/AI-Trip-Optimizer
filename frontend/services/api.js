// ---------------------------------------------------------------------------
// API layer for AI Trip Optimizer — now wired to the FastAPI backend.
//
// In dev, the Vite proxy forwards `/api/*` -> `http://localhost:8000/*`,
// so the default BASE_URL below works for both local dev and the live preview.
// To point at a deployed backend instead, set VITE_API_URL in a .env file:
//
//   VITE_API_URL=https://api.yourdomain.com
// ---------------------------------------------------------------------------

export const BASE_URL = import.meta.env.VITE_API_URL || '/api'

/** Small fetch wrapper: JSON in/out, Bearer token, errors carry `status`. */
export async function request(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }

  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        msg = data.detail
      } else if (Array.isArray(data.detail)) {
        msg = data.detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
      } else if (typeof data.detail === 'object') {
        msg = JSON.stringify(data.detail)
      }
    }
    const err = new Error(msg)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

// ---- token helpers ----
export function getToken() {
  return localStorage.getItem('token')
}
export function setToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}
export function clearToken() {
  localStorage.removeItem('token')
}

// Resolve an image URL returned by the API (e.g. "/images/bali.jpg") into a
// URL the browser can load. Absolute URLs (CDN) pass through untouched.
export function resolveImageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  if (url.startsWith('/')) return url // same-origin, handled by the Vite proxy
  return BASE_URL + url
}

// ---- typed endpoint helpers ----
export const api = {
  signup: (body) => request('/auth/signup', { method: 'POST', body }),
  login: (body) => request('/auth/login', { method: 'POST', body }),

  googleAuth: (access_token) =>
  request('/auth/google', {
    method: 'POST',
    body: { access_token },
  }),

  me: (token) => request('/users/me', { token }),
  updateMe: (body, token) => request('/users/me', { method: 'PATCH', body, token }),
  listTrips: (token) => request('/trips', { token }),
  getTrip: (id, token) => request(`/trips/${id}`, { token }),
  createTrip: (body, token) => request('/trips', { method: 'POST', body, token }),
  updateTrip: (id, body, token) => request(`/trips/${id}`, { method: 'PATCH', body, token }),
  deleteTrip: (id, token) => request(`/trips/${id}`, { method: 'DELETE', token }),

  optimize: (body, token) => request('/trips/optimize', { method: 'POST', body, token }),
  destinations: () => request('/destinations'),
  autocompleteDestinations: (q) =>
    request(`/destinations/autocomplete?q=${encodeURIComponent(q)}`),
  searchDestinations: (q) =>
    request(`/destinations/search?q=${encodeURIComponent(q)}`),
  getDestinationPreferences: (destination) =>
    request(`/destinations/preferences?destination=${encodeURIComponent(destination)}`),
  recommendDestinations: (body) => request('/destinations/recommend', { method: 'POST', body }),
  destinationImage: (q) =>
    request(`/destinations/image?q=${encodeURIComponent(q)}`),
  imageProviders: () => request('/destinations/image-providers'),

  searchStations: (query) => request(`/trains/stations?query=${encodeURIComponent(query || '')}`),
  searchTrains: ({ from_station, to_station, date, currency }) =>
    request(
      `/trains/search?from_station=${encodeURIComponent(from_station)}&to_station=${encodeURIComponent(to_station)}&date=${encodeURIComponent(date)}&currency=${encodeURIComponent(currency || 'INR')}`
    ),

  // TripPulse AI Endpoints
  getTripPulse: (tripId, token) => request(`/trips/${tripId}/pulse`, { token }),
  simulateDisruption: (tripId, body, token) =>
    request(`/trips/${tripId}/pulse/simulate`, { method: 'POST', body, token }),
  triggerReoptimization: (tripId, token) =>
    request(`/trips/${tripId}/pulse/reoptimize`, { method: 'POST', token }),
  applyReoptimization: (tripId, reoptId, body, token) =>
    request(`/trips/${tripId}/pulse/reoptimize/${reoptId}/apply`, { method: 'POST', body, token }),
  rollbackReoptimization: (tripId, reoptId, token) =>
    request(`/trips/${tripId}/pulse/reoptimize/${reoptId}/rollback`, { method: 'POST', token }),
  dismissAlert: (tripId, alertId, token) =>
    request(`/trips/${tripId}/pulse/alerts/${alertId}/dismiss`, { method: 'POST', token }),

  // Smart Alternatives, Explainable Itinerary & What-If Simulation
  findAlternatives: (tripId, body, token) =>
    request(`/trips/${tripId}/alternatives`, { method: 'POST', body, token }),
  replaceAttraction: (tripId, body, token) =>
    request(`/trips/${tripId}/replace-attraction`, { method: 'POST', body, token }),
  getItineraryExplanations: (tripId, token) =>
    request(`/trips/${tripId}/itinerary-explanations`, { token }),
  simulateTripChanges: (tripId, body, token) =>
    request(`/trips/${tripId}/simulate`, { method: 'POST', body, token }),
  applyTripSimulation: (tripId, body, token) =>
    request(`/trips/${tripId}/apply-simulation`, { method: 'POST', body, token }),
}
