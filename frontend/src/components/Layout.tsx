import React, { useState } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import './Layout.css'

interface SidebarItem {
  id: string
  label: string
  icon: React.ReactNode
}

interface LayoutProps {
  children: React.ReactNode
  sidebarItems: SidebarItem[]
  currentPage: string
  onNavigate: (pageId: string) => void
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  sidebarItems,
  currentPage,
  onNavigate
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="layout">
      {/* Sidebar */}
      <motion.aside
        className={clsx('sidebar', !sidebarOpen && 'sidebar--collapsed')}
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="sidebar__header">
          <div className="sidebar__logo">
            <span className="sidebar__logo-icon">🏦</span>
            {sidebarOpen && <span className="sidebar__logo-text">BankCore</span>}
          </div>
        </div>

        <nav className="sidebar__nav">
          {sidebarItems.map((item) => (
            <motion.button
              key={item.id}
              className={clsx(
                'sidebar__item',
                currentPage === item.id && 'sidebar__item--active'
              )}
              onClick={() => onNavigate(item.id)}
              whileHover={{ x: 4 }}
              whileTap={{ x: 2 }}
            >
              <span className="sidebar__item-icon">{item.icon}</span>
              {sidebarOpen && <span className="sidebar__item-label">{item.label}</span>}
            </motion.button>
          ))}
        </nav>

        <button
          className="sidebar__toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? '‹' : '›'}
        </button>
      </motion.aside>

      {/* Main Content */}
      <div className="layout__main">
        {/* Header */}
        <header className="header">
          <div className="header__content">
            <h1 className="header__title">Analytics Dashboard</h1>
            <div className="header__actions">
              <button className="header__button" aria-label="Notifications">
                🔔
              </button>
              <button className="header__button" aria-label="User Menu">
                👤
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <motion.main
          className="main-content"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          key={currentPage}
        >
          {children}
        </motion.main>
      </div>
    </div>
  )
}

interface PageProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  className?: string
}

export const Page: React.FC<PageProps> = ({
  title,
  subtitle,
  children,
  className
}) => {
  return (
    <div className={clsx('page', className)}>
      <div className="page__header">
        <div>
          <h2 className="page__title">{title}</h2>
          {subtitle && <p className="page__subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="page__content">
        {children}
      </div>
    </div>
  )
}

interface GridProps {
  columns?: number
  gap?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
}

export const Grid: React.FC<GridProps> = ({
  columns = 3,
  gap = 'lg',
  children,
  className
}) => {
  return (
    <div
      className={clsx('grid', `grid--col-${columns}`, `grid--gap-${gap}`, className)}
    >
      {children}
    </div>
  )
}
