import { useState } from 'react'
import { getUser, saveUser, clearUser } from '../lib/userStore.js'
import { getToken, clearToken } from '../services/api.js'

export function useAuth() {
  const [user, setUser] = useState(() => getUser())

  const persistUser = (u) => {
    saveUser(u)
    setUser(u)
  }

  const signOut = () => {
    clearUser()
    clearToken()
  }

  return { user, setUser, persistUser, signOut, token: getToken() }
}
