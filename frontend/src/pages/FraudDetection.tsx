import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Page, Grid } from '../components/Layout'
import { Card, MetricCard } from '../components/Card'
import { Button } from '../components/Button'
import { SearchWidget } from '../components/SearchWidget'
import { apiClient } from '../api/client'
import './FraudDetection.css'

interface BatchFraudResult {
  customer_id: string
  total_transactions: number
  flagged_count: number
  fraud_risk_avg: string
  transactions: Array<{
    transaction_id: string
    amount: number
    fraud_risk: string
    fraud_score: number
    timestamp: string
    location: string
    category: string
  }>
}

interface FraudDetectionProps {
  preSelectedCustomerId?: string | null
  onCustomerSelected?: () => void
}

export const FraudDetection: React.FC<FraudDetectionProps> = ({
  preSelectedCustomerId,
  onCustomerSelected
}) => {
  const [batchData, setBatchData] = useState<BatchFraudResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')

  const handleFetch = async (customerId: string) => {
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.batchFraudAnalysis(customerId)
      if (result.customer_id) {
        setBatchData(result)
      } else {
        setError('Unable to fetch fraud data')
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

  const filteredTransactions = batchData?.transactions.filter(t => {
    if (filter === 'all') return true
    return t.fraud_risk === filter
  }) || []

  const getRiskColor = (risk: string) => {
    if (risk === 'HIGH') return '#ef4444'
    if (risk === 'MEDIUM') return '#f59e0b'
    return '#10b981'
  }

  return (
    <Page
      title="Fraud Detection"
      subtitle="Real-time and batch fraud risk analysis"
    >
      {/* Search Section */}
      <SearchWidget
        pageKey="fraud"
        onSelect={(id) => handleFetch(id)}
      />

      {error && (
        <motion.div
          className="alert alert--danger"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.div>
      )}

      {batchData && (
        <>
          {/* Summary Metrics */}
          <Grid columns={4}>
            <MetricCard
              label="Total Transactions"
              value={batchData.total_transactions}
              color="default"
              icon="📊"
            />
            <MetricCard
              label="Flagged"
              value={batchData.flagged_count}
              color={batchData.flagged_count > 0 ? 'danger' : 'success'}
              icon="🚩"
            />
            <MetricCard
              label="Avg Risk Score"
              value={batchData.fraud_risk_avg}
              color={getRiskLevel(batchData.fraud_risk_avg)}
              icon="⚠️"
            />
            <MetricCard
              label="Status"
              value={batchData.flagged_count === 0 ? 'Safe' : 'Review'}
              color={batchData.flagged_count === 0 ? 'success' : 'warning'}
              icon={batchData.flagged_count === 0 ? '✓' : '!'}
            />
          </Grid>

          {/* Filter & Table */}
          <Card variant="default" className="transactions-card">
            <div className="transactions-header">
              <h3>Transaction Analysis</h3>
              <div className="risk-filters">
                {['all', 'LOW', 'MEDIUM', 'HIGH'].map(r => (
                  <button
                    key={r}
                    className={`filter-btn ${filter === r ? 'active' : ''}`}
                    onClick={() => setFilter(r)}
                  >
                    {r === 'all' ? 'All' : r}
                  </button>
                ))}
              </div>
            </div>

            {filteredTransactions.length > 0 ? (
              <div className="transactions-table">
                <div className="table-header">
                  <div className="col col-id">ID</div>
                  <div className="col col-amount">Amount</div>
                  <div className="col col-location">Location</div>
                  <div className="col col-category">Category</div>
                  <div className="col col-risk">Risk</div>
                  <div className="col col-score">Score</div>
                  <div className="col col-time">Time</div>
                </div>

                {filteredTransactions.map((txn, idx) => (
                  <motion.div
                    key={txn.transaction_id}
                    className="table-row"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    <div className="col col-id">{txn.transaction_id}</div>
                    <div className="col col-amount">${(txn.amount).toFixed(2)}</div>
                    <div className="col col-location">{txn.location}</div>
                    <div className="col col-category">{txn.category}</div>
                    <div className="col col-risk">
                      <span className={`risk-badge ${txn.fraud_risk.toLowerCase()}`}>
                        {txn.fraud_risk}
                      </span>
                    </div>
                    <div className="col col-score">{txn.fraud_score}/999</div>
                    <div className="col col-time">
                      {new Date(txn.timestamp).toLocaleDateString()}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="no-results">
                <p>No transactions match the selected filter</p>
              </div>
            )}
          </Card>

          {/* Risk Legend */}
          <Card variant="minimal" className="risk-legend">
            <h4>Risk Levels</h4>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-dot" style={{ background: '#10b981' }}></span>
                <span>Low Risk: Normal spending patterns</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ background: '#f59e0b' }}></span>
                <span>Medium Risk: Minor anomalies detected</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ background: '#ef4444' }}></span>
                <span>High Risk: Significant red flags present</span>
              </div>
            </div>
          </Card>
        </>
      )}

      {!batchData && !error && !loading && (
        <Card variant="minimal" className="empty-state">
          <div className="empty-state-content">
            <span className="empty-state-icon">🔍</span>
            <p>Enter a customer ID to analyze fraud risk across all transactions</p>
          </div>
        </Card>
      )}
    </Page>
  )
}

function getRiskLevel(riskStr: string): 'success' | 'warning' | 'danger' {
  const risk = parseFloat(riskStr)
  if (risk < 300) return 'success'
  if (risk < 600) return 'warning'
  return 'danger'
}
