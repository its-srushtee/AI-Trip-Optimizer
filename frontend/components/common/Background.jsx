/**
 * Page background. Deliberately plain — a solid themed surface.
 * (Previously aurora blobs + a masked grid + a glowing top rule; all removed.)
 */
export default function Background() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10"
      style={{ backgroundColor: 'var(--bg)' }}
    />
  )
}
