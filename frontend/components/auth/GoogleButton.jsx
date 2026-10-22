// /**
//  * "Continue with Google" — present in the reference layout.
//  *
//  * There is no OAuth provider configured on the backend, so this is rendered
//  * disabled rather than pretending to work: clicking a button that silently
//  * does nothing is worse than one that is visibly unavailable. Wire it up by
//  * adding a /auth/google route and swapping `disabled` for an onClick.
//  */
// export default function GoogleButton({ label = 'Continue with Google' }) {
//   return (
//     <div className="mt-6">
//       <div className="flex items-center gap-3">
//         <span className="h-px flex-1" style={{ backgroundColor: 'var(--border)' }} />
//         <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
//           Or continue with
//         </span>
//         <span className="h-px flex-1" style={{ backgroundColor: 'var(--border)' }} />
//       </div>

//       <button
//         type="button"
//         disabled
//         title="Google sign-in isn't set up yet — use your email and password."
//         className="mt-4 flex w-full cursor-not-allowed items-center justify-center gap-2.5 rounded-xl border border-subtle px-4 py-3 text-[14px] font-semibold text-mut opacity-60"
//         style={{ backgroundColor: 'var(--panel)' }}
//       >
//         <svg width="17" height="17" viewBox="0 0 48 48" aria-hidden="true">
//           <path
//             fill="#FFC107"
//             d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.0 6.1 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.2-.1-2.4-.4-3.5z"
//           />
//           <path
//             fill="#FF3D00"
//             d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.0 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"
//           />
//           <path
//             fill="#4CAF50"
//             d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.6 39.6 16.2 44 24 44z"
//           />
//           <path
//             fill="#1976D2"
//             d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.2 5.2C39.1 36.9 44 31.1 44 24c0-1.2-.1-2.4-.4-3.5z"
//           />
//         </svg>
//         {label}
//       </button>
//     </div>
//   )
// }


import { supabase } from '../../lib/supabase.js'

export default function GoogleButton({ label = 'Continue with Google' }) {
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      console.error('Google sign-in error:', error)
    }
  }

  return (
    <div className="mt-6">
      <div className="flex items-center gap-3">
        <span
          className="h-px flex-1"
          style={{ backgroundColor: 'var(--border)' }}
        />

        <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
          Or continue with
        </span>

        <span
          className="h-px flex-1"
          style={{ backgroundColor: 'var(--border)' }}
        />
      </div>

      <button
        type="button"
        onClick={handleGoogleLogin}
        className="mt-4 flex w-full items-center justify-center gap-2.5 rounded-xl border border-subtle px-4 py-3 text-[14px] font-semibold text-main transition-colors hover:bg-[var(--panel-hover)]"
        style={{ backgroundColor: 'var(--panel)' }}
      >
        <svg
          width="17"
          height="17"
          viewBox="0 0 48 48"
          aria-hidden="true"
        >
          <path
            fill="#FFC107"
            d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.0 6.1 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.2-.1-2.4-.4-3.5z"
          />
          <path
            fill="#FF3D00"
            d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.0 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"
          />
          <path
            fill="#4CAF50"
            d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.6 39.6 16.2 44 24 44z"
          />
          <path
            fill="#1976D2"
            d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.2 5.2C39.1 36.9 44 31.1 44 24c0-1.2-.1-2.4-.4-3.5z"
          />
        </svg>

        {label}
      </button>
    </div>
  )
}