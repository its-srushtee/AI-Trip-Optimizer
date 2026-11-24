import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Calendar,
  Users,
  DollarSign,
  MapPin,
  Clock,
  Sparkles,
  Edit3,
  Trash2,
  Share2,
  Check,
  Compass,
  Plane,
  Hotel,
  Utensils,
  Activity,
  Layers,
  Info,
  Shield,
  Heart,
  Camera,
  RefreshCw,
  Sun,
  Moon,
  Coffee,
  Sunset,
  Sunrise,
  Map as MapIcon,
  List,
  Star,
  Luggage,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  CloudSun,
  X,
  ExternalLink,
  Coins,
  Wallet,
  Train,
  Navigation,
} from 'lucide-react'
import Sidebar from '../components/common/Sidebar.jsx'
import TripPulseTab from '../components/trippulse/TripPulseTab.jsx'
import AttractionExplanation from '../components/itinerary/AttractionExplanation.jsx'
import ReplaceAttractionModal from '../components/itinerary/ReplaceAttractionModal.jsx'
import WhatIfSimulator from '../components/itinerary/WhatIfSimulator.jsx'
import { useSidebar } from '../hooks/useSidebar.js'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { getUser, clearUser } from '../lib/userStore.js'
import { INTERESTS, currencyOptions, formatCurrency, getCurrencySymbol, getTodayDateStr, getNextDayDateStr } from '../lib/constants.js'

const TABS = [
  { id: 'overview', label: 'Overview', icon: Compass },
  { id: 'trippulse', label: 'TripPulse AI', icon: Activity },
  { id: 'itinerary', label: 'Itinerary', icon: Calendar },
  { id: 'places', label: 'Places to Visit', icon: MapPin },
  { id: 'map', label: 'Map', icon: MapIcon },
  { id: 'flights_stay', label: 'Flights & Stay', icon: Plane },
  { id: 'budget', label: 'Budget', icon: DollarSign },
]

function resolvePlaceImage(place, heroImage, destination) {
  const rawUrl = place.image_url || ''
  const isGenericHero =
    !rawUrl ||
    rawUrl === heroImage ||
    rawUrl.includes('/images/hero.jpg') ||
    rawUrl.includes('/images/goa.jpg')

  // If a place has its own external distinct photo, use it directly
  if (!isGenericHero && /^https?:\/\//i.test(rawUrl)) {
    return rawUrl
  }

  const name = (place.name || '').toLowerCase()
  const cat = (place.category || '').toLowerCase()
  const tags = (place.tags || []).map((t) => t.toLowerCase())

  // Distinct Thematic & Geographic Fallback Categories (generic, not destination-specific)
  if (name.includes('waterfall') || cat.includes('waterfall')) {
    return 'https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('scuba') || name.includes('snorkel') || name.includes('diving')) {
    return 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('fort') || name.includes('castle') || name.includes('palace') || cat.includes('fort')) {
    return 'https://images.unsplash.com/photo-1590523741831-ab7e8b8f9c7f?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('temple') || name.includes('church') || name.includes('basilica') || name.includes('cathedral') || cat.includes('religion')) {
    return 'https://images.unsplash.com/photo-1548625361-16eb16422f28?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('market') || name.includes('bazaar') || name.includes('quarter') || name.includes('street')) {
    return 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('seafood') || name.includes('restaurant') || name.includes('cafe') || cat.includes('food') || cat.includes('dining')) {
    return 'https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=800&q=80'
  }
  if (name.includes('spa') || name.includes('yoga') || name.includes('wellness') || cat.includes('wellness')) {
    return 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80'
  }

  // Thematic Category Imagery
  if (tags.includes('beaches') || cat.includes('beach') || name.includes('beach') || name.includes('coast')) {
    return 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80'
  }
  if (tags.includes('adventure') || cat.includes('adventure') || tags.includes('water sports')) {
    return 'https://images.unsplash.com/photo-1533240332313-0db49b459ad6?auto=format&fit=crop&w=800&q=80'
  }
  if (tags.includes('nature') || cat.includes('nature') || tags.includes('wildlife')) {
    return 'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80'
  }
  if (tags.includes('history') || tags.includes('culture') || cat.includes('history') || cat.includes('heritage')) {
    return 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=800&q=80'
  }
  if (tags.includes('nightlife') || cat.includes('nightlife')) {
    return 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80'
  }
  if (tags.includes('shopping') || cat.includes('shopping') || cat.includes('bazaar')) {
    return 'https://images.unsplash.com/photo-1605371924599-2d0365da1ae0?auto=format&fit=crop&w=800&q=80'
  }

  if (rawUrl && !isGenericHero) return resolveImageUrl(rawUrl)
  return heroImage
}

