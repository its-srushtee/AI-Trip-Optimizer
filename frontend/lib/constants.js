// Shared constants for the trip form, signup preferences and recommendation
// scoring. Moved from the original `src/data/trips.js`.

export const interests = [
  { id: 'adventure', label: 'Adventure', emoji: '⛰️' },
  { id: 'nature', label: 'Nature', emoji: '🌲' },
  { id: 'culture', label: 'Culture & History', emoji: '🏛️' },
  { id: 'food', label: 'Food & Culinary', emoji: '🍜' },
  { id: 'relaxation', label: 'Relaxation & Wellness', emoji: '🏖️' },
  { id: 'beaches', label: 'Beaches & Coastal', emoji: '🌊' },
  { id: 'shopping', label: 'Shopping', emoji: '🛍️' },
  { id: 'nightlife', label: 'Nightlife', emoji: '🌃' },
  { id: 'photography', label: 'Photography', emoji: '📸' },
  { id: 'spirituality', label: 'Spirituality', emoji: '🧘' },
  { id: 'family', label: 'Family-friendly', emoji: '👨‍👩‍👧‍👦' },
]

export const INTERESTS = interests.map((i) => ({
  id: i.id,
  name: i.label,
  icon: i.emoji,
}))


export const currencyOptions = [
  { code: 'INR', symbol: '₹', label: 'INR (₹)' },
  { code: 'USD', symbol: '$', label: 'USD ($)' },
  { code: 'EUR', symbol: '€', label: 'EUR (€)' },
  { code: 'GBP', symbol: '£', label: 'GBP (£)' },
  { code: 'CAD', symbol: 'C$', label: 'CAD ($)' },
  { code: 'AUD', symbol: 'A$', label: 'AUD ($)' },
  { code: 'JPY', symbol: '¥', label: 'JPY (¥)' },
]

export { formatCurrency, getCurrencySymbol, CURRENCY_SYMBOLS } from './format.js'


export const dietaryOptions = [
  'No preference',
  'Vegetarian',
  'Vegan',
  'Halal',
  'Kosher',
  'Gluten-Free',
]

export const accessibilityOptions = [
  'None required',
  'Wheelchair accessible',
  'Elevator required',
  'Ground-floor accommodation',
  'Low walking pace',
]

export const travelStyles = ['Backpacker', 'Budget', 'Comfort', 'Luxury']
export const tripPaces = ['Relaxed', 'Moderate', 'Fast-paced']
export const accommodationOptions = ['Hotel', 'Hostel', 'Resort', 'Homestay']
export const foodOptions = ['Vegetarian', 'Non-vegetarian', 'Vegan', 'No preference']

/** Returns today's local date as YYYY-MM-DD */
export const getTodayDateStr = () => {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/** Given a YYYY-MM-DD string, returns the next day as YYYY-MM-DD */
export const getNextDayDateStr = (dateStr) => {
  if (!dateStr) return getTodayDateStr()
  const parts = String(dateStr).split('-').map(Number)
  if (parts.length !== 3 || parts.some(isNaN)) return getTodayDateStr()
  const [y, m, d] = parts
  const dateObj = new Date(y, m - 1, d)
  dateObj.setDate(dateObj.getDate() + 1)
  const nextY = dateObj.getFullYear()
  const nextM = String(dateObj.getMonth() + 1).padStart(2, '0')
  const nextD = String(dateObj.getDate()).padStart(2, '0')
  return `${nextY}-${nextM}-${nextD}`
}
