import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './layout.jsx'
import Login from './login.jsx'
import Signup from './signup.jsx'
import Dashboard from './dashboard.jsx'
import CompleteProfile from './complete-profile.jsx'
import CreateTrip from './create-trip.jsx'
import Trips from './trips.jsx'
import TripDetails from './trip-details.jsx'
import { getToken } from '../services/api.js'

import AuthCallback from './auth-callback.jsx'

function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

function GuestOnly({ children }) {
  return getToken() ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route
          path="/login"
          element={
            <GuestOnly>
              <Login />
            </GuestOnly>
          }
        />
        <Route
          path="/signup"
          element={
            <GuestOnly>
              <Signup />
            </GuestOnly>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />

        <Route 
          path="/auth/callback" 
          element={
            <AuthCallback />
          } 
        />

        <Route
          path="/complete-profile"
          element={
            <RequireAuth>
              <CompleteProfile />
            </RequireAuth>
          }
        />
        <Route
          path="/create-trip"
          element={
            <RequireAuth>
              <CreateTrip />
            </RequireAuth>
          }
        />
        <Route
          path="/trips"
          element={
            <RequireAuth>
              <Trips />
            </RequireAuth>
          }
        />
        <Route
          path="/trips/:id"
          element={
            <RequireAuth>
              <TripDetails />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Route>
    </Routes>
  )
}

