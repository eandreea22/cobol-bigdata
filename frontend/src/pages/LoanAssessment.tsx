import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Page, Grid } from '../components/Layout'
import { Card, MetricCard, StatusCard } from '../components/Card'
import { Button } from '../components/Button'
import { SearchWidget } from '../components/SearchWidget'
import { apiClient } from '../api/client'
import './LoanAssessment.css'

interface LoanResult {
  credit_score: number
  eligible: string
  interest_rate: number
  max_amount: number
  reject_reason: string
  return_code: string
}

export const LoanAssessment: React.FC = () => {
  const [selectedCustomerName, setSelectedCustomerName] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    customerId: '',
    amount: '15000',
    term: '36',
    purpose: 'PERS'
  })

  const [result, setResult] = useState<LoanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.customerId) {
      setError('Please select a customer first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await apiClient.assessLoan(
        formData.customerId,
        parseFloat(formData.amount),
        parseInt(formData.term),
        formData.purpose
      )

      if (res.return_code === '00') {
        setResult(res)
      } else if (res.return_code === '01') {
        setError('Customer not found')
      } else {
        setError('Assessment failed. Please try again.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const purposeOptions = [
    { value: 'PERS', label: 'Personal Loan' },
    { value: 'HOME', label: 'Home Loan' },
    { value: 'AUTO', label: 'Auto Loan' },
    { value: 'CONS', label: 'Consolidation' }
  ]

  return (
    <Page
      title="Loan Assessment"
      subtitle="Check loan eligibility and get personalized rates"
    >
      {/* Search Section */}
      <SearchWidget
        pageKey="loan"
        onSelect={(id, name) => {
          setSelectedCustomerName(name)
          setFormData(prev => ({ ...prev, customerId: id }))
        }}
      />

      <Grid columns={2} gap="lg">
        {/* Form Section */}
        <Card variant="default" className="loan-form-card">
          <h3>Loan Application</h3>

          {selectedCustomerName && (
            <div className="selected-customer">
              <p><strong>Customer:</strong> {selectedCustomerName}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="loan-form">

            <div className="form-group">
              <label>Loan Amount</label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                placeholder="15000"
                min="1000"
                max="500000"
                step="100"
              />
              <small>$1,000 - $500,000</small>
            </div>

            <div className="form-group">
              <label>Loan Term (Months)</label>
              <input
                type="number"
                name="term"
                value={formData.term}
                onChange={handleInputChange}
                placeholder="36"
                min="12"
                max="360"
                step="12"
              />
            </div>

            <div className="form-group">
              <label>Loan Purpose</label>
              <select name="purpose" value={formData.purpose} onChange={handleInputChange}>
                {purposeOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <Button type="submit" loading={loading} fullWidth>
              Get Assessment
            </Button>
          </form>

          {error && (
            <motion.div
              className="alert alert--danger"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {error}
            </motion.div>
          )}
        </Card>

        {/* Result Section */}
        <div>
          {result ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <StatusCard
                title="Assessment Complete"
                status={result.eligible === 'Y' ? 'approved' : 'declined'}
                details={[
                  { label: 'Credit Score', value: result.credit_score.toString() },
                  { label: 'Status', value: result.eligible === 'Y' ? 'Eligible' : 'Not Eligible' },
                  {
                    label: 'Interest Rate',
                    value: result.eligible === 'Y' ? `${result.interest_rate}%` : 'N/A'
                  },
                  {
                    label: 'Max Approved Amount',
                    value: result.eligible === 'Y' ? `$${result.max_amount.toLocaleString()}` : 'N/A'
                  }
                ]}
              />

              {result.eligible !== 'Y' && result.reject_reason && (
                <Card variant="default" className="reason-card">
                  <h4>Why You Weren't Approved</h4>
                  <p className="reason-text">{result.reject_reason}</p>
                </Card>
              )}
            </motion.div>
          ) : (
            <Card variant="minimal" className="empty-result">
              <div className="empty-state-icon">📋</div>
              <p>Submit an application to see results</p>
            </Card>
          )}
        </div>
      </Grid>

      {/* Information Section */}
      <Grid columns={3}>
        <Card variant="minimal">
          <h4>📊 Credit Score Ranges</h4>
          <div className="info-list">
            <div className="info-row">
              <span className="range-badge excellent">Excellent</span>
              <span>750-850</span>
            </div>
            <div className="info-row">
              <span className="range-badge good">Good</span>
              <span>670-749</span>
            </div>
            <div className="info-row">
              <span className="range-badge fair">Fair</span>
              <span>580-669</span>
            </div>
            <div className="info-row">
              <span className="range-badge poor">Poor</span>
              <span>300-579</span>
            </div>
          </div>
        </Card>

        <Card variant="minimal">
          <h4>💡 Interest Rate Factors</h4>
          <ul className="factor-list">
            <li>Credit Score (35%)</li>
            <li>Payment History (30%)</li>
            <li>Credit Utilization (20%)</li>
            <li>Loan Amount (10%)</li>
            <li>Term Length (5%)</li>
          </ul>
        </Card>

        <Card variant="minimal">
          <h4>✓ Approval Requirements</h4>
          <ul className="requirement-list">
            <li>Credit Score ≥ 650</li>
            <li>DTI Ratio &lt; 43%</li>
            <li>No Recent Defaults</li>
            <li>Active Account</li>
          </ul>
        </Card>
      </Grid>
    </Page>
  )
}
