import { Outlet } from 'react-router-dom'
import Background from '../components/common/Background.jsx'

export default function AppLayout() {
  return (
    <>
      <Background />
      <Outlet />
    </>
  )
}
