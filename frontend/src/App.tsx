import React, { useState } from 'react'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { LoanAssessment } from './pages/LoanAssessment'
import { FraudDetection } from './pages/FraudDetection'
import { CustomerManagement } from './pages/CustomerManagement'
import './styles/globals.css'

type PageId = 'dashboard' | 'loans' | 'fraud' | 'customers'

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard')
  const [preSelectedCustomerId, setPreSelectedCustomerId] = useState<string | null>(null)

  const sidebarItems = [
    { id: 'dashboard', label: 'Customer 360°', icon: '👤' },
    { id: 'loans', label: 'Loan Assessment', icon: '💰' },
    { id: 'fraud', label: 'Fraud Detection', icon: '🚨' },
    { id: 'customers', label: 'Management', icon: '📊' }
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <Dashboard
            preSelectedCustomerId={preSelectedCustomerId}
            onCustomerSelected={() => setPreSelectedCustomerId(null)}
          />
        )
      case 'loans':
        return <LoanAssessment />
      case 'fraud':
        return (
          <FraudDetection
            preSelectedCustomerId={preSelectedCustomerId}
            onCustomerSelected={() => setPreSelectedCustomerId(null)}
          />
        )
      case 'customers':
        return (
          <CustomerManagement
            onNavigateToDashboard={(customerId) => {
              setPreSelectedCustomerId(customerId)
              setCurrentPage('dashboard')
            }}
            onNavigateToFraud={(customerId) => {
              setPreSelectedCustomerId(customerId)
              setCurrentPage('fraud')
            }}
          />
        )
      default:
        return <Dashboard preSelectedCustomerId={preSelectedCustomerId} onCustomerSelected={() => setPreSelectedCustomerId(null)} />
    }
  }

  return (
    <Layout
      sidebarItems={sidebarItems}
      currentPage={currentPage}
      onNavigate={(pageId) => setCurrentPage(pageId as PageId)}
    >
      {renderPage()}
    </Layout>
  )
}

export default App
