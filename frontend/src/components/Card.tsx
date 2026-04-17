import React from 'react'
import clsx from 'clsx'
import './Card.css'

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'interactive' | 'minimal'
  onClick?: () => void
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  onClick
}) => {
  return (
    <div
      className={clsx('card', `card--${variant}`, className)}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string | number
  subtext?: string
  color?: 'default' | 'success' | 'danger' | 'warning'
  icon?: React.ReactNode
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  color = 'default',
  icon
}) => {
  return (
    <Card variant="interactive" className={`metric-card metric-card--${color}`}>
      <div className="metric-card__header">
        {icon && <div className="metric-card__icon">{icon}</div>}
        <span className="metric-card__label">{label}</span>
      </div>
      <div className="metric-card__value">{value}</div>
      {subtext && <p className="metric-card__subtext">{subtext}</p>}
    </Card>
  )
}

interface StatusCardProps {
  title: string
  status: 'approved' | 'pending' | 'declined'
  details: Array<{ label: string; value: string }>
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  status,
  details
}) => {
  const statusConfig = {
    approved: { label: 'APPROVED', color: 'success' },
    pending: { label: 'PENDING', color: 'warning' },
    declined: { label: 'DECLINED', color: 'danger' }
  }

  const config = statusConfig[status]

  return (
    <Card variant="default" className="status-card">
      <div className="status-card__header">
        <h3>{title}</h3>
        <span className={`badge badge--${config.color}`}>
          {config.label}
        </span>
      </div>
      <div className="status-card__details">
        {details.map((detail, idx) => (
          <div key={idx} className="status-card__detail">
            <span className="status-card__label">{detail.label}</span>
            <span className="status-card__value">{detail.value}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
