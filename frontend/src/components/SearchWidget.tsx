import React, { useState } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { Button } from './Button'
import { apiClient } from '../api/client'
import './SearchWidget.css'

interface SearchWidgetProps {
  onSelect: (customerId: string, customerName: string) => void
  pageKey: string
}

interface Customer {
  customer_id: string
  customer_name: string
  account_tier: string
  annual_income: number
  last_transaction_date: string
}

export const SearchWidget: React.FC<SearchWidgetProps> = ({
  onSelect,
  pageKey
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState<Customer[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedName, setSelectedName] = useState<string | null>(null)
  const [showResults, setShowResults] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setLoading(true)
    try {
      const result = await apiClient.getCustomers(searchQuery)
      if (result.customers && result.customers.length > 0) {
        setResults(result.customers)
        setShowResults(true)
      } else {
        setResults([])
        setShowResults(true)
      }
    } catch (err) {
      console.error('Search error:', err)
      setResults([])
      setShowResults(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (customer: Customer) => {
    setSelectedId(customer.customer_id)
    setSelectedName(customer.customer_name)
    setShowResults(false)
    setSearchQuery('')
    onSelect(customer.customer_id, customer.customer_name)
  }

  const handleChange = () => {
    setSelectedId(null)
    setSelectedName(null)
    setShowResults(false)
    setSearchQuery('')
    setResults([])
  }

  if (selectedId && selectedName) {
    return (
      <motion.div
        className="search-widget selected"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="search-widget__selected">
          <div className="search-widget__badge">
            <span className="search-widget__badge-name">{selectedName}</span>
            <span className="search-widget__badge-id">{selectedId}</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleChange}
          >
            Change
          </Button>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      className="search-widget"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="search-widget__input-group">
        <input
          type="text"
          className="search-widget__input"
          placeholder="Search by name (e.g., Smith)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          disabled={loading}
        />
        <Button
          onClick={handleSearch}
          loading={loading}
          size="sm"
        >
          Search
        </Button>
      </div>

      {showResults && (
        <motion.div
          className="search-widget__results"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {results.length > 0 ? (
            <div className="search-widget__list">
              {results.map((customer) => (
                <motion.button
                  key={customer.customer_id}
                  className="search-widget__result-item"
                  onClick={() => handleSelect(customer)}
                  whileHover={{ x: 4 }}
                  whileTap={{ x: 2 }}
                >
                  <div className="search-widget__result-info">
                    <span className="search-widget__result-name">
                      {customer.customer_name}
                    </span>
                    <span className="search-widget__result-id">
                      {customer.customer_id}
                    </span>
                  </div>
                  <span className="search-widget__select-arrow">→</span>
                </motion.button>
              ))}
            </div>
          ) : (
            <div className="search-widget__empty">
              <p>No customers found</p>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}
