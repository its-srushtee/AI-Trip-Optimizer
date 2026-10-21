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
  { code: 'USD', symbol: '$', label: 'USD ($)' },
  { code: 'EUR', symbol: '€', label: 'EUR (€)' },
  { code: 'GBP', symbol: '£', label: 'GBP (£)' },
  { code: 'CAD', symbol: 'C$', label: 'CAD ($)' },
  { code: 'AUD', symbol: 'A$', label: 'AUD ($)' },
  { code: 'INR', symbol: '₹', label: 'INR (₹)' },
  { code: 'JPY', symbol: '¥', label: 'JPY (¥)' },
]

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

export const travelStyles = ['Budget', 'Comfort', 'Luxury']
export const tripPaces = ['Relaxed', 'Balanced', 'Packed']
export const accommodationOptions = ['Hotel', 'Hostel', 'Resort', 'Homestay']
export const foodOptions = ['Vegetarian', 'Non-vegetarian', 'Vegan', 'No preference']
