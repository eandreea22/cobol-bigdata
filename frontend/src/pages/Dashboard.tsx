import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Page, Grid } from '../components/Layout'
import { Card, MetricCard, StatusCard } from '../components/Card'
import { Button } from '../components/Button'
import { SearchWidget } from '../components/SearchWidget'
import { apiClient } from '../api/client'
import './Dashboard.css'

interface Customer360Data {
  customer_name: string
  account_balance: number
  transaction_count: number
  avg_monthly: number
  risk_score: number
  last_transaction_date: string
  return_code: string
}

interface DashboardProps {
  preSelectedCustomerId?: string | null
  onCustomerSelected?: () => void
}

export const Dashboard: React.FC<DashboardProps> = ({
  preSelectedCustomerId,
  onCustomerSelected
}) => {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null)
  const [data, setData] = useState<Customer360Data | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFetch = async (customerId: string) => {
    setSelectedCustomerId(customerId)
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getCustomer360(customerId)
      if (result.return_code === '00') {
        setData(result)
      } else if (result.return_code === '01') {
        setError('Customer not found')
      } else {
        setError('An error occurred while fetching data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (preSelectedCustomerId) {
      handleFetch(preSelectedCustomerId)
      onCustomerSelected?.()
    }
  }, [preSelectedCustomerId])

  return (
    <Page
      title="Customer 360°"
      subtitle="Comprehensive customer profile and financial overview"
    >
      {/* Search Section */}
      <SearchWidget
        pageKey="c360"
        onSelect={(id) => handleFetch(id)}
      />

      {/* Error Display */}
      {error && (
        <motion.div
          className="alert alert--danger"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          ⚠️ {error}
        </motion.div>
      )}

      {/* Data Display */}
      {data && (
        <>
          {/* Customer Profile Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card variant="default" className="profile-card">
              <div className="profile-header">
                <div className="profile-avatar">
                  {data.customer_name.charAt(0).toUpperCase()}
                </div>
                <div className="profile-info">
                  <h3>{data.customer_name}</h3>
                  <p>ID: {selectedCustomerId}</p>
                </div>
                <div className={`risk-badge risk-badge--${getRiskLevel(data.risk_score)}`}>
                  {data.risk_score}
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Key Metrics */}
          <Grid columns={4}>
            <MetricCard
              label="Account Balance"
              value={`$${(data.account_balance / 100).toFixed(2)}`}
              color="success"
              icon="💰"
            />
            <MetricCard
              label="Total Transactions"
              value={data.transaction_count.toString()}
              color="default"
              icon="📊"
            />
            <MetricCard
              label="Avg Monthly Spend"
              value={`$${(data.avg_monthly / 100).toFixed(2)}`}
              color="default"
              icon="📈"
            />
            <MetricCard
              label="Risk Score"
              value={data.risk_score.toString()}
              color={data.risk_score > 500 ? 'danger' : 'success'}
              icon="⚠️"
            />
          </Grid>

          {/* Additional Information */}
          <Grid columns={2}>
            <Card variant="default">
              <h4>Activity Summary</h4>
              <div className="info-grid">
                <div className="info-item">
                  <span className="label">Last Transaction</span>
                  <span className="value">{data.last_transaction_date}</span>
                </div>
                <div className="info-item">
                  <span className="label">Customer Status</span>
                  <span className="value status-active">Active</span>
                </div>
              </div>
            </Card>

            <Card variant="default">
              <h4>Risk Assessment</h4>
              <div className="risk-meter">
                <div className="risk-bar">
                  <div
                    className={`risk-indicator ${getRiskLevel(data.risk_score)}`}
                    style={{ width: `${(data.risk_score / 999) * 100}%` }}
                  ></div>
                </div>
                <p className="risk-label">
                  {getRiskLabel(data.risk_score)}
                </p>
              </div>
            </Card>
          </Grid>
        </>
      )}

      {/* Empty State */}
      {!data && !error && !loading && (
        <Card variant="minimal" className="empty-state">
          <div className="empty-state-content">
            <span className="empty-state-icon">🔍</span>
            <p>Enter a customer ID to view their profile</p>
          </div>
        </Card>
      )}
    </Page>
  )
}

function getRiskLevel(score: number): string {
  if (score < 250) return 'low'
  if (score < 500) return 'medium'
  return 'high'
}

function getRiskLabel(score: number): string {
  if (score < 250) return 'Low Risk'
  if (score < 500) return 'Medium Risk'
  return 'High Risk'
}
