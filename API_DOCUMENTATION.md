# Banking Chatbot API Documentation

## Base URL
```
http://localhost:5000
```

## Endpoints

### 1. Health Check
Check if the service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "banking-chatbot"
}
```

---

### 2. Chat
Process natural language queries about loans and EMIs.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "customer_id": "CUST001",
  "query": "What's my current EMI and can I prepay this month?"
}
```

**Response:**
```json
{
  "response": "Based on your loan details...",
  "success": true,
  "customer_id": "CUST001",
  "query": "...",
  "context_used": {
    "faqs_count": 3,
    "policies_count": 3
  }
}
```

**Example Queries:**
- "What is my current EMI?"
- "When is my next EMI due?"
- "Can I prepay my loan?"
- "What are the prepayment charges?"
- "What is my outstanding loan amount?"

---

### 3. Prepayment Calculator
Calculate prepayment amount with charges.

**Endpoint:** `POST /prepayment/calculate`

**Request Body:**
```json
{
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "prepayment_amount": 100000
}
```

**Response:**
```json
{
  "response": "Explanation of prepayment calculation...",
  "success": true,
  "calculation": {
    "allowed": true,
    "prepayment_amount": 100000.0,
    "prepayment_charge": 2000.0,
    "prepayment_charge_percentage": 2.0,
    "total_amount_to_pay": 102000.0,
    "current_outstanding": 4250000.0,
    "new_outstanding": 4150000.0,
    "loan_type": "Home Loan"
  }
}
```

---

### 4. Customer Summary
Get account and loan summary for a customer.

**Endpoint:** `GET /customer/{customer_id}/summary`

**Path Parameter:**
- `customer_id`: Customer identifier (e.g., "CUST001")

**Response:**
```json
{
  "customer_name": "John Doe",
  "account_number": "ACC123456789",
  "account_balance": 125000.00,
  "total_loans": 1,
  "loans": [
    {
      "loan_id": "LOAN001",
      "type": "Home Loan",
      "outstanding": 4250000.00,
      "emi": 42500.00,
      "next_emi_date": "2026-01-05"
    }
  ]
}
```

---

### 5. Search FAQs
Search loan FAQs using keyword matching.

**Endpoint:** `POST /search/faqs`

**Request Body:**
```json
{
  "query": "What is EMI?",
  "n_results": 3
}
```

**Response:**
```json
{
  "query": "What is EMI?",
  "results": [
    {
      "content": "Q: What is EMI?\nA: EMI stands for...",
      "metadata": {
        "question": "What is EMI?",
        "type": "faq"
      },
      "score": 1.0
    }
  ]
}
```

---

### 6. Search Policies
Search policy documents using keyword matching.

**Endpoint:** `POST /search/policies`

**Request Body:**
```json
{
  "query": "prepayment charges",
  "n_results": 3
}
```

**Response:**
```json
{
  "query": "prepayment charges",
  "results": [
    {
      "content": "Title: Home Loan Policy\nSection: Prepayment Terms\n...",
      "metadata": {
        "title": "Home Loan Policy",
        "section": "Prepayment Terms",
        "type": "policy"
      },
      "score": 1.0
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
Missing required fields or invalid input.

```json
{
  "error": "Missing required fields: customer_id and query"
}
```

### 404 Not Found
Customer not found.

```json
{
  "error": "Customer not found"
}
```

### 500 Internal Server Error
Server error.

```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

---

## Sample Customers

The system includes mock data for testing:

### CUST001 - John Doe
- Account: ACC123456789
- Balance: ₹125,000
- Loans: 1 Home Loan (LOAN001)

### CUST002 - Jane Smith
- Account: ACC987654321
- Balance: ₹85,000
- Loans: 1 Personal Loan (LOAN002), 1 Car Loan (LOAN003)

---

## cURL Examples

### Chat Query
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "query": "What is my current EMI?"
  }'
```

### Prepayment Calculation
```bash
curl -X POST http://localhost:5000/prepayment/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "loan_id": "LOAN001",
    "prepayment_amount": 100000
  }'
```

### Customer Summary
```bash
curl http://localhost:5000/customer/CUST001/summary
```

### Search FAQs
```bash
curl -X POST http://localhost:5000/search/faqs \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is EMI?",
    "n_results": 3
  }'
```

---

## Testing

Use the provided test script to test all endpoints:
```bash
./test_api.sh
```

Or run the example Python script:
```bash
python example.py
```
