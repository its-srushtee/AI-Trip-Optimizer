/**
 * Button. Three variants, two sizes, one fixed height per size so rows of
 * buttons always align. Solid accent fill — no gradients, no glow.
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  className = '',
  ...rest
}) {
  const base =
    'inline-flex items-center justify-center gap-1.5 rounded-full font-semibold transition-colors ' +
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 ' +
    'disabled:cursor-not-allowed disabled:opacity-55'

  const sizes = {
    sm: 'h-11 px-4 text-[13px] sm:h-9',
    md: 'h-11 px-6 text-[15px]',
  }

  const variants = {
    primary: 'btn-grad',
    secondary: 'text-soft bg-panel border border-subtle hv hover:border-strong',
    ghost: 'text-mut hv hover:text-soft',
    danger: 'border',
  }

  const styles = {
    primary: { '--tw-ring-color': 'var(--accent)' },
    secondary: { '--tw-ring-color': 'var(--accent)' },
    ghost: { '--tw-ring-color': 'var(--accent)' },
    danger: {
      color: 'var(--danger)',
      borderColor: 'var(--danger-border)',
      backgroundColor: 'var(--danger-soft)',
      '--tw-ring-color': 'var(--danger)',
    },
  }

  return (
    <button
      type={type}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      style={styles[variant]}
      {...rest}
    >
      {children}
    </button>
  )
}
