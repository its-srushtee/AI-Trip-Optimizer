import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

export default function Field({ label, id, type = 'text', placeholder, icon, error, ...rest }) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-[13px] font-medium text-soft">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 z-10 -translate-y-1/2 text-faint">
            {icon}
          </span>
        )}
        <input
          id={id}
          type={type}
          placeholder={placeholder}
          className="input-field"
          style={{ paddingLeft: icon ? '2.75rem' : '1rem' }}
          {...rest}
        />
      </div>
      {error && <p className="text-[12px] font-medium text-rose-500">{error}</p>}
    </div>
  )
}

export function PasswordInput({ label, id, placeholder, icon, error, ...rest }) {
  const [show, setShow] = useState(false)
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-[13px] font-medium text-soft">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 z-10 -translate-y-1/2 text-faint">
            {icon}
          </span>
        )}
        <input
          id={id}
          type={show ? 'text' : 'password'}
          placeholder={placeholder}
          className="input-field"
          style={{ paddingLeft: icon ? '2.75rem' : '1rem', paddingRight: '2.75rem' }}
          {...rest}
        />
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="absolute right-1.5 top-1/2 z-10 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-lg text-faint transition hover:text-soft lg:h-9 lg:w-9"
          aria-label={show ? 'Hide password' : 'Show password'}
        >
          {show ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </div>
      {error && <p className="text-[12px] font-medium text-rose-500">{error}</p>}
    </div>
  )
}
