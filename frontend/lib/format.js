/** Inclusive day count between two ISO dates. 0 when either is missing/invalid. */
export function daysBetween(start, end) {
  if (!start || !end) return 0
  const s = new Date(start)
  const e = new Date(end)
  if (isNaN(s) || isNaN(e)) return 0
  const diff = Math.round((e - s) / 86400000) + 1
  return diff > 0 ? diff : 0
}

export function formatRange(start, end) {
  if (!start || !end) return 'Dates not set'
  const s = new Date(start)
  const e = new Date(end)
  if (isNaN(s) || isNaN(e)) return `${start} – ${end}`
  const a = s.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const b = e.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${a} – ${b}`
}

export const CURRENCY_SYMBOLS = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
  CAD: 'CA$',
  AUD: 'A$',
  JPY: '¥',
  CHF: 'CHF',
  SGD: 'S$',
  AED: 'AED',
  THB: '฿',
  IDR: 'Rp',
}

export function getCurrencySymbol(currency = 'USD') {
  if (!currency) return '$'
  const c = String(currency).trim().toUpperCase()
  return CURRENCY_SYMBOLS[c] || (c === 'INR' ? '₹' : c === 'EUR' ? '€' : c === 'GBP' ? '£' : '$')
}

export function formatCurrency(amount, currency = 'USD') {
  const num = Number(amount)
  if (isNaN(num)) return ''
  const c = (currency || 'USD').toUpperCase()
  const sym = getCurrencySymbol(c)

  const locale = c === 'INR' ? 'en-IN' : 'en-US'
  return `${sym}${num.toLocaleString(locale)}`
}
