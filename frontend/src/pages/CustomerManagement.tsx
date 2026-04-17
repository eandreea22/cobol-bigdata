import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Page, Grid } from '../components/Layout'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { apiClient } from '../api/client'
import './CustomerManagement.css'

interface Customer {
  customer_id: string
  customer_name: string
  account_tier: string
  annual_income: number
  last_transaction_date: string
}

export const CustomerManagement: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [editMode, setEditMode] = useState(false)

  const loadAllCustomers = async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getCustomers()
      if (result.customers && result.customers.length > 0) {
        setCustomers(result.customers)
      } else {
        setError('No customers found')
        setCustomers([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllCustomers()
  }, [])

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadAllCustomers()
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getCustomers(searchQuery)
      if (result.customers && result.customers.length > 0) {
        setCustomers(result.customers)
      } else {
        setError('No customers found')
        setCustomers([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer)
    setEditMode(false)
  }

  const tierColors: { [key: string]: string } = {
    GOLD: 'tier-gold',
    SILVER: 'tier-silver',
    BRONZE: 'tier-bronze',
    STANDARD: 'tier-standard'
  }

  return (
    <Page
      title="Customer Management"
      subtitle="Search, view, and manage customer accounts"
    >
      {/* Search Section */}
      <Card variant="minimal" className="search-card">
        <div className="search-form">
          <input
            type="text"
            placeholder="Search by customer name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button onClick={handleSearch} loading={loading}>
            Search
          </Button>
        </div>
      </Card>

      {error && (
        <motion.div
          className="alert alert--danger"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.div>
      )}

      <Grid columns={2} gap="lg">
        {/* Customer List */}
        <Card variant="default" className="customer-list-card">
          <h3>Results ({customers.length})</h3>
          {customers.length > 0 ? (
            <div className="customer-list">
              {customers.map((customer, idx) => (
                <motion.div
                  key={customer.customer_id}
                  className={`customer-item ${
                    selectedCustomer?.customer_id === customer.customer_id ? 'active' : ''
                  }`}
                  onClick={() => handleSelectCustomer(customer)}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  whileHover={{ x: 4 }}
                >
                  <div className="customer-item-main">
                    <h4>{customer.customer_name}</h4>
                    <p>{customer.customer_id}</p>
                  </div>
                  <span className={`tier-badge ${tierColors[customer.account_tier] || 'tier-standard'}`}>
                    {customer.account_tier}
                  </span>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="empty-list">
              <p>No customers found. Try searching by name.</p>
            </div>
          )}
        </Card>

        {/* Customer Details */}
        {selectedCustomer ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card variant="default" className="customer-details-card">
              <div className="details-header">
                <h3>{selectedCustomer.customer_name}</h3>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditMode(!editMode)}
                >
                  {editMode ? 'Cancel' : 'Edit'}
                </Button>
              </div>

              {editMode ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Customer Name</label>
                    <input type="text" defaultValue={selectedCustomer.customer_name} />
                  </div>
                  <div className="form-group">
                    <label>Annual Income</label>
                    <input
                      type="number"
                      defaultValue={selectedCustomer.annual_income}
                      step="1000"
                    />
                  </div>
                  <div className="form-group">
                    <label>Account Tier</label>
                    <select defaultValue={selectedCustomer.account_tier}>
                      <option>STANDARD</option>
                      <option>BRONZE</option>
                      <option>SILVER</option>
                      <option>GOLD</option>
                    </select>
                  </div>
                  <Button fullWidth onClick={() => setEditMode(false)}>
                    Save Changes
                  </Button>
                </div>
              ) : (
                <div className="details-info">
                  <div className="info-item">
                    <span className="label">Customer ID</span>
                    <span className="value">{selectedCustomer.customer_id}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">Account Tier</span>
                    <span className="value">
                      <span
                        className={`tier-badge ${
                          tierColors[selectedCustomer.account_tier] || 'tier-standard'
                        }`}
                      >
                        {selectedCustomer.account_tier}
                      </span>
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="label">Annual Income</span>
                    <span className="value">
                      ${(selectedCustomer.annual_income || 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="label">Last Transaction</span>
                    <span className="value">{selectedCustomer.last_transaction_date}</span>
                  </div>
                </div>
              )}

              <div className="action-buttons">
                <Button variant="tertiary" fullWidth>
                  View 360° Profile
                </Button>
                <Button variant="tertiary" fullWidth>
                  Check Fraud Risk
                </Button>
              </div>
            </Card>
          </motion.div>
        ) : (
          <Card variant="minimal" className="empty-details">
            <div className="empty-state-content">
              <span className="empty-state-icon">👤</span>
              <p>Select a customer to view details</p>
            </div>
          </Card>
        )}
      </Grid>
    </Page>
  )
}
