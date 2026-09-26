
export const BASE_URL = import.meta.env.VITE_API_URL || '/api'

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
    const msg = data && data.detail ? data.detail : `Request failed (${res.status})`
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return data
}

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

export function resolveImageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  if (url.startsWith('/')) return url
  return BASE_URL + url
}

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
  createTrip: (body, token) => request('/trips', { method: 'POST', body, token }),
  deleteTrip: (id, token) => request(`/trips/${id}`, { method: 'DELETE', token }),
  optimize: (body, token) => request('/trips/optimize', { method: 'POST', body, token }),
  destinations: () => request('/destinations'),
  destinationImage: (q) =>
    request(`/destinations/image?q=${encodeURIComponent(q)}`),
  imageProviders: () => request('/destinations/image-providers'),
}