export default function TripDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const sidebarCollapsed = useSidebar()

  const [trip, setTrip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  // Destination image & catalogue
  const [heroImage, setHeroImage] = useState(resolveImageUrl('/images/hero.jpg'))

  // AI-generated itinerary and multi-agent plan
  const [itinerary, setItinerary] = useState(null)
  const [optimizing, setOptimizing] = useState(false)
  const [optimizeError, setOptimizeError] = useState('')

  const tripCurrency = useMemo(() => {
    const raw =
      trip?.currency ||
      trip?.preferences?.currency ||
      itinerary?.currency ||
      itinerary?.budget_breakdown?.currency ||
      'USD'
    return String(raw).toUpperCase()
  }, [trip, itinerary])

  const currencySymbol = useMemo(() => {
    return getCurrencySymbol(tripCurrency)
  }, [tripCurrency])

  // Edit trip modal state
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    budget: 1000,
    currency: 'USD',
    travelers: 1,
    interests: [],
  })
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Places filter
  const [placeCategory, setPlaceCategory] = useState('All')
  const [selectedDayIndex, setSelectedDayIndex] = useState(null) // null = all days

  // Transport sub-tabs (Flights vs Trains)
  const [transportTab, setTransportTab] = useState('flights')
  const [trainFrom, setTrainFrom] = useState('')
  const [trainTo, setTrainTo] = useState('')
  const [trainDate, setTrainDate] = useState('')
  const [trainsList, setTrainsList] = useState([])
  const [trainsLoading, setTrainsLoading] = useState(false)
  const [trainsError, setTrainsError] = useState('')

  // Map state
  const [selectedMapPlace, setSelectedMapPlace] = useState(null)
  const [mapProvider, setMapProvider] = useState('google')
  const [replaceTarget, setReplaceTarget] = useState(null)

  // Fetch trip details from backend
  const fetchTrip = async () => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    setLoading(true)
    setLoadError('')
    try {
      const data = await api.getTrip(id, token)
      setTrip(data)
      const c = String(data.currency || data.preferences?.currency || 'USD').toUpperCase()
      setEditForm({
        destination: data.destination || '',
        start_date: data.start_date || '',
        end_date: data.end_date || '',
        budget: data.budget || 1000,
        currency: c,
        travelers: data.travelers || 1,
        interests: Array.isArray(data.interests) ? data.interests : [],
      })

      // Fetch hero photo
      try {
        const imgRes = await api.destinationImage(data.destination)
        if (imgRes && imgRes.url) {
          setHeroImage(resolveImageUrl(imgRes.url))
        }
      } catch (e) {
        // Fallback hero
      }

      // Check for valid existing itinerary in database first, then sessionStorage (with integrity check)
      let validItinerary = null
      const tripDest = (data.destination || '').toLowerCase().trim()
      const tripOrig = (data.origin || data.preferences?.origin || '').toLowerCase().trim()

      const isItineraryValid = (itin) => {
        if (!itin || !Array.isArray(itin.days) || itin.days.length === 0) return false
        const itinDest = (itin.destination || '').toLowerCase().trim()
        if (itinDest && tripDest && !tripDest.includes(itinDest) && !itinDest.includes(tripDest)) {
          return false
        }
        // Verify flights do not have corrupted BOM->DEL when trip is not Mumbai to Delhi
        const sampleFlight = itin.transport?.flights?.[0]
        if (
          sampleFlight &&
          sampleFlight.departure_code === 'BOM' &&
          sampleFlight.arrival_code === 'DEL' &&
          !tripDest.includes('delhi') &&
          !tripOrig.includes('mumbai')
        ) {
          return false
        }
        return true
      }

      // Priority 1: Check database preferences
      if (isItineraryValid(data.preferences?.itinerary)) {
        validItinerary = data.preferences.itinerary
      }

      // Priority 2: Check sessionStorage cache if DB has no itinerary
      if (!validItinerary) {
        try {
          const cached = sessionStorage.getItem(`itinerary_trip_${id}`)
          if (cached) {
            const parsed = JSON.parse(cached)
            if (isItineraryValid(parsed)) {
              validItinerary = parsed
            } else {
              sessionStorage.removeItem(`itinerary_trip_${id}`)
            }
          }
        } catch (e) {
          sessionStorage.removeItem(`itinerary_trip_${id}`)
        }
      }

      if (validItinerary) {
        setItinerary(validItinerary)
        try {
          sessionStorage.setItem(`itinerary_trip_${id}`, JSON.stringify(validItinerary))
        } catch (e) {}
      } else {
        sessionStorage.removeItem(`itinerary_trip_${id}`)
        generatePlan(data, token)
      }
    } catch (err) {
      if (err.status === 401) {
        clearUser()
        clearToken()
        navigate('/login')
      } else {
        setLoadError(err.message || 'Unable to load trip details.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Geographic domestic India check
  const isDomesticIndia = useMemo(() => {
    const dest = (trip?.destination || '').toLowerCase()
    const orig = (trip?.origin || trip?.preferences?.origin || '').toLowerCase()
    const foreignKeywords = [
      'berlin', 'germany', 'paris', 'france', 'tokyo', 'japan', 'kyoto',
      'london', 'uk', 'united kingdom', 'bali', 'indonesia', 'alps', 'swiss',
      'switzerland', 'interlaken', 'usa', 'york', 'singapore', 'dubai', 'uae',
      'maldives', 'male', 'thailand', 'bangkok', 'rome', 'italy', 'spain',
      'madrid', 'barcelona', 'toronto', 'canada', 'sydney', 'australia',
      'europe', 'america', 'africa', 'new zealand', 'vietnam', 'greece',
      'cape town', 'vancouver', 'cairo', 'egypt', 'phuket', 'istanbul', 'turkey',
      'colombo', 'sri lanka', 'kathmandu', 'nepal', 'bhutan', 'malaysia', 'kuala lumpur',
      'philippines', 'palawan', 'south africa',
    ]
    if (foreignKeywords.some((k) => dest.includes(k) || orig.includes(k))) return false

    const indianDestinations = [
      'india', 'goa', 'manali', 'jaipur', 'agra', 'delhi', 'mumbai', 'kerala',
      'udaipur', 'shimla', 'kalka', 'chandigarh', 'bengaluru', 'bangalore', 'banglore',
      'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad', 'varanasi',
      'amritsar', 'haridwar', 'rishikesh', 'dehradun', 'ooty', 'munnar',
      'alleppey', 'hampi', 'mysore', 'pondicherry', 'ladakh', 'leh', 'kashmir',
      'srinagar', 'darjeeling', 'gangtok', 'andaman', 'coorg', 'lonavala',
      'nagpur', 'surat', 'lucknow', 'kanpur', 'patna', 'indore', 'bhopal',
    ]
    return indianDestinations.some((k) => dest.includes(k))
  }, [trip?.destination, trip?.origin, trip?.preferences?.origin])

  // Synchronize train search inputs with trip destination/dates
  useEffect(() => {
    if (trip) {
      setTrainFrom((prev) => prev || trip.origin || trip.preferences?.origin || 'Mumbai')
      const nearbyRail = itinerary?.transport?.nearby_transit?.nearby_railway?.name
      setTrainTo((prev) => prev || nearbyRail || trip.destination || '')
      setTrainDate((prev) => prev || trip.start_date || new Date().toISOString().slice(0, 10))
      if (!isDomesticIndia) {
        setTransportTab('flights')
        setTrainsList([])
      }
    }
  }, [trip, itinerary, isDomesticIndia])

  useEffect(() => {
    if (Array.isArray(itinerary?.transport?.trains) && itinerary.transport.trains.length > 0) {
      setTrainsList(itinerary.transport.trains)
    } else if (!isDomesticIndia) {
      setTrainsList([])
    }
  }, [itinerary, isDomesticIndia])

  const handleSearchTrains = async (e) => {
    if (e) e.preventDefault()
    if (!trainFrom.trim() || !trainTo.trim() || !trainDate) {
      setTrainsError('Please enter starting station/city, destination, and date.')
      return
    }

    const foreignKeywords = [
      'berlin', 'germany', 'paris', 'france', 'tokyo', 'japan', 'kyoto',
      'london', 'uk', 'united kingdom', 'bali', 'indonesia', 'alps', 'swiss',
      'switzerland', 'interlaken', 'usa', 'york', 'singapore', 'dubai', 'uae',
      'maldives', 'male', 'thailand', 'bangkok', 'rome', 'italy', 'spain',
    ]
    const fromL = trainFrom.toLowerCase()
    const toL = trainTo.toLowerCase()
    if (foreignKeywords.some((k) => fromL.includes(k) || toL.includes(k))) {
      setTrainsError(
        `No direct train route exists between ${trainFrom} and ${trainTo}. RailCore search is restricted to Indian Railway (IRCTC) stations. Please check the Flights tab for international travel.`
      )
      setTrainsList([])
      return
    }

    setTrainsLoading(true)
    setTrainsError('')
    try {
      const res = await api.searchTrains({
        from_station: trainFrom.trim(),
        to_station: trainTo.trim(),
        date: trainDate,
        currency: tripCurrency,
      })
      const found = Array.isArray(res.trains) ? res.trains : []
      setTrainsList(found)
      if (found.length === 0) {
        setTrainsError('No direct trains available for this corridor and date.')
      }
    } catch (err) {
      setTrainsError(err.message || 'Failed to search trains via RailCore.')
    } finally {
      setTrainsLoading(false)
    }
  }

  // Optimize itinerary via multi-agent workflow
  const generatePlan = async (tripData, tokenOverride) => {
    const token = tokenOverride || getToken()
    if (!tripData || !token) return
    setOptimizing(true)
    setOptimizeError('')
    try {
      const user = getUser()
      const userPrefs = user?.preferences || {}
      const tripPrefs = tripData.preferences || {}

      const effectiveCurrency = (
        tripData.currency ||
        tripPrefs.currency ||
        userPrefs.currency ||
        'USD'
      ).toUpperCase()

      const res = await api.optimize(
        {
          destination: tripData.destination,
          start_date: tripData.start_date || '2026-11-01',
          end_date: tripData.end_date || '2026-11-07',
          budget: tripData.budget || 1500,
          travelers: tripData.travelers || 1,
          interests: Array.isArray(tripData.interests) ? tripData.interests : [],
          style: tripPrefs.style || userPrefs.style || 'Comfort',
          pace: tripPrefs.pace || userPrefs.pace || 'Moderate',
          accommodation: tripPrefs.accommodation || userPrefs.accommodation || 'Hotel',
          food: tripPrefs.food || userPrefs.food || 'No preference',
          currency: effectiveCurrency,
          origin: tripPrefs.origin || userPrefs.origin || undefined,
          special_requests: tripPrefs.special_requests || undefined,
          accessibility: tripPrefs.accessibility || undefined,
          preferences: {
            ...userPrefs,
            ...tripPrefs,
            currency: effectiveCurrency,
          },
        },
        token
      )
      if (res && res.itinerary) {
        setItinerary(res.itinerary)
        const targetTripId = tripData.id || id
        try {
          sessionStorage.setItem(`itinerary_trip_${targetTripId}`, JSON.stringify(res.itinerary))
        } catch (e) {}

        // Persist the itinerary to trip preferences in DB so it remains consistent
        try {
          api.updateTrip(
            targetTripId,
            {
              preferences: {
                ...(tripData.preferences || {}),
                itinerary: res.itinerary,
              },
            },
            token
          ).catch(() => {})
        } catch (e) {}
      }
    } catch (err) {
      setOptimizeError(err.message || 'Could not generate AI itinerary plan.')
    } finally {
      setOptimizing(false)
    }
  }

  useEffect(() => {
    fetchTrip()
  }, [id])

  // Duration in days and nights
  const duration = useMemo(() => {
    if (!trip?.start_date || !trip?.end_date) return { days: 1, nights: 0 }
    const start = new Date(trip.start_date)
    const end = new Date(trip.end_date)
    const nights = Math.max(0, Math.round((end - start) / 86400000))
    return { days: nights + 1, nights }
  }, [trip])

  // Save edited trip
  const handleSaveEdit = async (e) => {
    e.preventDefault()
    setSavingEdit(true)
    setEditError('')

    const todayStr = getTodayDateStr()
    if (editForm.start_date < todayStr) {
      setEditError('Start date cannot be in the past. Please choose today or a future date.')
      setSavingEdit(false)
      return
    }
    if (editForm.end_date <= editForm.start_date) {
      setEditError('End date cannot be the same as or earlier than the start date. A trip must be at least 1 night.')
      setSavingEdit(false)
      return
    }

    try {
      const token = getToken()
      const targetCurr = (editForm.currency || tripCurrency || 'USD').toUpperCase()
      const updatePayload = {
        ...editForm,
        currency: targetCurr,
        preferences: {
          ...(trip?.preferences || {}),
          currency: targetCurr,
        },
      }
      const updated = await api.updateTrip(id, updatePayload, token)
      setTrip(updated)
      setSaveSuccess(true)
      setTimeout(() => {
        setSaveSuccess(false)
        setIsEditing(false)
      }, 1000)

      // Re-fetch destination image if destination changed
      if (updated.destination !== trip.destination) {
        try {
          const imgRes = await api.destinationImage(updated.destination)
          if (imgRes?.url) setHeroImage(resolveImageUrl(imgRes.url))
        } catch {}
      }

      // Re-run itinerary optimization with updated values and refresh cache
      try {
        sessionStorage.removeItem(`itinerary_trip_${id}`)
      } catch (e) {}
      generatePlan(updated, token)
    } catch (err) {
      setEditError(err.message || 'Failed to update trip.')
    } finally {
      setSavingEdit(false)
    }
  }

  // Toggle interest pill in edit form
  const toggleInterest = (interestName) => {
    const norm = interestName.toLowerCase()
    setEditForm((prev) => {
      const current = prev.interests || []
      const exists = current.some((i) => i.toLowerCase() === norm)
      return {
        ...prev,
        interests: exists
          ? current.filter((i) => i.toLowerCase() !== norm)
          : [...current, interestName],
      }
    })
  }

  // Curated places list from itinerary
  const places = useMemo(() => {
    return Array.isArray(itinerary?.places_to_visit) ? itinerary.places_to_visit : []
  }, [itinerary])

  // Filtered places
  const filteredPlaces = useMemo(() => {
    if (placeCategory === 'All') return places
    return places.filter(
      (p) =>
        p.category?.toLowerCase().includes(placeCategory.toLowerCase()) ||
        p.tags?.some((t) => t.toLowerCase().includes(placeCategory.toLowerCase()))
    )
  }, [places, placeCategory])

  // Available place categories
  const categoriesList = useMemo(() => {
    const set = new Set(['All'])
    places.forEach((p) => {
      if (p.category) {
        const clean = p.category.split('&')[0].trim()
        set.add(clean)
      }
    })
    return Array.from(set)
  }, [places])

  // Map destination coordinates lookup (dynamic geocoded coordinates with fallback)
  const mapCoords = useMemo(() => {
    const getLon = (obj) => {
      if (!obj) return undefined
      if (obj.lng !== undefined && obj.lng !== null) return Number(obj.lng)
      if (obj.lon !== undefined && obj.lon !== null) return Number(obj.lon)
      return undefined
    }

    // 1. Check if itinerary has dynamic coordinates from Geoapify
    if (itinerary?.coordinates?.lat && getLon(itinerary?.coordinates) !== undefined) {
      return {
        lat: Number(itinerary.coordinates.lat),
        lng: getLon(itinerary.coordinates),
        zoom: 12,
      }
    }
    // 2. Check if any place has coordinates
    const placeWithCoords = (places || []).find(
      (p) => p.coordinates?.lat && getLon(p.coordinates) !== undefined
    )
    if (placeWithCoords) {
      return {
        lat: Number(placeWithCoords.coordinates.lat),
        lng: getLon(placeWithCoords.coordinates),
        zoom: 12,
      }
    }
    // 3. Fallback dictionary for common travel hubs
    const dest = (trip?.destination || '').toLowerCase()
    if (dest.includes('bali')) return { lat: -8.4095, lng: 115.1889, zoom: 10 }
    if (dest.includes('paris')) return { lat: 48.8566, lng: 2.3522, zoom: 12 }
    if (dest.includes('tokyo')) return { lat: 35.6762, lng: 139.6503, zoom: 11 }
    if (dest.includes('alps') || dest.includes('swiss') || dest.includes('interlaken')) return { lat: 46.6863, lng: 7.8632, zoom: 11 }
    if (dest.includes('maldives')) return { lat: 3.2028, lng: 73.2207, zoom: 10 }
    if (dest.includes('goa')) return { lat: 15.2993, lng: 74.124, zoom: 10 }
    if (dest.includes('thailand') || dest.includes('bangkok')) return { lat: 13.7563, lng: 100.5018, zoom: 11 }
    if (dest.includes('rome')) return { lat: 41.9028, lng: 12.4964, zoom: 12 }
    if (dest.includes('kyoto')) return { lat: 35.0116, lng: 135.7681, zoom: 12 }
    if (dest.includes('manali')) return { lat: 32.2396, lng: 77.1887, zoom: 12 }
    if (dest.includes('jaipur')) return { lat: 26.9124, lng: 75.7873, zoom: 12 }
    if (dest.includes('berlin')) return { lat: 52.52, lng: 13.405, zoom: 12 }
    return { lat: 48.8566, lng: 2.3522, zoom: 11 }
  }, [trip?.destination, itinerary?.coordinates, places])

  if (loading) {
    return (
      <div className="min-h-screen w-full flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <Sidebar activeNav="My Trips" />
        <main
          className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
            sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
          }`}
        >
          <div className="flex flex-col items-center justify-center min-h-[70vh] p-6 text-center">
            <div className="h-14 w-14 rounded-2xl bg-violet-100 dark:bg-violet-950/60 flex items-center justify-center animate-pulse mb-4 text-violet-600 dark:text-violet-400">
              <Compass size={28} className="animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">Loading trip details…</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm">
              Retrieving your itinerary, attractions, and destination intelligence.
            </p>
          </div>
        </main>
      </div>
    )
  }

  if (loadError || !trip) {
    return (
      <div className="min-h-screen w-full flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <Sidebar activeNav="My Trips" />
        <main
          className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
            sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
          }`}
        >
          <div className="mx-auto max-w-2xl px-4 py-16 text-center">
            <div className="mx-auto h-16 w-16 rounded-2xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-4">
              <AlertCircle size={32} />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Trip Not Found</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 mb-6">
              {loadError || 'The requested trip could not be found or was deleted.'}
            </p>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 transition-colors shadow-sm"
            >
              <ArrowLeft size={16} /> Back to Dashboard
            </Link>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full flex bg-slate-50 dark:bg-[#0d0f14] text-slate-900 dark:text-slate-100 transition-colors duration-150">
      {/* Collapsible Sidebar */}
      <Sidebar activeNav="My Trips" />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        <section className="relative w-full overflow-hidden min-h-[380px] sm:min-h-[440px] lg:min-h-[480px] flex flex-col justify-between bg-slate-900 text-white">
          {/* Scenic Full-Width Destination Photograph */}
          <img
            src={heroImage}
            alt={trip.destination}
            referrerPolicy="no-referrer"
            onError={(e) => {
              e.currentTarget.onerror = null
              e.currentTarget.src = resolveImageUrl('/images/hero.jpg')
            }}
            className="absolute inset-0 h-full w-full object-cover object-center transition-transform duration-700 ease-out"
          />

          {/* Dark Gradient Overlay for Maximum Readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/45 to-black/25" />

          {/* Top Hero Bar (Back Button + Actions) */}
          <div className="relative z-10 mx-auto w-full max-w-7xl px-4 pt-6 sm:px-6 lg:px-8 flex items-center justify-between">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-white/20 px-3.5 py-1.5 text-xs font-semibold text-white backdrop-blur-md transition-all hover:bg-white/30 active:scale-95 border border-white/20"
            >
              <ArrowLeft size={14} />
              <span>Back to Dashboard</span>
            </Link>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => generatePlan(trip)}
                disabled={optimizing}
                className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3.5 py-1.5 text-xs font-semibold text-white backdrop-blur-md transition-all hover:bg-white/30 border border-white/20 active:scale-95 disabled:opacity-50"
                title="Regenerate with AI"
              >
                <Sparkles size={14} className={optimizing ? 'animate-spin' : ''} />
                <span>{optimizing ? 'Generating…' : 'Refresh AI Plan'}</span>
              </button>

              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-1.5 rounded-full bg-violet-600 hover:bg-violet-700 px-4 py-1.5 text-xs font-semibold text-white shadow-md transition-all active:scale-95 border border-violet-400/40"
              >
                <Edit3 size={14} />
                <span>Edit Trip</span>
              </button>
            </div>
          </div>

          {/* Bottom Hero Content: Title, Dates, Travelers, Badges */}
          <div className="relative z-10 mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
            <div className="max-w-3xl">
              {/* Trip Status Badge */}
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider backdrop-blur-md">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {trip.status || 'Active Journey'}
                </span>
                <span className="inline-flex items-center gap-1 text-[12px] font-medium text-slate-300">
                  <Clock size={13} className="text-violet-400" />
                  {duration.days} Days / {duration.nights} Nights
                </span>
              </div>

              {/* Destination Name */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight drop-shadow-md">
                {trip.destination}
              </h1>

              {/* Supporting Subtitle / AI Note */}
              <p className="mt-2 text-sm sm:text-base text-slate-200 line-clamp-2 max-w-2xl font-normal drop-shadow-xs">
                {itinerary?.summary ||
                  `Personalized travel plan for ${trip.travelers} traveler${trip.travelers > 1 ? 's' : ''} with a focus on ${trip.interests?.join(', ') || 'sights & local culture'}.`}
              </p>

              {/* Meta Pills (Dates, Travelers, Budget) */}
              <div className="mt-5 flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <Calendar size={14} className="text-violet-300" />
                  <span>
                    {trip.start_date
                      ? new Date(trip.start_date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                        })
                      : 'TBD'}{' '}
                    –{' '}
                    {trip.end_date
                      ? new Date(trip.end_date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })
                      : 'TBD'}
                  </span>
                </div>

                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <Users size={14} className="text-blue-300" />
                  <span>
                    {trip.travelers} Traveler{trip.travelers > 1 ? 's' : ''}
                  </span>
                </div>

                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <Coins size={14} className="text-emerald-300" />
                  <span>{formatCurrency(trip.budget, tripCurrency)} Budget</span>
                </div>

                {Array.isArray(trip?.interests) && trip.interests.length > 0 && (
                  <div className="hidden sm:flex items-center gap-1.5">
                    {trip.interests.slice(0, 3).map((int) => (
                      <span
                        key={int}
                        className="rounded-lg bg-violet-500/25 px-2.5 py-1 text-[11px] font-semibold text-violet-200 border border-violet-400/30 backdrop-blur-sm capitalize"
                      >
                        {int}
                      </span>
                    ))}
                    {trip.interests.length > 3 && (
                      <span className="text-[11px] text-slate-300">
                        +{trip.interests.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <div className="sticky top-14 lg:top-0 z-20 border-b border-slate-200/80 bg-white/95 dark:border-slate-800 dark:bg-slate-900/95 backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2 scrollbar-none" aria-label="Trip Tabs">
              {TABS.map((tab) => {
                const Icon = tab.icon
                const active = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-150 ${
                      active
                        ? 'bg-violet-600 text-white shadow-xs'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                    }`}
                  >
                    <Icon size={15} />
                    <span>{tab.label}</span>
                    {tab.id === 'trippulse' && (
                      <span
                        className={`ml-1 rounded-full px-1.5 py-0.2 text-[9px] font-black uppercase tracking-wider ${
                          active
                            ? 'bg-white/20 text-white'
                            : 'bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400'
                        }`}
                      >
                        Live
                      </span>
                    )}
                    {tab.id === 'itinerary' && itinerary?.days?.length > 0 && (
                      <span
                        className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                          active ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}
                      >
                        {itinerary.days.length}d
                      </span>
                    )}
                    {tab.id === 'places' && places.length > 0 && (
                      <span
                        className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                          active ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}
                      >
                        {places.length}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>
        </div>

        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-8 animate-fade-in">
              {/* Stat Cards Grid */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Duration
                    </span>
                    <Clock size={18} className="text-violet-600 dark:text-violet-400" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                    {duration.days} Days
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {duration.nights} night{duration.nights > 1 ? 's' : ''} stay
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Travelers
                    </span>
                    <Users size={18} className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                    {trip.travelers} Guest{trip.travelers > 1 ? 's' : ''}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {trip.travelers === 1 ? 'Solo Trip' : trip.travelers === 2 ? 'Couple / Duo' : 'Group Adventure'}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Est. Budget
                    </span>
                    <Coins size={18} className="text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                    {formatCurrency(trip.budget, tripCurrency)}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    ~{formatCurrency(Math.round(trip.budget / Math.max(1, duration.days)), tripCurrency)}/day
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Pace & Style
                    </span>
                    <Compass size={18} className="text-amber-600 dark:text-amber-400" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                    Balanced
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Comfort & Discovery
                  </p>
                </div>
              </div>

              {/* Two Column Section: Destination Blurb + Travel Preferences */}
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Destination Spotlight (2 cols) */}
                <div className="lg:col-span-2 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-lg bg-violet-50 dark:bg-violet-950/60 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                        <MapPin size={17} />
                      </div>
                      <h2 className="text-base font-bold text-slate-900 dark:text-white">
                        About {trip.destination}
                      </h2>
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Travel Guide</span>
                  </div>

                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {itinerary?.summary ||
                      `${trip.destination} offers stunning scenery, vibrant local culture, and memorable activities tailored to your itinerary. Whether exploring historical landmarks or enjoying regional gastronomy, your trip is set up for an unforgettable journey.`}
                  </p>

                  {/* Highlights Bullet List from Agent */}
                  <div className="mt-5 grid sm:grid-cols-2 gap-3">
                    <div className="flex items-start gap-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-transparent dark:border-slate-700/60 p-3">
                      <Check size={16} className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                          Handpicked Experiences
                        </h3>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          Activities organized by morning, afternoon, and evening to maximize time.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-transparent dark:border-slate-700/60 p-3">
                      <Check size={16} className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                          Budget Tracking
                        </h3>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          Calculated cost distribution across stay, flights, dining, and activities.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Quick CTAs */}
                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      onClick={() => setActiveTab('itinerary')}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-violet-700 transition-colors"
                    >
                      <Calendar size={14} /> View Day-by-Day Plan
                    </button>
                    <button
                      onClick={() => setActiveTab('places')}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                      <MapPin size={14} /> Recommended Attractions ({places.length})
                    </button>
                  </div>
                </div>

                {/* Selected Travel Preferences (1 col) */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900">
                  <div>
                    <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                      <div className="h-8 w-8 rounded-lg bg-pink-50 dark:bg-pink-950/60 text-pink-600 dark:text-pink-400 flex items-center justify-center">
                        <Heart size={17} />
                      </div>
                      <h2 className="text-base font-bold text-slate-900 dark:text-white">
                        Trip Preferences
                      </h2>
                    </div>

                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                      Your travel interests shape the activities and attractions suggested for this journey.
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {Array.isArray(trip?.interests) && trip.interests.length > 0 ? (
                        trip.interests.map((int) => (
                          <span
                            key={int}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-violet-50 dark:bg-violet-950/50 px-3 py-1.5 text-xs font-semibold text-violet-700 dark:text-violet-300 border border-violet-100 dark:border-violet-800/60 capitalize"
                          >
                            <Sparkles size={12} className="text-violet-500 dark:text-violet-400" />
                            {int}
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400 italic">
                          No specific interests chosen. Sights & culture default selected.
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
                    <button
                      onClick={() => setIsEditing(true)}
                      className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-200 dark:border-slate-700 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                    >
                      <Edit3 size={13} /> Edit Preferences & Details
                    </button>
                  </div>
                </div>
              </div>

              {/* Destination Weather & Climate Guidance Card */}
              {itinerary?.weather && (
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                    <div className="flex items-center gap-2.5">
                      <div className="h-8 w-8 rounded-lg bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center">
                        <CloudSun size={17} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-bold text-slate-900 dark:text-white">
                            Weather & Climate for {trip.destination}
                          </h3>
                          {itinerary.weather.is_live ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                              Live 5-Day Forecast
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800">
                              Seasonal Climate Guidance
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400">
                          {itinerary.weather.source || 'Regional Meteorological Guidance'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-xl font-extrabold text-slate-900 dark:text-white">
                          {itinerary.weather.current_or_typical_temp_c}°C
                        </span>
                        <span className="block text-[10px] text-slate-400 font-medium">
                          {itinerary.weather.temp_range || 'Typical Temp'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3.5 sm:grid-cols-3 text-xs">
                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                      <span className="font-bold text-slate-800 dark:text-slate-200 block mb-1">
                        {itinerary.weather.season ? 'Seasonal Context' : 'General Conditions'}
                      </span>
                      <p className="text-slate-600 dark:text-slate-300">
                        {itinerary.weather.season ? `${itinerary.weather.season} — ${itinerary.weather.condition}` : itinerary.weather.condition}
                      </p>
                    </div>

                    <div className="sm:col-span-2 rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                      <span className="font-bold text-slate-800 dark:text-slate-200 block mb-1">
                        Recommended Packing & Attire
                      </span>
                      <p className="text-slate-600 dark:text-slate-300">
                        {itinerary.weather.packing_advice}
                      </p>
                    </div>
                  </div>

                  {itinerary.weather.note && (
                    <div className="mt-3 flex items-start gap-1.5 text-[11px] text-slate-400 dark:text-slate-500">
                      <Info size={12} className="shrink-0 mt-0.5 text-slate-400" />
                      <span>{itinerary.weather.note}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Transport & Local Tips Card */}
              {itinerary?.transport?.guidelines && (
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center gap-2 mb-3">
                    <Luggage size={17} className="text-blue-600 dark:text-blue-400" />
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                      Local Transport & Travel Guidelines
                    </h3>
                  </div>
                  <div className="grid sm:grid-cols-3 gap-3">
                    {itinerary.transport.guidelines.map((guide, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-300"
                      >
                        <span className="font-semibold text-slate-800 dark:text-slate-200">Tip #{i + 1}:</span>{' '}
                        {guide}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DATE-WISE ITINERARY */}
          {activeTab === 'itinerary' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Date-Wise Itinerary Plan
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Day-by-day morning, afternoon, and evening activities tailored to your preferences.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => generatePlan(trip)}
                    disabled={optimizing}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-violet-50 text-violet-700 px-3 py-1.5 text-xs font-semibold hover:bg-violet-100 transition-colors border border-violet-100 dark:bg-violet-950/60 dark:text-violet-300 dark:border-violet-800 dark:hover:bg-violet-900/60"
                  >
                    <RefreshCw size={13} className={optimizing ? 'animate-spin' : ''} />
                    <span>{optimizing ? 'Optimizing…' : 'Regenerate Itinerary'}</span>
                  </button>
                </div>
              </div>

              {/* Day filter pills */}
              {itinerary?.days && itinerary.days.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  <button
                    onClick={() => setSelectedDayIndex(null)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                      selectedDayIndex === null
                        ? 'bg-slate-900 text-white dark:bg-violet-600 dark:text-white'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700'
                    }`}
                  >
                    All Days ({itinerary.days.length})
                  </button>
                  {itinerary.days.map((d, idx) => (
                    <button
                      key={d.day}
                      onClick={() => setSelectedDayIndex(idx)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                        selectedDayIndex === idx
                          ? 'bg-violet-600 text-white shadow-xs'
                          : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700'
                      }`}
                    >
                      Day {d.day}
                    </button>
                  ))}
                </div>
              )}

              {/* Loading State */}
              {optimizing && !itinerary && (
                <div className="space-y-4">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs animate-pulse dark:border-slate-800 dark:bg-slate-900"
                    >
                      <div className="h-5 w-40 bg-slate-200 dark:bg-slate-800 rounded mb-4" />
                      <div className="space-y-2">
                        <div className="h-4 w-full bg-slate-100 dark:bg-slate-800/60 rounded" />
                        <div className="h-4 w-3/4 bg-slate-100 dark:bg-slate-800/60 rounded" />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Error State */}
              {optimizeError && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 flex items-center justify-between">
                  <span>{optimizeError}</span>
                  <button
                    onClick={() => generatePlan(trip)}
                    className="font-bold underline ml-2"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* What-If Trip Simulator */}
              {itinerary?.days && itinerary.days.length > 0 && (
                <WhatIfSimulator
                  trip={trip}
                  itinerary={itinerary}
                  onApplied={(res) => {
                    if (res?.trip) setTrip(res.trip)
                    if (res?.itinerary) {
                      setItinerary(res.itinerary)
                      try {
                        sessionStorage.setItem(`itinerary_trip_${id}`, JSON.stringify(res.itinerary))
                      } catch (e) {}
                    }
                  }}
                />
              )}

              {/* Days List / Timeline */}
              {itinerary?.days && itinerary.days.length > 0 ? (
                <div className="space-y-6">
                  {itinerary.days
                    .filter((_, idx) => selectedDayIndex === null || selectedDayIndex === idx)
                    .map((day) => (
                      <article
                        key={day.day}
                        className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900/95"
                      >
                        {/* Day Card Header */}
                        <div className="day-card-header flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 bg-slate-100 px-5 py-3.5 dark:border-slate-700 dark:bg-slate-800">
                          <div className="flex items-center gap-3">
                            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-600 text-xs font-bold text-white shadow-xs">
                              {day.day}
                            </span>
                            <div>
                              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                                Day {day.day}: {day.theme || 'Exploration & Sights'}
                              </h3>
                              <p className="text-[11px] text-slate-500 dark:text-slate-300 font-medium">
                                {day.date
                                  ? new Date(day.date).toLocaleDateString('en-US', {
                                      weekday: 'long',
                                      month: 'short',
                                      day: 'numeric',
                                    })
                                  : `Day ${day.day}`}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 text-xs">
                            <span className="day-est-badge rounded-full bg-emerald-100 text-emerald-900 border border-emerald-400 px-3 py-1 font-bold shadow-xs dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-600">
                              Est. {formatCurrency(day.estimate_cost || day.estimate_usd || Math.round(trip.budget / duration.days), tripCurrency)}
                            </span>
                            <span className="text-slate-400 dark:text-slate-500">·</span>
                            <span className="text-slate-700 dark:text-slate-200 font-medium truncate max-w-[220px]">
                              {day.stay || `Stay in ${trip.destination}`}
                            </span>
                          </div>
                        </div>

                        {/* Day Content Body */}
                        <div className="p-5 sm:p-6 space-y-5">
                          {/* Day summary/description if present */}
                          {day.description && (
                            <p className="text-xs text-slate-700 dark:text-slate-200 italic border-l-2 border-violet-500 pl-3 leading-relaxed">
                              {day.description}
                            </p>
                          )}

                          {/* Pace note indicator */}
                          {day.pace_notes && (
                            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100 dark:bg-slate-800/90 dark:border-slate-700/80 dark:text-slate-200">
                              <Clock size={12} className="text-violet-500 dark:text-violet-400 shrink-0" />
                              <span>{day.pace_notes}</span>
                            </div>
                          )}

                          {/* 3 Activities Blocks: Morning, Afternoon, Evening */}
                          <div className="grid gap-3.5 sm:grid-cols-3">
                            {/* Morning Block */}
                            {(() => {
                              const act = (day.activities || []).find((a) => a.time_slot?.toLowerCase() === 'morning')
                              return (
                                <div className="activity-card-morning rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-500/40 dark:bg-slate-800/90 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-center justify-between gap-1 mb-2">
                                      <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                                        <Sunrise size={16} />
                                        <span className="text-xs font-bold uppercase tracking-wider">
                                          Morning
                                        </span>
                                      </div>
                                      {act?.time_window && (
                                        <span className="text-[10px] font-semibold text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-950 dark:border dark:border-amber-700/50 px-2 py-0.5 rounded-md">
                                          {act.time_window}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-800 dark:text-slate-100 leading-relaxed font-normal">
                                      {day.morning}
                                    </p>
                                  </div>
                                  {act && (act.estimated_cost || act.estimated_duration) && (
                                    <div className="mt-3 pt-2.5 border-t border-amber-200/60 dark:border-slate-700/80 flex items-center justify-between text-[11px] text-amber-900 dark:text-amber-300 font-medium">
                                      {act.estimated_duration && <span>⏱ {act.estimated_duration}</span>}
                                      {act.estimated_cost && <span className="font-semibold text-emerald-700 dark:text-emerald-300">💰 {act.estimated_cost}</span>}
                                    </div>
                                  )}
                                  {act && (
                                    <AttractionExplanation
                                      activity={act}
                                      onFindAlternative={() => setReplaceTarget({ dayNumber: day.day, activity: act })}
                                    />
                                  )}
                                </div>
                              )
                            })()}

                            {/* Afternoon Block */}
                            {(() => {
                              const act = (day.activities || []).find((a) => a.time_slot?.toLowerCase() === 'afternoon')
                              return (
                                <div className="activity-card-afternoon rounded-xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-500/40 dark:bg-slate-800/90 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-center justify-between gap-1 mb-2">
                                      <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
                                        <Sun size={16} />
                                        <span className="text-xs font-bold uppercase tracking-wider">
                                          Afternoon
                                        </span>
                                      </div>
                                      {act?.time_window && (
                                        <span className="text-[10px] font-semibold text-blue-800 dark:text-blue-300 bg-blue-100 dark:bg-blue-950 dark:border dark:border-blue-700/50 px-2 py-0.5 rounded-md">
                                          {act.time_window}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-800 dark:text-slate-100 leading-relaxed font-normal">
                                      {day.afternoon}
                                    </p>
                                  </div>
                                  {act && (act.estimated_cost || act.estimated_duration) && (
                                    <div className="mt-3 pt-2.5 border-t border-blue-200/60 dark:border-slate-700/80 flex items-center justify-between text-[11px] text-blue-900 dark:text-blue-300 font-medium">
                                      {act.estimated_duration && <span>⏱ {act.estimated_duration}</span>}
                                      {act.estimated_cost && <span className="font-semibold text-emerald-700 dark:text-emerald-300">💰 {act.estimated_cost}</span>}
                                    </div>
                                  )}
                                  {act && (
                                    <AttractionExplanation
                                      activity={act}
                                      onFindAlternative={() => setReplaceTarget({ dayNumber: day.day, activity: act })}
                                    />
                                  )}
                                </div>
                              )
                            })()}

                            {/* Evening Block */}
                            {(() => {
                              const act = (day.activities || []).find((a) => a.time_slot?.toLowerCase() === 'evening')
                              return (
                                <div className="activity-card-evening rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 dark:border-indigo-500/40 dark:bg-slate-800/90 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-center justify-between gap-1 mb-2">
                                      <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-400">
                                        <Sunset size={16} />
                                        <span className="text-xs font-bold uppercase tracking-wider">
                                          Evening
                                        </span>
                                      </div>
                                      {act?.time_window && (
                                        <span className="text-[10px] font-semibold text-indigo-800 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-950 dark:border dark:border-indigo-700/50 px-2 py-0.5 rounded-md">
                                          {act.time_window}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-800 dark:text-slate-100 leading-relaxed font-normal">
                                      {day.evening}
                                    </p>
                                  </div>
                                  {act && (act.estimated_cost || act.estimated_duration) && (
                                    <div className="mt-3 pt-2.5 border-t border-indigo-200/60 dark:border-slate-700/80 flex items-center justify-between text-[11px] text-indigo-900 dark:text-indigo-300 font-medium">
                                      {act.estimated_duration && <span>⏱ {act.estimated_duration}</span>}
                                      {act.estimated_cost && <span className="font-semibold text-emerald-700 dark:text-emerald-300">💰 {act.estimated_cost}</span>}
                                    </div>
                                  )}
                                  {act && (
                                    <AttractionExplanation
                                      activity={act}
                                      onFindAlternative={() => setReplaceTarget({ dayNumber: day.day, activity: act })}
                                    />
                                  )}
                                </div>
                              )
                            })()}
                          </div>

                          {/* Meal Suggestions */}
                          {day.meal_suggestions && (
                            <div className="culinary-card rounded-xl border border-orange-200 bg-orange-50/60 p-3.5 text-xs space-y-2 dark:border-orange-500/40 dark:bg-slate-800/90">
                              <div className="flex items-center gap-1.5 text-orange-700 dark:text-orange-400 font-bold text-xs uppercase tracking-wider">
                                <Utensils size={13} />
                                <span>Curated Culinary Highlights</span>
                              </div>
                              <div className="grid gap-2 text-xs text-slate-700 dark:text-slate-100 sm:grid-cols-3 pt-1">
                                <div><span className="font-bold text-orange-950 dark:text-orange-300">Breakfast:</span> <span className="text-slate-800 dark:text-slate-100">{day.meal_suggestions.breakfast}</span></div>
                                <div><span className="font-bold text-orange-950 dark:text-orange-300">Lunch:</span> <span className="text-slate-800 dark:text-slate-100">{day.meal_suggestions.lunch}</span></div>
                                <div><span className="font-bold text-orange-950 dark:text-orange-300">Dinner:</span> <span className="text-slate-800 dark:text-slate-100">{day.meal_suggestions.dinner}</span></div>
                              </div>
                            </div>
                          )}

                          {/* Suggested Places to Visit for this Day */}
                          {day.suggested_places && day.suggested_places.length > 0 && (
                            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-300 block mb-2">
                                Featured Places for Day {day.day}
                              </span>
                              <div className="flex flex-wrap gap-2">
                                {day.suggested_places.map((placeName, pi) => (
                                  <span
                                    key={pi}
                                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-800 hover:bg-slate-200 transition-colors dark:bg-slate-800 dark:text-slate-100 dark:border dark:border-slate-700 dark:hover:bg-slate-700"
                                  >
                                    <MapPin size={12} className="text-violet-600 dark:text-violet-400" />
                                    {placeName}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </article>
                    ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
                  <Compass size={32} className="mx-auto text-slate-300 dark:text-slate-600 mb-2" />
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">No itinerary generated yet.</p>
                  <p className="text-xs text-slate-400 mt-1 mb-4">
                    Click the button below to generate a tailored date-wise plan.
                  </p>
                  <button
                    onClick={() => generatePlan(trip)}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-xs"
                  >
                    <Sparkles size={14} /> Generate Itinerary Now
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: PLACES TO VISIT */}
          {activeTab === 'places' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Recommended Places & Attractions
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Curated points of interest in {trip.destination}, prioritized by your selected travel preferences.
                  </p>
                </div>
              </div>

              {/* Category Filter Pills */}
              {categoriesList.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  {categoriesList.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setPlaceCategory(cat)}
                      className={`rounded-full px-3.5 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                        placeCategory === cat
                          ? 'bg-violet-600 text-white shadow-xs'
                          : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              )}

              {/* Places Grid */}
              {filteredPlaces.length > 0 ? (
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredPlaces.map((place, idx) => {
                    const placeImg = resolvePlaceImage(place, heroImage, trip?.destination)
                    // Check if place matches any user interest
                    const matchesPreference = (trip.interests || []).some(
                      (int) =>
                        place.tags?.includes(int.toLowerCase()) ||
                        place.category?.toLowerCase().includes(int.toLowerCase())
                    )

                    return (
                      <article
                        key={idx}
                        className="group overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900"
                      >
                        <div>
                          {/* Image Thumbnail with Overlay */}
                          <div className="relative h-48 w-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                            <img
                              src={placeImg}
                              alt={place.name}
                              referrerPolicy="no-referrer"
                              onError={(e) => {
                                e.currentTarget.onerror = null
                                e.currentTarget.src = resolveImageUrl('/images/hero.jpg')
                              }}
                              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-black/20" />

                            {/* Category Badge */}
                            <span className="absolute top-3 left-3 rounded-full bg-white/90 dark:bg-slate-900/90 px-2.5 py-1 text-[10px] font-bold text-slate-800 dark:text-slate-100 shadow-xs backdrop-blur-md">
                              {place.category || 'Attraction'}
                            </span>

                            {/* Preference Match Badge */}
                            {matchesPreference && (
                              <span className="absolute top-3 right-3 rounded-full bg-violet-600/90 text-white px-2 py-0.5 text-[10px] font-bold shadow-xs backdrop-blur-md flex items-center gap-1">
                                <Sparkles size={10} /> Top Match
                              </span>
                            )}

                            {/* Rating on image */}
                            <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-bold text-amber-300 backdrop-blur-md">
                              <Star size={12} fill="currentColor" />
                              <span>{place.rating || 4.8}</span>
                            </div>

                            <div className="absolute bottom-3 left-3 text-white pr-16">
                              <h3 className="text-base font-bold drop-shadow-xs line-clamp-1">
                                {place.name}
                              </h3>
                            </div>
                          </div>

                          {/* Card Details */}
                          <div className="p-4 space-y-2.5">
                            <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed">
                              {place.description}
                            </p>

                            {place.why_it_matches && (
                              <div className="flex items-start gap-1.5 rounded-lg bg-violet-50 dark:bg-violet-950/50 p-2 text-[11px] text-violet-900 dark:text-violet-200 border border-violet-100 dark:border-violet-800/60">
                                <Sparkles size={12} className="text-violet-600 dark:text-violet-400 shrink-0 mt-0.5" />
                                <span className="font-medium leading-snug">{place.why_it_matches}</span>
                              </div>
                            )}

                            {/* Location & Duration */}
                            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-1">
                              <div className="flex items-center gap-1.5 truncate">
                                <MapPin size={13} className="text-violet-500 shrink-0" />
                                <span className="truncate">{place.address || place.location || trip.destination}</span>
                              </div>
                              {place.estimated_duration && (
                                <div className="flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border dark:border-emerald-800/60 px-2 py-0.5 rounded-md font-medium shrink-0 ml-2">
                                  <Clock size={11} />
                                  <span>{place.estimated_duration}</span>
                                </div>
                              )}
                            </div>

                            {/* Verification Source Badge if available */}
                            {place.source && (
                              <div className="flex items-center gap-1 text-[10px] font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50/70 dark:bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-100 dark:border-emerald-900/60 w-fit">
                                <Shield size={10} className="shrink-0" />
                                <span>{place.source}</span>
                              </div>
                            )}

                            {place.visit_info && (
                              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/70 rounded-lg p-2 border border-slate-100 dark:border-slate-700">
                                <Info size={12} className="text-blue-500 shrink-0" />
                                <span className="line-clamp-1">{place.visit_info}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Card Footer */}
                        <div className="p-4 pt-0">
                          <button
                            type="button"
                            onClick={() => {
                              window.open(
                                `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                                  place.name + ' ' + trip.destination
                                )}`,
                                '_blank'
                              )
                            }}
                            className="w-full flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-700 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                          >
                            <span>Explore on Map</span>
                            <ExternalLink size={12} />
                          </button>
                        </div>
                      </article>
                    )
                  })}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-sm text-slate-500 dark:text-slate-400">No attractions match the selected filter.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MAP */}
          {activeTab === 'map' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Destination & Attractions Map
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Interactive geographic overview of {trip.destination} and {places.length} marked points of interest.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200/80 dark:border-slate-700 text-xs">
                    <button
                      type="button"
                      onClick={() => setMapProvider('google')}
                      className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                        mapProvider === 'google'
                          ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-300 shadow-xs'
                          : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
                      }`}
                    >
                      Google Maps
                    </button>
                    <button
                      type="button"
                      onClick={() => setMapProvider('osm')}
                      className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                        mapProvider === 'osm'
                          ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-300 shadow-xs'
                          : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
                      }`}
                    >
                      OpenStreetMap
                    </button>
                  </div>

                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                      selectedMapPlace ? `${selectedMapPlace.name}, ${trip.destination}` : `${trip.destination} tourist attractions`
                    )}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-750 transition-all shadow-xs"
                  >
                    <span>Open in Maps</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                {/* Embedded Map Canvas (2 cols) */}
                <div className="lg:col-span-2 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs h-[480px] relative dark:border-slate-800 dark:bg-slate-900 flex flex-col">
                  {selectedMapPlace && (
                    <div className="absolute top-3 left-3 z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-xl p-2.5 shadow-md border border-slate-200/80 dark:border-slate-700 max-w-sm flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <span className="text-[10px] font-bold text-violet-600 dark:text-violet-400 uppercase tracking-wider block">
                          Focused Pin
                        </span>
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {selectedMapPlace.name}
                        </h4>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                          {selectedMapPlace.location || trip.destination}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setSelectedMapPlace(null)}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg"
                        title="Reset to whole destination view"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}

                  {mapProvider === 'google' ? (
                    <iframe
                      title="Google Maps"
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      scrolling="no"
                      loading="lazy"
                      src={`https://maps.google.com/maps?q=${encodeURIComponent(
                        selectedMapPlace
                          ? `${selectedMapPlace.name}, ${selectedMapPlace.location || trip.destination}`
                          : `${trip.destination} tourist attractions`
                      )}&t=&z=${selectedMapPlace ? 15 : 12}&ie=UTF8&iwloc=&output=embed`}
                      className="w-full h-full border-0"
                    />
                  ) : (
                    <iframe
                      title="OpenStreetMap"
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      scrolling="no"
                      marginHeight="0"
                      marginWidth="0"
                      src={`https://www.openstreetmap.org/export/embed.html?bbox=${
                        mapCoords.lng - 0.2
                      }%2C${mapCoords.lat - 0.2}%2C${mapCoords.lng + 0.2}%2C${
                        mapCoords.lat + 0.2
                      }&layer=mapnik&marker=${mapCoords.lat}%2C${mapCoords.lng}`}
                      className="w-full h-full border-0"
                    />
                  )}

                  <div className="absolute bottom-3 right-3 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md rounded-lg px-2.5 py-1 text-[10px] text-slate-600 dark:text-slate-300 shadow-xs border border-slate-200 dark:border-slate-700">
                    {mapProvider === 'google' ? '© Google Maps' : '© OpenStreetMap Contributors'}
                  </div>
                </div>

                {/* Places Pinpoint List (1 col) */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs overflow-y-auto max-h-[480px] dark:border-slate-800 dark:bg-slate-900 flex flex-col">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400">
                      Locations Marked ({places.length})
                    </h3>
                    <span className="text-[10px] text-slate-400">Click to pin on map</span>
                  </div>
                  <div className="space-y-2 flex-1 overflow-y-auto pr-1">
                    {places.map((p, i) => {
                      const isSelected = selectedMapPlace?.name === p.name
                      return (
                        <div
                          key={i}
                          role="button"
                          tabIndex={0}
                          onClick={() => setSelectedMapPlace(isSelected ? null : p)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              setSelectedMapPlace(isSelected ? null : p)
                            }
                          }}
                          className={`flex items-start gap-3 rounded-xl border p-2.5 transition-all text-left w-full cursor-pointer ${
                            isSelected
                              ? 'border-violet-500 bg-violet-50/70 dark:border-violet-500/80 dark:bg-violet-950/40 shadow-xs'
                              : 'border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                          }`}
                        >
                          <span className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold shrink-0 ${
                            isSelected
                              ? 'bg-violet-600 text-white'
                              : 'bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300'
                          }`}>
                            {i + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <h4 className={`text-xs font-bold truncate ${
                              isSelected ? 'text-violet-900 dark:text-violet-200' : 'text-slate-800 dark:text-slate-200'
                            }`}>
                              {p.name}
                            </h4>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                              {p.location || trip.destination}
                            </p>
                          </div>
                          {isSelected && (
                            <span className="text-[10px] font-bold text-violet-600 dark:text-violet-400 bg-white dark:bg-slate-900 px-1.5 py-0.5 rounded border border-violet-200 dark:border-violet-800">
                              Active
                            </span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FLIGHTS & STAY */}
          {activeTab === 'flights_stay' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                      Flights & Accommodations
                    </h2>
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Live SerpApi Connected
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Real-time flight schedules and verified lodging rates for {trip.destination}.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => generatePlan(trip)}
                  disabled={optimizing}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 disabled:opacity-60 transition-colors self-start sm:self-auto cursor-pointer dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  <RefreshCw size={13} className={optimizing ? 'animate-spin text-blue-600' : 'text-slate-500 dark:text-slate-400'} />
                  <span>{optimizing ? 'Fetching Live Rates…' : 'Refresh Live Rates'}</span>
                </button>
              </div>

              {optimizing && !itinerary && (
                <div className="rounded-2xl border border-blue-200/60 bg-blue-50/50 dark:border-blue-900/50 dark:bg-blue-950/30 p-6 text-center animate-pulse">
                  <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/60 text-blue-600 dark:text-blue-300 mb-3">
                    <Plane size={20} className="animate-bounce" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Querying Real-Time Travel APIs…
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
                    Retrieving live flight routes via Google Flights and real-time hotel pricing via Google Hotels for {trip.destination}.
                  </p>
                </div>
              )}

              {/* Live Flights, Trains & Hotels Data */}
              {(() => {
                const liveFlights = Array.isArray(itinerary?.transport?.flights) ? itinerary.transport.flights : []
                const liveTrains = Array.isArray(trainsList) && trainsList.length > 0
                  ? trainsList
                  : (Array.isArray(itinerary?.transport?.trains) ? itinerary.transport.trains : [])
                const liveHotels = Array.isArray(itinerary?.hotels) ? itinerary.hotels : []
                const guidelines = Array.isArray(itinerary?.transport?.guidelines) ? itinerary.transport.guidelines : []
                const recommendedMode = itinerary?.transport?.recommended_mode || (isDomesticIndia ? 'Train' : 'Flight')
                const nearbyTransit = itinerary?.transport?.nearby_transit || null

                return (
                  <div className="space-y-6">
                    {/* Nearby Transit Gateways Banner (When destination has no direct commercial airport) */}
                    {nearbyTransit && !nearbyTransit.has_direct_airport && (
                      <div className="rounded-2xl border border-blue-200/90 bg-gradient-to-r from-blue-50/90 via-indigo-50/60 to-white dark:border-blue-900/60 dark:from-blue-950/40 dark:via-slate-900 dark:to-slate-900 p-4 shadow-xs">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-3">
                          <div className="flex items-center gap-2">
                            <div className="h-7 w-7 rounded-lg bg-blue-100 dark:bg-blue-900/60 text-blue-600 dark:text-blue-300 flex items-center justify-center font-bold shrink-0">
                              <Navigation size={14} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-bold text-slate-900 dark:text-white">
                                  Transit Gateway for {nearbyTransit.destination_name || trip.destination}
                                </span>
                                <span className="rounded-full bg-amber-100 dark:bg-amber-950/70 border border-amber-300 dark:border-amber-700 px-2 py-0.2 text-[9px] font-bold text-amber-800 dark:text-amber-300">
                                  No Direct Commercial Airport
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                                {nearbyTransit.notice || `${trip.destination} has no commercial airport. Travel via the nearest airport or railway gateway.`}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid sm:grid-cols-2 gap-3 pt-1">
                          {/* Nearby Airport Card */}
                          {nearbyTransit.nearby_airport && (
                            <div className="rounded-xl border border-blue-100/90 bg-white/90 dark:border-slate-800 dark:bg-slate-800/80 p-3 flex flex-col justify-between">
                              <div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center gap-1">
                                    <Plane size={11} /> Nearest Airport
                                  </span>
                                  <span className="rounded bg-blue-100 dark:bg-blue-900/60 px-1.5 py-0.2 font-mono text-[10px] font-bold text-blue-800 dark:text-blue-300">
                                    {nearbyTransit.nearby_airport.code}
                                  </span>
                                </div>
                                <p className="text-xs font-bold text-slate-900 dark:text-white">
                                  {nearbyTransit.nearby_airport.name}
                                </p>
                                <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-0.5">
                                  Distance: <strong className="text-slate-700 dark:text-slate-300">{nearbyTransit.nearby_airport.distance}</strong>
                                </p>
                                {nearbyTransit.nearby_airport.transfer_tip && (
                                  <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 line-clamp-2">
                                    Transfer: {nearbyTransit.nearby_airport.transfer_tip}
                                  </p>
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => setTransportTab('flights')}
                                className="mt-2.5 flex items-center justify-center gap-1 rounded-lg bg-blue-50 dark:bg-blue-950/60 py-1 text-[11px] font-semibold text-blue-600 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/60 transition-colors"
                              >
                                <span>View Flights to {nearbyTransit.nearby_airport.code}</span>
                                <ExternalLink size={10} />
                              </button>
                            </div>
                          )}

                          {/* Nearby Railway Station Card */}
                          {nearbyTransit.nearby_railway && (
                            <div className="rounded-xl border border-emerald-100/90 bg-white/90 dark:border-slate-800 dark:bg-slate-800/80 p-3 flex flex-col justify-between">
                              <div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                                    <Train size={11} /> Nearest Railway Station
                                  </span>
                                  <span className="rounded bg-emerald-100 dark:bg-emerald-900/60 px-1.5 py-0.2 font-mono text-[10px] font-bold text-emerald-800 dark:text-emerald-300">
                                    {nearbyTransit.nearby_railway.code}
                                  </span>
                                </div>
                                <p className="text-xs font-bold text-slate-900 dark:text-white">
                                  {nearbyTransit.nearby_railway.name}
                                </p>
                                <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-0.5">
                                  Distance: <strong className="text-slate-700 dark:text-slate-300">{nearbyTransit.nearby_railway.distance}</strong>
                                </p>
                                {nearbyTransit.nearby_railway.transfer_tip && (
                                  <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 line-clamp-2">
                                    Transfer: {nearbyTransit.nearby_railway.transfer_tip}
                                  </p>
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => {
                                  setTransportTab('trains')
                                  if (nearbyTransit.nearby_railway.name) {
                                    setTrainTo(nearbyTransit.nearby_railway.name)
                                  }
                                }}
                                className="mt-2.5 flex items-center justify-center gap-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 py-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition-colors"
                              >
                                <span>Search Trains to {nearbyTransit.nearby_railway.code}</span>
                                <Train size={10} />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="grid gap-6 lg:grid-cols-2">
                    {/* Transport Card (Flights & Trains sub-tabs - NO Bus tab) */}
                    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900">
                      <div>
                        {/* Transport Mode Switcher: Flights vs Trains */}
                        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200/80 dark:border-slate-700">
                              <button
                                type="button"
                                onClick={() => setTransportTab('flights')}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                  transportTab === 'flights'
                                    ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-300 shadow-xs'
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
                                }`}
                              >
                                <Plane size={13} />
                                <span>Flights</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setTransportTab('trains')}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                  transportTab === 'trains'
                                    ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-300 shadow-xs'
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
                                }`}
                              >
                                <Train size={13} />
                                <span>Trains</span>
                              </button>
                            </div>
                            {recommendedMode && (
                              <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-violet-100 dark:bg-violet-950/70 border border-violet-300 dark:border-violet-700 px-2 py-0.5 text-[10px] font-bold text-violet-800 dark:text-violet-300">
                                Best: {recommendedMode}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* SUB-TAB 1: FLIGHTS */}
                        {transportTab === 'flights' && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                                Available Flight Schedules
                              </span>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => {
                                    sessionStorage.removeItem(`itinerary_trip_${id}`)
                                    if (trip) generatePlan(trip)
                                  }}
                                  disabled={optimizing}
                                  className="flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors shadow-2xs"
                                  title="Force live refresh of flight routes and fares"
                                >
                                  <RefreshCw size={11} className={optimizing ? 'animate-spin text-blue-600' : ''} />
                                  <span>{optimizing ? 'Updating…' : 'Refresh Live Flights'}</span>
                                </button>
                                {liveFlights.length > 0 && (
                                  liveFlights.some((f) => f.is_live) ? (
                                    <span className="rounded-full bg-emerald-100 dark:bg-emerald-950/70 border border-emerald-300 dark:border-emerald-750 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:text-emerald-300">
                                      Confirmed Live Inventory
                                    </span>
                                  ) : (
                                    <span className="rounded-full bg-amber-100 dark:bg-amber-950/70 border border-amber-300 dark:border-amber-700 px-2 py-0.5 text-[10px] font-bold text-amber-800 dark:text-amber-300">
                                      Estimated Market Guidance
                                    </span>
                                  )
                                )}
                              </div>
                            </div>

                            {liveFlights.length > 0 ? (
                              <div className="space-y-3">
                                {liveFlights.map((f, idx) => (
                                  <div
                                    key={idx}
                                    className="rounded-xl border border-slate-200/90 bg-slate-50/50 p-4 transition-all hover:border-blue-300 hover:bg-white hover:shadow-xs dark:border-slate-700/60 dark:bg-slate-800/60 dark:hover:border-blue-500/50 dark:hover:bg-slate-800"
                                  >
                                    <div className="flex items-center justify-between mb-2.5">
                                      <div className="flex items-center gap-2">
                                        {f.airline_logo ? (
                                          <img
                                            src={f.airline_logo}
                                            alt={f.airline}
                                            referrerPolicy="no-referrer"
                                            onError={(e) => {
                                              e.currentTarget.style.display = 'none'
                                            }}
                                            className="h-6 w-6 object-contain rounded"
                                          />
                                        ) : (
                                          <div className="h-6 w-6 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-600 dark:text-blue-300 flex items-center justify-center font-bold text-[10px]">
                                            ✈
                                          </div>
                                        )}
                                        <div>
                                          <div className="flex items-center gap-1.5">
                                            <span className="font-bold text-xs text-slate-900 dark:text-white">
                                              {f.airline}
                                            </span>
                                            {f.is_live ? (
                                              <span className="rounded bg-emerald-100 dark:bg-emerald-950/80 px-1.5 py-0.2 text-[9px] font-bold text-emerald-800 dark:text-emerald-300">
                                                Live Fares
                                              </span>
                                            ) : (
                                              <span className="rounded bg-amber-100 dark:bg-amber-950/80 px-1.5 py-0.2 text-[9px] font-bold text-amber-800 dark:text-amber-300">
                                                Est. Guidance
                                              </span>
                                            )}
                                          </div>
                                          {f.flight_number && (
                                            <span className="text-[10px] text-slate-400 font-mono">
                                              {f.flight_number}
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                      <span className="text-sm font-extrabold text-blue-700 dark:text-blue-400">
                                        {f.price}
                                      </span>
                                    </div>

                                    <div className="flex items-center justify-between py-1 text-xs">
                                      <div>
                                        <p className="font-bold text-slate-800 dark:text-slate-200">
                                          {f.departure_time?.split(' ')[1] || f.departure_time || 'Dep'}
                                        </p>
                                        <p className="text-[10px] text-slate-400 truncate max-w-[90px]">
                                          {f.departure_code || 'Origin'}
                                        </p>
                                      </div>

                                      <div className="flex flex-col items-center px-2">
                                        <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                                          {f.duration}
                                        </span>
                                        <div className="w-16 h-px bg-slate-300 dark:bg-slate-700 relative my-1">
                                          <span className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400" />
                                        </div>
                                        <span className="text-[9px] font-semibold text-emerald-600 dark:text-emerald-400">
                                          {f.stops || 'Nonstop'}
                                        </span>
                                      </div>

                                      <div className="text-right">
                                        <p className="font-bold text-slate-800 dark:text-slate-200">
                                          {f.arrival_time?.split(' ')[1] || f.arrival_time || 'Arr'}
                                        </p>
                                        <p className="text-[10px] text-slate-400 truncate max-w-[90px]">
                                          {f.arrival_code || 'Dest'}
                                        </p>
                                      </div>
                                    </div>

                                    {f.booking_link && (
                                      <a
                                        href={f.booking_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-3 flex items-center justify-center gap-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 py-1.5 text-[11px] font-semibold text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/60 transition-colors"
                                      >
                                        <span>View on Google Flights</span>
                                        <ExternalLink size={12} />
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 p-3.5 border border-slate-100 dark:border-slate-700">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold text-slate-800 dark:text-slate-200">Travel Window:</span>
                                    <span className="font-bold text-violet-600 dark:text-violet-400">
                                      {trip.start_date} – {trip.end_date}
                                    </span>
                                  </div>
                                  <p className="text-slate-500 dark:text-slate-400">
                                    Aim for Tuesday or Wednesday departures to save an estimated 15–20% on round-trip fares.
                                  </p>
                                </div>
                              </div>
                            )}

                            {guidelines.length > 0 && (
                              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-1.5">
                                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 block">Flight Guidelines:</span>
                                {guidelines.map((g, i) => (
                                  <p key={i} className="text-[11px] text-slate-500 dark:text-slate-400 flex items-start gap-1.5">
                                    <span className="text-blue-500 mt-0.5">•</span>
                                    <span>{g}</span>
                                  </p>
                                ))}
                              </div>
                            )}

                            <div className="pt-2">
                              <button
                                type="button"
                                onClick={() =>
                                  window.open(
                                    `https://www.google.com/travel/flights?q=flights+to+${encodeURIComponent(
                                      trip.destination
                                    )}`,
                                    '_blank'
                                  )
                                }
                                className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 text-white py-2.5 text-xs font-semibold hover:bg-blue-700 transition-colors shadow-xs"
                              >
                                <Plane size={14} /> Search More Flights on Google
                              </button>
                            </div>
                          </div>
                        )}

                        {/* SUB-TAB 2: TRAINS (RailCore API Integrated) */}
                        {transportTab === 'trains' && (
                          <div className="space-y-4">
                            {/* International Destination Warning Banner */}
                            {!isDomesticIndia && (
                              <div className="rounded-xl border border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/40 p-4 text-xs space-y-2">
                                <div className="flex items-center gap-2 font-bold text-amber-900 dark:text-amber-200">
                                  <AlertCircle size={16} className="text-amber-600 dark:text-amber-400 shrink-0" />
                                  <span>International Destination — Rail Transit Not Applicable</span>
                                </div>
                                <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
                                  <strong>{trip.destination}</strong> is an international destination with no overland Indian Railway link from {trip.preferences?.origin || trip.origin || 'India'}. Indian Railways (IRCTC via RailCore) operates domestic railway routes within India. Please check the Flights tab for flights to {trip.destination}.
                                </p>
                                <div className="pt-1">
                                  <button
                                    type="button"
                                    onClick={() => setTransportTab('flights')}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-xs"
                                  >
                                    <Plane size={13} /> Switch to Flights Tab
                                  </button>
                                </div>
                              </div>
                            )}

                            {/* Train Search Controls */}
                            <form onSubmit={handleSearchTrains} className="rounded-xl border border-slate-200/90 bg-slate-50/60 dark:border-slate-700/60 dark:bg-slate-800/40 p-3 space-y-2.5">
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                <div>
                                  <label className="block text-[10px] font-bold uppercase text-slate-500 dark:text-slate-400 mb-1">
                                    From Station / City
                                  </label>
                                  <input
                                    type="text"
                                    value={trainFrom}
                                    onChange={(e) => setTrainFrom(e.target.value)}
                                    placeholder="e.g. Bangalore, SBC, Mumbai"
                                    className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-blue-500"
                                  />
                                </div>
                                <div>
                                  <label className="block text-[10px] font-bold uppercase text-slate-500 dark:text-slate-400 mb-1">
                                    To Station / City
                                  </label>
                                  <input
                                    type="text"
                                    value={trainTo}
                                    onChange={(e) => setTrainTo(e.target.value)}
                                    placeholder="e.g. Goa, MAO, Jaipur"
                                    className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-blue-500"
                                  />
                                </div>
                              </div>

                              <div className="flex items-center gap-2">
                                <div className="flex-1">
                                  <input
                                    type="date"
                                    min={new Date().toISOString().slice(0, 10)}
                                    value={trainDate}
                                    onChange={(e) => setTrainDate(e.target.value)}
                                    className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-blue-500"
                                  />
                                </div>
                                <button
                                  type="submit"
                                  disabled={trainsLoading}
                                  className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-xs disabled:opacity-50"
                                >
                                  {trainsLoading ? <RefreshCw size={12} className="animate-spin" /> : <Train size={12} />}
                                  <span>{trainsLoading ? 'Searching…' : 'Find Trains'}</span>
                                </button>
                              </div>

                              {trainsError && (
                                <p className="text-[11px] text-rose-600 dark:text-rose-400 font-medium">
                                  {trainsError}
                                </p>
                              )}
                            </form>

                            {/* Train Results */}
                            {liveTrains.length > 0 ? (
                              <div className="space-y-3">
                                {liveTrains.map((t, idx) => (
                                  <div
                                    key={idx}
                                    className="rounded-xl border border-slate-200/90 bg-slate-50/50 p-4 transition-all hover:border-blue-300 hover:bg-white hover:shadow-xs dark:border-slate-700/60 dark:bg-slate-800/60 dark:hover:border-blue-500/50 dark:hover:bg-slate-800 space-y-2.5"
                                  >
                                    <div className="flex items-center justify-between">
                                      <div>
                                        <div className="flex items-center gap-2">
                                          <span className="font-bold text-xs text-slate-900 dark:text-white">
                                            {t.train_name}
                                          </span>
                                          <span className="rounded bg-blue-100 dark:bg-blue-950/80 px-1.5 py-0.2 text-[9px] font-bold text-blue-800 dark:text-blue-300 font-mono">
                                            #{t.train_number}
                                          </span>
                                        </div>
                                        <p className="text-[10px] text-slate-400">
                                          {t.from_station} → {t.to_station}
                                        </p>
                                      </div>
                                      {t.lowest_fare && (
                                        <span className="text-sm font-extrabold text-blue-700 dark:text-blue-400">
                                          from {t.lowest_fare}
                                        </span>
                                      )}
                                    </div>

                                    {/* Departure - Duration - Arrival */}
                                    <div className="flex items-center justify-between text-xs py-1">
                                      <div>
                                        <p className="font-bold text-slate-800 dark:text-slate-200">
                                          {t.departure_time}
                                        </p>
                                        <p className="text-[10px] text-slate-400 truncate max-w-[80px]">
                                          {t.from_station}
                                        </p>
                                      </div>

                                      <div className="flex flex-col items-center px-2">
                                        <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                                          {t.duration}
                                        </span>
                                        <div className="w-16 h-px bg-slate-300 dark:bg-slate-700 relative my-1">
                                          <span className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400" />
                                        </div>
                                        <span className="text-[9px] font-semibold text-emerald-600 dark:text-emerald-400">
                                          Direct Rail Link
                                        </span>
                                      </div>

                                      <div className="text-right">
                                        <p className="font-bold text-slate-800 dark:text-slate-200">
                                          {t.arrival_time}
                                        </p>
                                        <p className="text-[10px] text-slate-400 truncate max-w-[80px]">
                                          {t.to_station}
                                        </p>
                                      </div>
                                    </div>

                                    {/* Classes & Fares Badges */}
                                    {Array.isArray(t.classes) && t.classes.length > 0 && (
                                      <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-100 dark:border-slate-750">
                                        {t.classes.map((cls, ci) => (
                                          <div
                                            key={ci}
                                            className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-2 py-0.5 text-[10px]"
                                          >
                                            <span className="font-bold text-slate-800 dark:text-slate-200">
                                              {cls.class_code}:
                                            </span>
                                            <span className="text-blue-600 dark:text-blue-400 font-medium">
                                              {cls.fare}
                                            </span>
                                            {cls.availability && (
                                              <span className="text-[9px] text-emerald-600 dark:text-emerald-400 font-semibold">
                                                · {cls.availability}
                                              </span>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Booking Link */}
                                    <a
                                      href={t.booking_link || 'https://www.irctc.co.in/nget/train-search'}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="mt-2 flex items-center justify-center gap-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 py-1.5 text-[11px] font-semibold text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/60 transition-colors"
                                    >
                                      <span>Book on IRCTC (Official Portal)</span>
                                      <ExternalLink size={12} />
                                    </a>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 p-4 border border-slate-100 dark:border-slate-700 text-center text-xs text-slate-500 dark:text-slate-400">
                                <Train size={24} className="mx-auto text-slate-400 mb-2" />
                                <p className="font-semibold text-slate-700 dark:text-slate-200">
                                  RailCore Railway Service Connected
                                </p>
                                <p className="mt-1">
                                  Click "Find Trains" above to query real-time Indian Railways schedules and IRCTC fares.
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Stays & Accommodations Card */}
                    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                          <div className="flex items-center gap-2.5">
                            <div className="h-8 w-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                              <Hotel size={17} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="text-base font-bold text-slate-900 dark:text-white">Recommended Stays</h3>
                                {liveHotels.length > 0 && (
                                  liveHotels.some((h) => h.is_live) ? (
                                    <span className="rounded-full bg-emerald-100 dark:bg-emerald-950/70 border border-emerald-300 dark:border-emerald-700 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:text-emerald-300">
                                      Confirmed Live Inventory
                                    </span>
                                  ) : (
                                    <span className="rounded-full bg-amber-100 dark:bg-amber-950/70 border border-amber-300 dark:border-amber-700 px-2 py-0.5 text-[10px] font-bold text-amber-800 dark:text-amber-300">
                                      Estimated Market Guidance
                                    </span>
                                  )
                                )}
                              </div>
                              <p className="text-[11px] text-slate-400">
                                Real hotels & lodges in {trip.destination}
                              </p>
                            </div>
                          </div>
                        </div>

                        {liveHotels.length > 0 ? (
                          <div className="space-y-3">
                            {liveHotels.map((h, idx) => (
                              <div
                                key={idx}
                                className="flex flex-col sm:flex-row gap-3.5 rounded-xl border border-slate-200/90 bg-slate-50/50 p-3.5 transition-all hover:border-emerald-300 hover:bg-white hover:shadow-xs dark:border-slate-700/60 dark:bg-slate-800/60 dark:hover:border-emerald-500/50 dark:hover:bg-slate-800"
                              >
                                {h.thumbnail && (
                                  <img
                                    src={h.thumbnail}
                                    alt={h.name}
                                    referrerPolicy="no-referrer"
                                    onError={(e) => {
                                      e.currentTarget.onerror = null
                                      e.currentTarget.src = resolveImageUrl('/images/hero.jpg')
                                    }}
                                    className="h-24 w-full sm:w-28 rounded-lg object-cover shrink-0"
                                  />
                                )}
                                <div className="flex-1 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex flex-col gap-0.5">
                                        <div className="flex items-center gap-1.5 flex-wrap">
                                          <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-snug">
                                            {h.name}
                                          </h4>
                                          {h.is_live ? (
                                            <span className="rounded bg-emerald-100 dark:bg-emerald-950/80 px-1.5 py-0.2 text-[9px] font-bold text-emerald-800 dark:text-emerald-300">
                                              Live Rates
                                            </span>
                                          ) : (
                                            <span className="rounded bg-amber-100 dark:bg-amber-950/80 px-1.5 py-0.2 text-[9px] font-bold text-amber-800 dark:text-amber-300">
                                              Est. Guidance
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                      <span className="text-xs font-extrabold text-emerald-600 dark:text-emerald-400 shrink-0">
                                        {h.price_per_night}
                                      </span>
                                    </div>

                                    {h.rating && (
                                      <div className="flex items-center gap-1.5 mt-1">
                                        <div className="flex items-center gap-0.5 text-amber-500">
                                          <Star size={11} className="fill-amber-500" />
                                          <span className="text-[11px] font-bold text-slate-800 dark:text-slate-200">
                                            {Number(h.rating).toFixed(1)}
                                          </span>
                                        </div>
                                        {h.reviews_count > 0 && (
                                          <span className="text-[10px] text-slate-400">
                                            ({h.reviews_count} reviews)
                                          </span>
                                        )}
                                      </div>
                                    )}

                                    {h.amenities && h.amenities.length > 0 && (
                                      <div className="flex flex-wrap gap-1 mt-2">
                                        {h.amenities.slice(0, 3).map((a, i) => (
                                          <span
                                            key={i}
                                            className="rounded-md bg-white dark:bg-slate-700 px-1.5 py-0.5 text-[9px] font-medium text-slate-600 dark:text-slate-200 border border-slate-200/70 dark:border-slate-600"
                                          >
                                            {a}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {h.link && (
                                    <div className="pt-2.5">
                                      <a
                                        href={h.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300"
                                      >
                                        <span>View Hotel on Google</span>
                                        <ExternalLink size={11} />
                                      </a>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="rounded-xl border border-slate-100 dark:border-slate-700/60 dark:bg-slate-800/60 p-3.5 hover:border-violet-200 transition-colors">
                              <div className="flex items-center justify-between">
                                <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                                  Central Boutique Hotel & Suites
                                </h4>
                                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                                  ~${Math.round((trip.budget * 0.35) / duration.nights || 120)}/nt
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                                Conveniently situated near major sights with complimentary breakfast, high-speed Wi-Fi, and terrace views.
                              </p>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="pt-4 mt-4 border-t border-slate-100 dark:border-slate-800">
                        <button
                          type="button"
                          onClick={() =>
                            window.open(
                              `https://www.google.com/travel/hotels?q=hotels+in+${encodeURIComponent(
                                trip.destination
                              )}`,
                              '_blank'
                            )
                          }
                          className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 text-white py-2.5 text-xs font-semibold hover:bg-emerald-700 transition-colors shadow-xs"
                        >
                          <Hotel size={14} /> Search More Hotels in {trip.destination}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
              })()}
            </div>
          )}

          {/* TAB 6: BUDGET */}
          {activeTab === 'budget' && (() => {
            const bb = itinerary?.budget_breakdown || {}
            const targetBudget = bb.target_budget || trip.budget || 0
            const totalCost = bb.total || trip.budget || 0
            const bCurr = (bb.currency || tripCurrency || 'USD').toUpperCase()
            const exceeds = bb.exceeds_budget || (totalCost > targetBudget && targetBudget > 0)
            const variance = Math.abs(bb.budget_variance || totalCost - targetBudget)
            const remaining = bb.remaining_budget ?? Math.max(0, targetBudget - totalCost)
            const utilization = bb.utilization_percent ?? (targetBudget > 0 ? Math.min(100, Math.round((totalCost / targetBudget) * 100)) : 100)
            const feasibility = bb.feasibility || {}

            const flightsCost = bb.flights || Math.round(targetBudget * 0.25)
            const stayCost = bb.stay || Math.round(targetBudget * 0.35)
            const foodCost = bb.food || Math.round(targetBudget * 0.20)
            const actCost = bb.activities || Math.round(targetBudget * 0.12)
            const transitCost = bb.local_transit || Math.round(targetBudget * 0.05)
            const miscCost = bb.miscellaneous || Math.max(0, totalCost - flightsCost - stayCost - foodCost - actCost - transitCost)

            const flightsPct = totalCost > 0 ? Math.round((flightsCost / totalCost) * 100) : 25
            const stayPct = totalCost > 0 ? Math.round((stayCost / totalCost) * 100) : 35
            const foodPct = totalCost > 0 ? Math.round((foodCost / totalCost) * 100) : 20
            const actPct = totalCost > 0 ? Math.round((actCost / totalCost) * 100) : 12
            const transitPct = totalCost > 0 ? Math.round((transitCost / totalCost) * 100) : 5
            const miscPct = Math.max(1, 100 - flightsPct - stayPct - foodPct - actPct - transitPct)

            return (
              <div className="space-y-6 animate-fade-in">
                {/* Top Header & Key Metrics */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                      Financial & Budget Breakdown
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Strictly constrained bottom-up itemized cost breakdown across {duration.days} days and {trip.travelers || 1} traveler(s).
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
                    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs">
                      <span className="text-slate-500 dark:text-slate-400">Target Budget: </span>
                      <span className="font-bold text-slate-900 dark:text-white">{formatCurrency(targetBudget, bCurr)}</span>
                    </div>
                    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs">
                      <span className="text-slate-500 dark:text-slate-400">Estimated Total: </span>
                      <span className={`font-bold ${exceeds ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                        {formatCurrency(totalCost, bCurr)}
                      </span>
                    </div>
                    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs">
                      <span className="text-slate-500 dark:text-slate-400">{exceeds ? 'Overage: ' : 'Remaining: '}</span>
                      <span className={`font-bold ${exceeds ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                        {formatCurrency(exceeds ? variance : remaining, bCurr)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Budget Utilization Progress Bar */}
                <div className="rounded-2xl border border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900 p-4 shadow-xs">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      Budget Utilization Progress
                    </span>
                    <span className={`font-bold ${exceeds ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {utilization}% utilized {exceeds ? '(Exceeds Target)' : '(Within Target Budget)'}
                    </span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      style={{ width: `${Math.min(100, utilization)}%` }}
                      className={`h-full transition-all duration-500 ${
                        exceeds ? 'bg-gradient-to-r from-amber-500 to-rose-500' : 'bg-gradient-to-r from-emerald-500 to-teal-500'
                      }`}
                    />
                  </div>
                </div>

                {/* Budget Health / Feasibility Banner */}
                {exceeds ? (
                  <div className="rounded-2xl border border-amber-300 bg-amber-50/80 p-5 dark:border-amber-700/60 dark:bg-amber-950/40 space-y-3">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                      <div className="text-xs space-y-2">
                        <p className="font-bold text-amber-900 dark:text-amber-200 text-sm">
                          Estimated Total ({formatCurrency(totalCost, bCurr)}) Exceeds Target Budget by {formatCurrency(variance, bCurr)}
                        </p>
                        <p className="text-amber-800/90 dark:text-amber-300 leading-relaxed">
                          {feasibility.unrealistic_reason || 
                            'Bottom-up costs for realistic transportation, accommodations, and dining surpass your initial budget target. Review the suggested adjustments below.'}
                        </p>

                        {Array.isArray(feasibility.cost_contributors) && feasibility.cost_contributors.length > 0 && (
                          <div className="pt-2">
                            <span className="font-bold text-amber-950 dark:text-amber-200 block mb-1">
                              Major Cost Drivers:
                            </span>
                            <ul className="list-disc list-inside space-y-0.5 text-amber-900 dark:text-amber-300">
                              {feasibility.cost_contributors.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {Array.isArray(feasibility.suggested_alternatives) && feasibility.suggested_alternatives.length > 0 && (
                          <div className="pt-2">
                            <span className="font-bold text-amber-950 dark:text-amber-200 block mb-1">
                              Suggested Realistic Alternatives:
                            </span>
                            <ul className="list-disc list-inside space-y-0.5 text-amber-900 dark:text-amber-300">
                              {feasibility.suggested_alternatives.map((alt, i) => (
                                <li key={i}>{alt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {feasibility.suggested_revised_budget && (
                          <div className="pt-2">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-200/80 dark:bg-amber-900/60 text-amber-950 dark:text-amber-200 font-bold">
                              Suggested Revised Budget: {formatCurrency(feasibility.suggested_revised_budget, bCurr)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-emerald-300 bg-emerald-50/80 p-5 dark:border-emerald-700/60 dark:bg-emerald-950/40">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <div className="text-xs space-y-1">
                        <p className="font-bold text-emerald-900 dark:text-emerald-200 text-sm">
                          Budget Balanced & Strictly Constrained ({formatCurrency(totalCost, bCurr)} of {formatCurrency(targetBudget, bCurr)} target)
                        </p>
                        <p className="text-emerald-800/90 dark:text-emerald-300 leading-relaxed">
                          Trip generation strictly respected your budget as the primary constraint. All transportation ({bb.transport_mode || 'flights'}), accommodations, meals, and curated sights fit comfortably within your allocated budget, leaving a healthy buffer of {formatCurrency(remaining, bCurr)} for unexpected experiences.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 6 Budget Category Cards Grid */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {/* Card 1: Flights / Intercity */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                        {bb.transport_mode === 'Train' ? 'Railway Transport' : 'Flights / Intercity'}
                      </span>
                      {bb.transport_mode === 'Train' ? (
                        <Train size={16} className="text-blue-500" />
                      ) : (
                        <Plane size={16} className="text-blue-500" />
                      )}
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(flightsCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{flightsPct}% of estimated total</span>
                      <span>{trip.travelers || 1} traveler{(trip.travelers || 1) > 1 ? 's' : ''}</span>
                    </div>
                  </div>

                  {/* Card 2: Lodging / Stay */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Accommodation</span>
                      <Hotel size={16} className="text-violet-500" />
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(stayCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{stayPct}% · {duration.nights} night{duration.nights > 1 ? 's' : ''} total</span>
                      <span className="font-semibold text-violet-600 dark:text-violet-400">
                        ~{formatCurrency(Math.round(stayCost / Math.max(1, duration.nights)), bCurr)}/night
                      </span>
                    </div>
                  </div>

                  {/* Card 3: Food & Dining */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Food & Dining</span>
                      <Utensils size={16} className="text-amber-500" />
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(foodCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{foodPct}% · {duration.days} day{duration.days > 1 ? 's' : ''} total</span>
                      <span className="font-semibold text-amber-600 dark:text-amber-400">
                        ~{formatCurrency(Math.round(foodCost / Math.max(1, duration.days)), bCurr)}/day
                      </span>
                    </div>
                  </div>

                  {/* Card 4: Activities & Tours */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Activities & Attractions</span>
                      <Activity size={16} className="text-emerald-500" />
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(actCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{actPct}% · {duration.days} day{duration.days > 1 ? 's' : ''} total</span>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        ~{formatCurrency(Math.round(actCost / Math.max(1, duration.days)), bCurr)}/day
                      </span>
                    </div>
                  </div>

                  {/* Card 5: Local Transit */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Local Transit & Commuting</span>
                      <Compass size={16} className="text-teal-500" />
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(transitCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{transitPct}% · {duration.days} day{duration.days > 1 ? 's' : ''} total</span>
                      <span className="font-semibold text-teal-600 dark:text-teal-400">
                        ~{formatCurrency(Math.round(transitCost / Math.max(1, duration.days)), bCurr)}/day
                      </span>
                    </div>
                  </div>

                  {/* Card 6: Contingency */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Miscellaneous Buffer</span>
                      <Shield size={16} className="text-rose-500" />
                    </div>
                    <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                      {formatCurrency(miscCost, bCurr)}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span>{miscPct}% · {duration.days} day{duration.days > 1 ? 's' : ''} total</span>
                      <span className="font-semibold text-rose-600 dark:text-rose-400">
                        ~{formatCurrency(Math.round(miscCost / Math.max(1, duration.days)), bCurr)}/day
                      </span>
                    </div>
                  </div>
                </div>

                {/* Visual Multi-Segment Bar */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400">
                      Budget Distribution Bar
                    </h3>
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                      Total Sum: {formatCurrency(totalCost, bCurr)}
                    </span>
                  </div>
                  <div className="h-4 w-full overflow-hidden rounded-full flex bg-slate-100 dark:bg-slate-800">
                    <div style={{ width: `${flightsPct}%` }} className="bg-blue-500" title={`Transport ${flightsPct}%`} />
                    <div style={{ width: `${stayPct}%` }} className="bg-violet-500" title={`Stay ${stayPct}%`} />
                    <div style={{ width: `${foodPct}%` }} className="bg-amber-500" title={`Food ${foodPct}%`} />
                    <div style={{ width: `${actPct}%` }} className="bg-emerald-500" title={`Activities ${actPct}%`} />
                    <div style={{ width: `${transitPct}%` }} className="bg-teal-500" title={`Local Transit ${transitPct}%`} />
                    <div style={{ width: `${miscPct}%` }} className="bg-rose-500" title={`Miscellaneous ${miscPct}%`} />
                  </div>

                  <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-blue-500 shrink-0" />
                      <span className="truncate">Transport ({flightsPct}%)</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-violet-500 shrink-0" />
                      <span className="truncate">Stay ({stayPct}%)</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-amber-500 shrink-0" />
                      <span className="truncate">Food ({foodPct}%)</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 shrink-0" />
                      <span className="truncate">Activities ({actPct}%)</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-teal-500 shrink-0" />
                      <span className="truncate">Transit ({transitPct}%)</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      <div className="h-2.5 w-2.5 rounded-full bg-rose-500 shrink-0" />
                      <span className="truncate">Buffer ({miscPct}%)</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })()}

          {activeTab === 'trippulse' && (
            <TripPulseTab
              trip={trip}
              onTripUpdated={fetchTrip}
            />
          )}
        </div>

        {replaceTarget && (
          <ReplaceAttractionModal
            tripId={trip.id}
            dayNumber={replaceTarget.dayNumber}
            activity={replaceTarget.activity}
            onClose={() => setReplaceTarget(null)}
            onReplaced={(updatedItinerary) => {
              if (updatedItinerary) {
                setItinerary(updatedItinerary)
                try {
                  sessionStorage.setItem(`itinerary_trip_${id}`, JSON.stringify(updatedItinerary))
                } catch (e) {}
              }
            }}
          />
        )}

        {isEditing && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs animate-fade-in">
            <div className="w-full max-w-xl rounded-2xl bg-white dark:bg-slate-900 p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-violet-50 dark:bg-violet-950/60 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                    <Edit3 size={16} />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">Edit Trip Details</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSaveEdit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Destination
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.destination}
                    onChange={(e) =>
                      setEditForm((prev) => ({ ...prev, destination: e.target.value }))
                    }
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-3.5 py-2 text-sm text-slate-800 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                    placeholder="e.g. Bali, Paris, Tokyo"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      required
                      min={getTodayDateStr()}
                      value={editForm.start_date}
                      onChange={(e) => {
                        const newStart = e.target.value
                        setEditForm((prev) => {
                          const nextEnd =
                            newStart && (!prev.end_date || prev.end_date <= newStart)
                              ? getNextDayDateStr(newStart)
                              : prev.end_date
                          return { ...prev, start_date: newStart, end_date: nextEnd }
                        })
                      }}
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      required
                      min={editForm.start_date ? getNextDayDateStr(editForm.start_date) : getNextDayDateStr(getTodayDateStr())}
                      value={editForm.end_date}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, end_date: e.target.value }))
                      }
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Travelers
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={15}
                      value={editForm.travelers}
                      onChange={(e) =>
                        setEditForm((prev) => ({
                          ...prev,
                          travelers: Math.min(15, Math.max(1, parseInt(e.target.value) || 1)),
                        }))
                      }
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Currency
                    </label>
                    <select
                      value={editForm.currency || 'USD'}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, currency: e.target.value }))
                      }
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-2 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    >
                      {currencyOptions.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.code} ({c.symbol})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Budget ({getCurrencySymbol(editForm.currency || 'USD')})
                    </label>
                    <input
                      type="number"
                      min={0}
                      step={50}
                      value={editForm.budget}
                      onChange={(e) =>
                        setEditForm((prev) => ({
                          ...prev,
                          budget: Math.max(0, parseInt(e.target.value) || 0),
                        }))
                      }
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                {/* Preferences Selector Chips */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    Travel Interests & Preferences
                  </label>
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1 border border-slate-100 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/50">
                    {INTERESTS.map((int) => {
                      const selected = (editForm.interests || []).some(
                        (i) => i.toLowerCase() === int.name.toLowerCase()
                      )
                      return (
                        <button
                          key={int.name}
                          type="button"
                          onClick={() => toggleInterest(int.name)}
                          className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                            selected
                              ? 'bg-violet-600 text-white shadow-xs'
                              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700'
                          }`}
                        >
                          {int.icon} {int.name}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {editError && (
                  <p className="text-xs text-rose-600 font-medium">{editError}</p>
                )}
                {saveSuccess && (
                  <p className="text-xs text-emerald-600 font-medium">✓ Changes saved successfully!</p>
                )}

                <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingEdit}
                    className="rounded-xl bg-violet-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-violet-700 disabled:opacity-50"
                  >
                    {savingEdit ? 'Saving…' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
