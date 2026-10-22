// Tiny mock user store (UI-only demo). When the real backend lands, replace
// this with the JWT session described in README.md / src/lib/api.js.
const KEY = 'tripopt_user'

export function saveUser(user) {
  localStorage.setItem(KEY, JSON.stringify(user))
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(KEY))
  } catch {
    return null
  }
}

export function updateUser(patch) {
  const next = { ...(getUser() || {}), ...patch }
  localStorage.setItem(KEY, JSON.stringify(next))
  return next
}

export function clearUser() {
  localStorage.removeItem(KEY)
}
