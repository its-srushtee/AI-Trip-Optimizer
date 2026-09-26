
const REQUIRED_KEYS = ['style', 'interests', 'pace', 'accommodation', 'food']

const DISMISS_KEY = 'tripopt_profile_prompt_dismissed'

export function isProfileComplete(preferences) {
  const prefs = preferences || {}
  return REQUIRED_KEYS.every((key) => {
    const value = prefs[key]
    if (key === 'interests') return Array.isArray(value) && value.length > 0
    return typeof value === 'string' && value.trim().length > 0
  })
}

export function userProfileComplete(user) {
  if (!user) return false
  if (typeof user.profile_complete === 'boolean') return user.profile_complete
  return isProfileComplete(user.preferences)
}

export function isPromptDismissed(userId) {
  if (!userId) return false
  try {
    const raw = JSON.parse(localStorage.getItem(DISMISS_KEY)) || []
    return Array.isArray(raw) && raw.includes(userId)
  } catch {
    return false
  }
}

export function dismissPrompt(userId) {
  if (!userId) return
  try {
    const raw = JSON.parse(localStorage.getItem(DISMISS_KEY)) || []
    const list = Array.isArray(raw) ? raw : []
    if (!list.includes(userId)) {
      localStorage.setItem(DISMISS_KEY, JSON.stringify([...list, userId]))
    }
  } catch {
    localStorage.setItem(DISMISS_KEY, JSON.stringify([userId]))
  }
}

export function clearDismissed(userId) {
  if (!userId) return
  try {
    const raw = JSON.parse(localStorage.getItem(DISMISS_KEY)) || []
    const list = (Array.isArray(raw) ? raw : []).filter((id) => id !== userId)
    localStorage.setItem(DISMISS_KEY, JSON.stringify(list))
  } catch {
    
  }
}
