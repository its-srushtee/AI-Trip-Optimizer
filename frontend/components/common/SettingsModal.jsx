import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import Button from './Button.jsx'
import { ThemeSegment } from './ThemeToggle.jsx'
import PreferencesEditor, { defaultPreferences } from '../auth/PreferencesEditor.jsx'
import { interests } from '../../lib/constants.js'

export default function SettingsModal({
  open,
  user,
  onClose,
  onSaveProfile,
  onSavePreferences,
  onSignOut,
  onClearData,
  tripsCount,
}) {
  const [profileName, setProfileName] = useState('')
  const [profileEmail, setProfileEmail] = useState('')
  const [editPrefs, setEditPrefs] = useState(defaultPreferences)
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (open) {
      setProfileName(user?.name || '')
      setProfileEmail(user?.email || '')
      setEditPrefs(user?.preferences || defaultPreferences)
      setEditing(false)
    }
  }, [open, user])

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  // An empty object is truthy — check for real content, not just presence.
  const prefs = user?.preferences
  const hasPrefs = !!prefs && Object.keys(prefs).length > 0 && !!prefs.style

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4">
      <div className="absolute inset-0" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} onClick={onClose} />

      <div
        className="relative max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-lg border border-subtle sm:rounded-lg"
        style={{ backgroundColor: 'var(--panel)' }}
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
      >
        <div
          className="sticky top-0 flex items-center justify-between border-b border-subtle px-5 py-3.5"
          style={{ backgroundColor: 'var(--panel)' }}
        >
          <h2 className="text-[15px] font-semibold text-main">Settings</h2>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-md text-mut transition-colors hv hover:text-soft"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-5 py-5">
          {/* Account */}
          <section>
            <h3 className="eyebrow">Account</h3>
            <div className="mt-3 space-y-3">
              <div>
                <label htmlFor="set-name" className="field-label">Name</label>
                <input
                  id="set-name"
                  className="input-field"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="set-email" className="field-label">Email</label>
                <input
                  id="set-email"
                  className="input-field"
                  type="email"
                  value={profileEmail}
                  onChange={(e) => setProfileEmail(e.target.value)}
                />
              </div>
              <div className="flex justify-end">
                <Button
                  variant="secondary"
                  onClick={() => onSaveProfile({ name: profileName, email: profileEmail })}
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </section>

          {/* Preferences */}
          <section className="mt-6 border-t border-subtle pt-5">
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="eyebrow">Travel preferences</h3>
              {!editing && (
                <button
                  onClick={() => setEditing(true)}
                  className="text-[13px] font-medium text-brand hover:underline"
                >
                  {hasPrefs ? 'Edit Preferences' : 'Add Preferences'}
                </button>
              )}
            </div>

            {editing ? (
              <div className="mt-3">
                <PreferencesEditor value={editPrefs} onChange={setEditPrefs} />
                <div className="mt-4 flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setEditing(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={() => {
                      onSavePreferences(editPrefs)
                      setEditing(false)
                    }}
                  >
                    Save Preferences
                  </Button>
                </div>
              </div>
            ) : hasPrefs ? (
              <div className="mt-3 space-y-0">
                <Row label="Style" value={prefs.style} />
                <Row label="Pace" value={prefs.pace} />
                <Row label="Stay" value={prefs.accommodation} />
                <Row label="Food" value={prefs.food} />
                {prefs.interests?.length > 0 && (
                  <div className="flex items-start justify-between gap-4 py-1.5 text-[13px]">
                    <span className="text-mut">Interests</span>
                    <span className="flex flex-wrap justify-end gap-1">
                      {prefs.interests.map((id) => {
                        const it = interests.find((x) => x.id === id)
                        return it ? (
                          <span key={id} className="tag">
                            {it.label}
                          </span>
                        ) : null
                      })}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="mt-2 text-[13px] text-mut">
                Not set yet — add them to get personalized recommendations.
              </p>
            )}
          </section>

          {/* Appearance */}
          <section className="mt-6 border-t border-subtle pt-5">
            <h3 className="eyebrow">Appearance</h3>
            <ThemeSegment className="mt-3 max-w-[16rem]" />
          </section>

          {/* Data */}
          <section className="mt-6 border-t border-subtle pt-5">
            <h3 className="eyebrow">Data</h3>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <p className="text-[13px] text-mut">
                Delete all {tripsCount} saved trip{tripsCount === 1 ? '' : 's'}. This cannot be undone.
              </p>
              <Button variant="danger" onClick={onClearData} disabled={tripsCount === 0}>
                Delete All Trips
              </Button>
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="secondary" onClick={onSignOut}>
                Sign Out
              </Button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-subtle py-1.5 text-[13px] last:border-0">
      <span className="text-mut">{label}</span>
      <span className="font-medium text-soft">{value}</span>
    </div>
  )
}
