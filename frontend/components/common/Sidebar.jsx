import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import {
  Home,
  Map,
  Plus,
  User,
  LogOut,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Sparkles,
  Sun,
  Moon,
} from 'lucide-react'
import { clearUser, getUser } from '../../lib/userStore.js'
import { clearToken } from '../../services/api.js'
import { useTheme } from '../../hooks/useTheme.js'

const NAV_ITEMS = [
  { icon: Home, label: 'Home', path: '/dashboard' },
  { icon: Map, label: 'My Trips', path: '/trips' },
  { icon: Plus, label: 'Create Trip', path: '/create-trip' },
  { icon: User, label: 'Profile', path: '/complete-profile' },
]

export default function Sidebar({ activeNav }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggle: toggleTheme } = useTheme()

  // Collapsed state persisted in localStorage
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('sidebar_collapsed') === 'true'
    } catch {
      return false
    }
  })

  // Mobile drawer open state
  const [mobileOpen, setMobileOpen] = useState(false)
  const [showHelp, setShowHelp] = useState(false)

  const user = getUser()
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'Traveler'

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev
      try {
        localStorage.setItem('sidebar_collapsed', String(next))
        window.dispatchEvent(new Event('sidebar_toggle'))
      } catch {}
      return next
    })
  }

  const signOut = () => {
    clearUser()
    clearToken()
    navigate('/login')
  }

  const currentPath = location.pathname

  const isItemActive = (item) => {
    if (activeNav) return activeNav.toLowerCase() === item.label.toLowerCase()
    return currentPath === item.path
  }

  return (
    <>
      {/* ======= Desktop Sidebar ======= */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r transition-all duration-300 ease-in-out lg:flex ${
          collapsed ? 'w-[72px]' : 'w-[230px]'
        }`}
        style={{
          borderColor: 'var(--sidebar-border, #e4e8ef)',
          backgroundColor: 'var(--sidebar-bg, #ffffff)',
          boxShadow: '1px 0 10px rgba(0,0,0,0.02)',
        }}
      >
        {/* Logo & Pin/Unpin */}
        <div
          className="flex h-16 items-center justify-between border-b px-4"
          style={{ borderColor: 'var(--border, #e4e8ef)' }}
        >
          <Link
            to="/dashboard"
            className="flex items-center gap-2.5 overflow-hidden transition-opacity hover:opacity-90"
          >
            <span
              className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-white shadow-sm"
              style={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z"
                  stroke="#fff"
                  strokeWidth="2.2"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="10" r="2.5" fill="#fff" />
              </svg>
            </span>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-[15px] font-bold tracking-tight text-slate-900">
                  TripPlanner
                </span>
                <span className="text-[10px] font-medium text-slate-400 -mt-0.5">
                  Smart Travel Studio
                </span>
              </div>
            )}
          </Link>

          {/* Pin/Unpin Collapse Toggle */}
          <button
            type="button"
            onClick={toggleCollapsed}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="grid h-7 w-7 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const active = isItemActive(item)
            return (
              <button
                key={item.label}
                type="button"
                onClick={() => navigate(item.path)}
                title={collapsed ? item.label : undefined}
                className={`group relative flex w-full items-center rounded-xl font-medium transition-all duration-150 ${
                  collapsed
                    ? 'h-11 justify-center px-0'
                    : 'h-11 gap-3 px-3 text-[14px]'
                } ${
                  active
                    ? 'bg-violet-50 text-violet-700 shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
                style={
                  active
                    ? {
                        backgroundColor: theme === 'dark' ? 'rgba(99, 102, 241, 0.22)' : '#f5f3ff',
                        color: theme === 'dark' ? '#c7d2fe' : '#6d28d9',
                      }
                    : {}
                }
              >
                <Icon
                  size={19}
                  className={`shrink-0 transition-transform group-hover:scale-105 ${
                    active ? 'text-violet-600 dark:text-indigo-300' : 'text-slate-400 dark:text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200'
                  }`}
                  style={active ? { color: theme === 'dark' ? '#818cf8' : '#7c3aed' } : {}}
                />
                {!collapsed && (
                  <span className="truncate tracking-[-0.01em]">{item.label}</span>
                )}
                {active && !collapsed && (
                  <span
                    className="ml-auto h-1.5 w-1.5 rounded-full"
                    style={{ backgroundColor: theme === 'dark' ? '#818cf8' : '#7c3aed' }}
                  />
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer Actions: Help & Logout */}
        <div
          className="border-t p-3 space-y-1"
          style={{ borderColor: 'var(--border, #e4e8ef)' }}
        >
          {/* Help Button */}
          <button
            type="button"
            onClick={() => setShowHelp(true)}
            title={collapsed ? 'Help & Guides' : undefined}
            className={`group flex w-full items-center rounded-xl font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors ${
              collapsed
                ? 'h-10 justify-center px-0'
                : 'h-10 gap-3 px-3 text-[13px]'
            }`}
          >
            <HelpCircle size={18} className="shrink-0 text-slate-400 group-hover:text-slate-600" />
            {!collapsed && <span>Help & FAQ</span>}
          </button>

          {/* Dark / Light Mode Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            title={collapsed ? (theme === 'dark' ? 'Dark Mode (click for light)' : 'Light Mode (click for dark)') : undefined}
            className={`group flex w-full items-center rounded-xl font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors ${
              collapsed
                ? 'h-10 justify-center px-0'
                : 'h-10 justify-between px-3 text-[13px]'
            }`}
          >
            <div className="flex items-center gap-3">
              {theme === 'dark' ? (
                <Moon size={18} className="shrink-0 text-indigo-400 transition-transform group-hover:-rotate-12" />
              ) : (
                <Sun size={18} className="shrink-0 text-amber-500 transition-transform group-hover:rotate-45" />
              )}
              {!collapsed && <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>}
            </div>
            {!collapsed && (
              <div
                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-200 ${
                  theme === 'dark' ? 'bg-indigo-600' : 'bg-slate-200'
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                    theme === 'dark' ? 'translate-x-4.5' : 'translate-x-1'
                  }`}
                />
              </div>
            )}
          </button>

          {/* User Profile summary when expanded */}
          {!collapsed && (
            <div
              onClick={() => navigate('/complete-profile')}
              className="flex cursor-pointer items-center gap-2.5 rounded-xl px-2.5 py-2 hover:bg-slate-50 transition-colors"
            >
              <div
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[12px] font-bold text-white shadow-xs"
                style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
              >
                {firstName.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[13px] font-semibold text-slate-800 truncate">
                  {user?.name || 'Traveler'}
                </span>
                <span className="text-[11px] text-slate-400 truncate">
                  {user?.email || 'My account'}
                </span>
              </div>
            </div>
          )}

          {/* Logout Button */}
          <button
            type="button"
            onClick={signOut}
            title={collapsed ? 'Logout' : undefined}
            className={`group flex w-full items-center rounded-xl font-medium text-red-600 hover:bg-red-50 transition-colors ${
              collapsed
                ? 'h-10 justify-center px-0'
                : 'h-10 gap-3 px-3 text-[13px]'
            }`}
          >
            <LogOut size={18} className="shrink-0 text-red-500 transition-transform group-hover:-translate-x-0.5" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* ======= Mobile Top Bar ======= */}
      <header
        className="fixed top-0 left-0 right-0 z-30 flex h-14 items-center justify-between border-b px-4 lg:hidden"
        style={{
          backgroundColor: 'var(--panel, #ffffff)',
          borderColor: 'var(--border, #e4e8ef)',
        }}
      >
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="grid h-9 w-9 place-items-center rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <Link to="/dashboard" className="flex items-center gap-2">
            <span
              className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-white"
              style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z"
                  stroke="#fff"
                  strokeWidth="2.2"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="10" r="2.2" fill="#fff" />
              </svg>
            </span>
            <span className="text-[14px] font-bold text-slate-900">TripPlanner</span>
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="grid h-8 w-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={17} className="text-amber-400" /> : <Moon size={17} className="text-indigo-500" />}
          </button>

          <button
            onClick={() => navigate('/complete-profile')}
            className="grid h-8 w-8 place-items-center rounded-full text-[11px] font-bold text-white shadow-xs"
            style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
          >
            {firstName.slice(0, 2).toUpperCase()}
          </button>
        </div>
      </header>

      {/* ======= Mobile Drawer Backdrop & Menu ======= */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileOpen(false)}
          />

          {/* Drawer panel */}
          <div
            className="fixed inset-y-0 left-0 w-64 max-w-[80vw] flex flex-col bg-white shadow-xl animate-in slide-in-from-left duration-200"
            style={{ backgroundColor: 'var(--panel, #ffffff)' }}
          >
            {/* Header */}
            <div className="flex h-14 items-center justify-between border-b px-4">
              <div className="flex items-center gap-2">
                <span
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-white"
                  style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z"
                      stroke="#fff"
                      strokeWidth="2"
                    />
                    <circle cx="12" cy="10" r="2.2" fill="#fff" />
                  </svg>
                </span>
                <span className="text-[14px] font-bold text-slate-900">TripPlanner</span>
              </div>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>

            {/* Navigation items */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon
                const active = isItemActive(item)
                return (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => {
                      setMobileOpen(false)
                      navigate(item.path)
                    }}
                    className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-3 text-[14px] font-medium transition-colors ${
                      active
                        ? 'bg-violet-50 text-violet-700 font-semibold'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                    style={
                      active
                        ? {
                            backgroundColor: theme === 'dark' ? 'rgba(99, 102, 241, 0.22)' : '#f5f3ff',
                            color: theme === 'dark' ? '#c7d2fe' : '#6d28d9',
                          }
                        : {}
                    }
                  >
                    <Icon
                      size={18}
                      className={active ? 'text-violet-600 dark:text-indigo-300' : 'text-slate-400 dark:text-slate-400'}
                      style={active ? { color: theme === 'dark' ? '#818cf8' : '#7c3aed' } : {}}
                    />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </nav>

            {/* Footer */}
            <div className="border-t p-3 space-y-1">
              <button
                type="button"
                onClick={toggleTheme}
                className="flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-[13px] font-medium text-slate-600 hover:bg-slate-50"
              >
                <div className="flex items-center gap-3">
                  {theme === 'dark' ? (
                    <Moon size={17} className="text-indigo-400" />
                  ) : (
                    <Sun size={17} className="text-amber-500" />
                  )}
                  <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
                </div>
                <div
                  className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-200 ${
                    theme === 'dark' ? 'bg-indigo-600' : 'bg-slate-200'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                      theme === 'dark' ? 'translate-x-4.5' : 'translate-x-1'
                    }`}
                  />
                </div>
              </button>
              <button
                type="button"
                onClick={() => {
                  setMobileOpen(false)
                  setShowHelp(true)
                }}
                className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-medium text-slate-600 hover:bg-slate-50"
              >
                <HelpCircle size={17} className="text-slate-400" />
                <span>Help & FAQ</span>
              </button>
              <button
                type="button"
                onClick={signOut}
                className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-medium text-red-600 hover:bg-red-50"
              >
                <LogOut size={17} className="text-red-500" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======= Help & Support Modal ======= */}
      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
            onClick={() => setShowHelp(false)}
          />
          <div
            className="relative z-10 w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl transition-all"
            style={{ backgroundColor: 'var(--panel, #ffffff)' }}
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-violet-100 text-violet-600">
                  <Sparkles size={16} />
                </span>
                <h3 className="text-base font-bold text-slate-900">TripPlanner Help & Guides</h3>
              </div>
              <button
                onClick={() => setShowHelp(false)}
                className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 space-y-4 max-h-[60vh] overflow-y-auto pr-1 text-[13px] text-slate-600 leading-relaxed">
              <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                <h4 className="font-semibold text-slate-800 mb-1">
                  How does AI trip optimization work?
                </h4>
                <p>
                  When you plan a trip, our multi-agent pipeline analyzes your budget, interests, and travel pace to balance your budget across flights (30%), accommodation (35%), dining (15%), and activities (20%).
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                <h4 className="font-semibold text-slate-800 mb-1">
                  How are destination recommendations personalized?
                </h4>
                <p>
                  Set your travel style, pace, and interests under <strong>Profile</strong>. We score every destination against your personal preferences to highlight the best matches first.
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                <h4 className="font-semibold text-slate-800 mb-1">
                  Can I edit or remove saved trips?
                </h4>
                <p>
                  Yes! Head over to <strong>My Trips</strong> to view your upcoming, past, or saved trips, review details, or remove trips anytime.
                </p>
              </div>
            </div>

            <div className="mt-5 flex justify-end pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowHelp(false)}
                className="rounded-xl px-4 py-2 text-[13px] font-semibold text-white shadow-xs transition-opacity hover:opacity-90"
                style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
