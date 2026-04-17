import React from 'react'
import clsx from 'clsx'
import './Button.css'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled = false,
  onClick,
  className,
  type = 'button'
}) => {
  return (
    <button
      className={clsx(
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth && 'btn--full-width',
        (disabled || loading) && 'btn--disabled',
        className
      )}
      onClick={onClick}
      disabled={disabled || loading}
      type={type}
    >
      {loading ? (
        <>
          <span className="btn__spinner"></span>
          {children}
        </>
      ) : (
        children
      )}
    </button>
  )
}

interface IconButtonProps {
  icon: React.ReactNode
  variant?: 'default' | 'accent'
  onClick?: () => void
  className?: string
  ariaLabel?: string
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  variant = 'default',
  onClick,
  className,
  ariaLabel
}) => {
  return (
    <button
      className={clsx('icon-btn', `icon-btn--${variant}`, className)}
      onClick={onClick}
      aria-label={ariaLabel}
    >
      {icon}
    </button>
  )
}
