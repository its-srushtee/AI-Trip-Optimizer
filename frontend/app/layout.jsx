import { Outlet } from 'react-router-dom'
import Background from '../components/common/Background.jsx'

/**
 * Shared app layout: ambient background + routed content.
 * Wraps every route (login, signup, dashboard, …) so the themed background
 * renders once, exactly like the original single-page layout.
 */
export default function AppLayout() {
  return (
    <>
      <Background />
      <Outlet />
    </>
  )
}
