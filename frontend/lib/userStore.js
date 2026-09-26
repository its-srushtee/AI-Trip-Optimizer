
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
