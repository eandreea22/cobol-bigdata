# User Interface Guide

## Streamlit UI (ui/app.py)

### Overview
1,300-line analytical dashboard with 4 pages. Design: dark mode (navy + cyan), Epilogue font.

### Pages

**1. Customer 360°**
- Search: Name-based lookup with dropdown
- Display: Profile card + risk badge + 4 metric cards (balance, transactions, avg monthly, risk score) + Activity summary + Risk meter
- Data source: customer_360.py (IPC bridge to COBOL)

**2. Loan Assessment**
- Search: Name-based lookup
- Form: Loan amount, term months, purpose dropdown
- Display: Decision card (approved/declined) + Credit score + Interest rate + Max approved amount
- Data source: loan_scoring.py

**3. Fraud Detection**
- Search: Name-based lookup
- Filters: Channel multiselect, amount range slider, search text
- Display: Flagged transaction count + Avg risk score + Status (Safe/Review) + Full transaction table with fraud risk badges
- Data source: fraud_batch_analysis.py

**4. Customer Management**
- Paginated editable dataframe (100 rows per page)
- Columns: customer_id, name, email, city, street, balance, income
- Edit: Click row, modify fields, "Save Changes" button
- Data source: customer_list.py + customer_update.py

### Design System
- **Colors:** Navy #0f172a (background) + Cyan #00d4ff (accent)
- **Font:** Epilogue sans-serif
- **Layout:** Full-width cards with metric badges
- **Animations:** None (pure Python, no JS)
- **Responsive:** Desktop only (no mobile)

### Running Streamlit
```bash
streamlit run ui/app.py  # Opens http://localhost:8501
```

---

## React UI (frontend/)

### Overview
React 18.2 + TypeScript + Vite, 4 pages mirroring Streamlit functionality.

### Pages

**1. Dashboard (Customer 360°)**
- SearchWidget: Reusable name search component
- Display: Profile header (avatar initial + name + risk badge) + 4 MetricCards + 2 detail cards
- Auto-fetch on customer selection (no additional button click)
- Data source: GET /customer-360/{customer_id}

**2. LoanAssessment**
- SearchWidget: Name search
- Form: Amount, term months, purpose dropdown, "Get Assessment" button
- Display: StatusCard (approved/declined) + metrics
- Data source: POST /loan-assessment

**3. FraudDetection**
- SearchWidget: Name search
- Auto-fetches all transactions on selection
- Filters: Risk level tabs (ALL/LOW/MEDIUM/HIGH)
- Table: txn_id, amount, location, category, risk badge, score, date
- Data source: GET /fraud-batch/{customer_id}

**4. CustomerManagement**
- Auto-loads 100 customers on mount (no search needed on open)
- Two-column: Customer list (left) + detail panel (right)
- Detail: View mode shows customer info; edit mode shows form
- Buttons: "View 360° Profile" → navigate to Dashboard with pre-selected customer
- Data sources: GET /customers, PUT /customers/{customer_id}

### Key Component: SearchWidget

**Props:**
```tsx
interface SearchWidgetProps {
  onSelect: (customerId: string, customerName: string) => void
  pageKey: string  // Prevents state collision on multi-page use
}
```

**Behavior:**
1. Text input + "Search" button
2. Calls `GET /customers?search=...`
3. Displays dropdown with matching customers
4. Click → calls `onSelect(id, name)`
5. Shows selected customer badge + "Change" button to reset

### Stack
- **Framework:** React 18.2
- **Language:** TypeScript 5.3
- **Build:** Vite (dev: port 3002)
- **HTTP:** Axios with 30s timeout
- **Animation:** Framer Motion
- **Classes:** clsx for conditional styling

### Cross-Page Navigation Pattern
```tsx
// In App.tsx
const [preSelectedCustomerId, setPreSelectedCustomerId] = useState(null)

// CustomerManagement: Click "View 360° Profile"
<Button onClick={() => {
  setPreSelectedCustomerId(customer.customer_id)
  setCurrentPage('dashboard')
}} />

// Dashboard: useEffect watches preSelectedCustomerId
useEffect(() => {
  if (preSelectedCustomerId) {
    handleFetch(preSelectedCustomerId)
    onCustomerSelected?.()  // Clear after use
  }
}, [preSelectedCustomerId])
```

### Running React
```bash
cd frontend && npm install && npm run dev  # Opens http://localhost:3000
```

---

## Comparing the Two UIs

| Aspect | Streamlit | React |
|--------|-----------|-------|
| **Best for** | Rapid iteration, algorithm exploration | Production, user-facing analytics |
| **Interactivity** | High (sliders, multiselect native) | High (optimized responsiveness) |
| **Customization** | Limited (Streamlit components only) | Unlimited (custom React components) |
| **Performance** | Good for analytical queries | Excellent for user experience |
| **Accessibility** | Basic | Professional (ARIA, keyboard nav) |
| **Mobile** | Not supported | Responsive design ready |
| **Learning curve** | Very low (Python-only) | Moderate (React + TypeScript) |

---

## Running Both UIs Simultaneously

```bash
# Terminal 1: Backend API
cd backend && python main.py  # http://localhost:8000

# Terminal 2: Streamlit
streamlit run ui/app.py  # http://localhost:8501

# Terminal 3: React
cd frontend && npm run dev  # http://localhost:3000

# Now:
# - Test Streamlit at localhost:8501
# - Test React at localhost:3000
# - Both connect to same backend API at localhost:8000
```

---

**Last Updated:** 2026-04-17
