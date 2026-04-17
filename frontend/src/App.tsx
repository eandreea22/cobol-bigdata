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

  const sidebarItems = [
    { id: 'dashboard', label: 'Customer 360°', icon: '👤' },
    { id: 'loans', label: 'Loan Assessment', icon: '💰' },
    { id: 'fraud', label: 'Fraud Detection', icon: '🚨' },
    { id: 'customers', label: 'Management', icon: '📊' }
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'loans':
        return <LoanAssessment />
      case 'fraud':
        return <FraudDetection />
      case 'customers':
        return <CustomerManagement />
      default:
        return <Dashboard />
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
