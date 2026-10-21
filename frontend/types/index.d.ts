/**
 * Shared type shapes (documentation / editor IntelliSense).
 * This is a JS project — these declarations are inert at runtime and exist
 * purely to document the API contract the UI talks to.
 */

export interface Preferences {
  style: string
  interests: string[]
  pace: string
  accommodation: string
  food: string
}

export interface User {
  id: number
  name: string
  email: string
  preferences?: Partial<Preferences>
}

export interface Trip {
  id: number
  destination: string
  start_date: string
  end_date: string
  budget: number
  travelers: number
  interests: string[]
  status: string
}

export interface Destination {
  id: string
  name: string
  country: string
  image_url: string
  tags: string[]
  styles: string[]
  paces: string[]
  price: string
  blurb: string
}

export interface ItineraryDay {
  day: number
  date: string
  theme: string
  morning: string
  afternoon: string
  evening: string
  stay: string
  estimate_usd: number
}

export interface Itinerary {
  destination: string
  dates: { start: string; end: string; nights: number }
  travelers: number
  interests: string[]
  budget: number
  budget_breakdown: {
    flights: number
    stay: number
    food: number
    activities: number
    total: number
  }
  summary: string
  days: ItineraryDay[]
}
