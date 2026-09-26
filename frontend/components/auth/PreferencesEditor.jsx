import { interests, travelStyles, tripPaces, accommodationOptions, foodOptions } from '../../lib/constants.js'

export const defaultPreferences = {
  style: 'Comfort',
  interests: [],
  pace: 'Balanced',
  accommodation: 'Hotel',
  food: 'No preference',
}

export default function PreferencesEditor({ value, onChange }) {
  const v = { ...defaultPreferences, ...(value || {}) }
  const set = (key, val) => onChange({ ...v, [key]: val })

  const toggleInterest = (id) =>
    onChange({
      ...v,
      interests: v.interests.includes(id)
        ? v.interests.filter((x) => x !== id)
        : [...v.interests, id],
    })

  const Group = ({ label, hint, children }) => (
    <div>
      <label className="field-label">
        {label}
        {hint && <span className="ml-1 font-normal text-faint">{hint}</span>}
      </label>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  )

  const Choice = ({ active, onClick, children }) => (
    <button type="button" onClick={onClick} className={`chip-btn ${active ? 'chip-on' : ''}`}>
      {children}
    </button>
  )

  return (
    <div className="space-y-5">
      <Group label="Travel style">
        {travelStyles.map((s) => (
          <Choice key={s} active={v.style === s} onClick={() => set('style', s)}>
            {s}
          </Choice>
        ))}
      </Group>

      <Group label="Interests" hint="— select any">
        {interests.map((i) => (
          <Choice
            key={i.id}
            active={v.interests.includes(i.id)}
            onClick={() => toggleInterest(i.id)}
          >
            {i.label}
          </Choice>
        ))}
      </Group>

      <Group label="Trip pace">
        {tripPaces.map((p) => (
          <Choice key={p} active={v.pace === p} onClick={() => set('pace', p)}>
            {p}
          </Choice>
        ))}
      </Group>

      <Group label="Accommodation">
        {accommodationOptions.map((a) => (
          <Choice key={a} active={v.accommodation === a} onClick={() => set('accommodation', a)}>
            {a}
          </Choice>
        ))}
      </Group>

      <Group label="Food preference">
        {foodOptions.map((f) => (
          <Choice key={f} active={v.food === f} onClick={() => set('food', f)}>
            {f}
          </Choice>
        ))}
      </Group>
    </div>
  )
}
