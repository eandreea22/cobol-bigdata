import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 30000
    })
  }

  // Customer 360
  async getCustomer360(customerId: string) {
    const response = await this.client.get(`/customer-360/${customerId}`)
    return response.data
  }

  // Loan Assessment
  async assessLoan(customerId: string, amount: number, term: number, purpose: string) {
    const response = await this.client.post('/loan-assessment', {
      customer_id: customerId,
      amount,
      term_months: term,
      purpose_code: purpose
    })
    return response.data
  }

  // Fraud Detection
  async analyzeFraud(
    customerId: string,
    amount: number,
    mcc: string,
    location: string,
    timestamp: string,
    channel: string
  ) {
    const response = await this.client.post('/fraud-detection', {
      customer_id: customerId,
      amount,
      mcc,
      location,
      timestamp,
      channel
    })
    return response.data
  }

  // Batch Fraud Analysis
  async batchFraudAnalysis(customerId: string, limit?: number) {
    const response = await this.client.get(`/fraud-batch/${customerId}`, {
      params: { limit }
    })
    return response.data
  }

  // Customer List
  async getCustomers(search?: string, skip: number = 0, limit: number = 100) {
    const params: Record<string, any> = { skip, limit }
    if (search) params.search = search
    const response = await this.client.get('/customers', { params })
    return response.data
  }

  // Customer Details
  async getCustomerDetails(customerId: string) {
    const response = await this.client.get(`/customers/${customerId}`)
    return response.data
  }

  // Update Customer
  async updateCustomer(customerId: string, data: any) {
    const response = await this.client.put(`/customers/${customerId}`, data)
    return response.data
  }

  // Customer Transactions
  async getCustomerTransactions(customerId: string, limit?: number) {
    const response = await this.client.get(`/transactions/${customerId}`, {
      params: { limit }
    })
    return response.data
  }
}

export const apiClient = new APIClient()
