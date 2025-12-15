# Banking Chatbot - Quick Start Guide

This guide will help you get started with the Banking Chatbot in minutes.

## Quick Demo

### 1. Run the Example Script

The fastest way to see the chatbot in action:

```bash
python example.py
```

This will demonstrate:
- Multiple natural language queries
- Prepayment calculations
- Customer summary retrieval
- Context retrieval from FAQs and policies

**Expected Output:**
```
============================================================
BANKING CHATBOT DEMO
============================================================

Customer ID: CUST001

------------------------------------------------------------
Query 1: What's my current EMI and can I prepay this month?
------------------------------------------------------------

Response:
Based on your loan details, here's the information about your EMI and prepayment:
...
```

### 2. Start the API Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Test with cURL

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Ask a Question:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "query": "What is my current EMI?"
  }'
```

**Get Customer Summary:**
```bash
curl http://localhost:5000/customer/CUST001/summary
```

**Calculate Prepayment:**
```bash
curl -X POST http://localhost:5000/prepayment/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "loan_id": "LOAN001",
    "prepayment_amount": 100000
  }'
```

### 4. Run All API Tests

```bash
./test_api.sh
```

## Understanding the System

### Components

1. **LLM Service** (`llm_service.py`)
   - Handles LLM integration (OpenAI)
   - Includes demo mode for testing without API key
   - Validates query scope

2. **Vector DB Service** (`vector_db_service.py`)
   - Keyword-based search for FAQs and policies
   - RAG implementation for context retrieval

3. **Bank API Client** (`bank_api_client.py`)
   - Mock banking API with sample customer data
   - Account and loan information
   - Prepayment calculations

4. **Chatbot Service** (`chatbot_service.py`)
   - Main orchestration layer
   - Combines LLM, RAG, and bank APIs
   - Processes queries end-to-end

5. **Prompts** (`prompts.py`)
   - Strict system prompts
   - Structured templates
   - Context injection logic

## How It Works

### Query Flow

1. **User Query**: "What's my current EMI and can I prepay this month?"

2. **Validation**: System checks if query is loan-related

3. **Data Retrieval**:
   - Fetch customer data from Bank API
   - Search FAQs for relevant information
   - Search policies for prepayment rules

4. **Prompt Construction**:
   ```
   === CONTEXT INFORMATION ===
   CUSTOMER DATA:
   - Name: John Doe
   - Account Balance: ₹125,000
   - Loan Details: Home Loan, EMI ₹42,500...
   
   RELEVANT FAQs:
   - What is EMI?
   - Can I prepay my loan?
   
   RELEVANT POLICIES:
   - Home Loan Prepayment Terms
   
   === USER QUERY ===
   What's my current EMI and can I prepay this month?
   ```

5. **LLM Generation**: OpenAI generates response based on context

6. **Response**: Personalized answer with all relevant information

### Prompt Strategy

The system uses **strict system prompts** to ensure:
- Only loan-related queries are answered
- No sensitive information is requested
- Responses are accurate and based on provided context
- Professional tone is maintained

**System Prompt Rules:**
```
1. ONLY answer questions related to loans, EMIs, prepayment
2. NEVER provide info about new accounts/loans
3. ALWAYS use provided customer data and policies
4. NEVER make up information
5. Be polite, professional, and concise
```

## Sample Queries

Try these queries with the chatbot:

### Basic Information
- "What is EMI?"
- "What is my account balance?"
- "How many loans do I have?"

### Loan Details
- "What is my current EMI?"
- "When is my next EMI due?"
- "What is my outstanding loan amount?"
- "What is the interest rate on my loan?"

### Prepayment
- "Can I prepay my loan?"
- "What are the prepayment charges?"
- "Calculate prepayment for ₹100,000"
- "How much will I save with prepayment?"

### Policies
- "What is your prepayment policy?"
- "What happens if I miss an EMI payment?"
- "How can I make EMI payments?"

## Mock Data

The system includes two sample customers:

### CUST001 - John Doe
```
Account: ACC123456789
Balance: ₹125,000

Loan: LOAN001 (Home Loan)
- Outstanding: ₹42,50,000
- EMI: ₹42,500
- EMI Date: 5th of each month
- Interest: 8.5% p.a.
- Prepayment: Allowed (2% charges)
```

### CUST002 - Jane Smith
```
Account: ACC987654321
Balance: ₹85,000

Loan 1: LOAN002 (Personal Loan)
- Outstanding: ₹3,20,000
- EMI: ₹15,000
- EMI Date: 15th of each month
- Interest: 12.0% p.a.

Loan 2: LOAN003 (Car Loan)
- Outstanding: ₹4,50,000
- EMI: ₹18,500
- EMI Date: 10th of each month
- Interest: 9.5% p.a.
```

## Demo Mode vs Production

### Demo Mode (Default)
- Works without OpenAI API key
- Uses rule-based responses
- Perfect for testing and demonstration
- All features except actual LLM generation work

### Production Mode
1. Get OpenAI API key from https://platform.openai.com/
2. Create `.env` file:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart the server
4. Now uses actual GPT for better responses

## Next Steps

1. **Customize Data**: Edit `data.py` to add your FAQs and policies
2. **Integrate Real APIs**: Replace mock client in `bank_api_client.py`
3. **Add Authentication**: Implement user authentication
4. **Deploy**: Use Gunicorn/uWSGI for production deployment
5. **Monitor**: Add logging and monitoring

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env or:
FLASK_PORT=5001 python app.py
```

### Dependencies Issue
```bash
pip install -r requirements.txt
```

### OpenAI API Errors
The system automatically falls back to demo mode if OpenAI is unavailable.

## Additional Resources

- [API Documentation](API_DOCUMENTATION.md)
- [Main README](README.md)
- OpenAI API: https://platform.openai.com/docs
