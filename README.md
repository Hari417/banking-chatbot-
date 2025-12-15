# Banking Chatbot

A banking support chatbot that helps existing customers manage their loans using LLMs, RAG (Retrieval-Augmented Generation), and internal APIs.

## Overview

This is a backend service that orchestrates:
- **LLM (Large Language Model)** - For natural language understanding and generation
- **Vector Database** - For RAG to retrieve loan FAQs and policy documents
- **Bank APIs** - To fetch account and loan details

Users can ask natural language questions like:
- "What's my current EMI and can I prepay this month?"
- "How much prepayment charges will I have to pay?"
- "When is my next EMI due?"

The system uses a **strict system prompt** and **structured templates** that inject retrieved policy snippets and API outputs to provide personalized, accurate answers.

## Features

### 🤖 Natural Language Processing
- Processes natural language queries about loans and EMIs
- Validates query scope to ensure only loan-related questions are answered
- Provides contextual, personalized responses

### 📚 RAG (Retrieval-Augmented Generation)
- Keyword-based semantic search for FAQs and policies (demo implementation)
- Retrieves relevant FAQs and policy documents
- Injects context into LLM prompts for accurate responses
- **Note**: Production systems should use ChromaDB or similar vector databases with proper embeddings

### 🏦 Bank API Integration
- Mock bank API client for account details
- Loan information retrieval
- Prepayment calculations with charges

### 🎯 Strict Prompt Engineering
- System prompts with clear boundaries
- Structured templates for consistency
- Context injection (policies + API data)
- Professional, accurate responses

## Architecture

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Banking Chatbot Service        │
│  ┌─────────────────────────────┐   │
│  │  Query Validation           │   │
│  └────────────┬────────────────┘   │
│               │                     │
│  ┌────────────▼────────────┐       │
│  │  Orchestration Layer    │       │
│  │  ┌──────┐  ┌──────┐    │       │
│  │  │ RAG  │  │ API  │    │       │
│  │  └───┬──┘  └───┬──┘    │       │
│  └──────┼─────────┼────────┘       │
│         │         │                 │
│  ┌──────▼──┐  ┌───▼────┐          │
│  │ Vector  │  │ Bank   │          │
│  │   DB    │  │  API   │          │
│  └─────────┘  └────────┘          │
│         │         │                 │
│  ┌──────▼─────────▼────────┐      │
│  │   Prompt Construction    │      │
│  └────────────┬─────────────┘      │
│               │                     │
│  ┌────────────▼─────────────┐      │
│  │    LLM (OpenAI GPT)      │      │
│  └────────────┬─────────────┘      │
│               │                     │
│  ┌────────────▼─────────────┐      │
│  │    Response Generation   │      │
│  └──────────────────────────┘      │
└─────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Hari417/banking-chatbot-.git
cd banking-chatbot-
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment (optional):
Create a `.env` file:
```env
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.1
FLASK_PORT=5000
```

**Note**: The system includes a demo mode that works without an OpenAI API key for testing purposes.

## Usage

### Running the Service

Start the Flask API server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

**Note**: The system includes a demo mode that works without an OpenAI API key. When no API key is configured, it uses rule-based responses for demonstration. For production use, configure a valid OpenAI API key in the `.env` file.

### Running the Example

To see a demonstration of the chatbot's capabilities:
```bash
python example.py
```

### API Endpoints

#### 1. Chat Endpoint
Process natural language queries:

```bash
POST /chat
Content-Type: application/json

{
  "customer_id": "CUST001",
  "query": "What's my current EMI and can I prepay this month?"
}
```

Response:
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

#### 2. Prepayment Calculator
Calculate prepayment with charges:

```bash
POST /prepayment/calculate
Content-Type: application/json

{
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "prepayment_amount": 100000
}
```

#### 3. Customer Summary
Get account and loan summary:

```bash
GET /customer/{customer_id}/summary
```

#### 4. Search FAQs
Search loan FAQs semantically:

```bash
POST /search/faqs
Content-Type: application/json

{
  "query": "What is EMI?",
  "n_results": 3
}
```

#### 5. Search Policies
Search policy documents:

```bash
POST /search/policies
Content-Type: application/json

{
  "query": "prepayment charges",
  "n_results": 3
}
```

### Testing the API

Use the provided test script:
```bash
chmod +x test_api.sh
./test_api.sh
```

## Project Structure

```
banking-chatbot-/
├── app.py                  # Flask API server
├── chatbot_service.py      # Main chatbot orchestration
├── llm_service.py          # LLM integration (OpenAI)
├── vector_db_service.py    # Vector DB for RAG (ChromaDB)
├── bank_api_client.py      # Mock bank API client
├── prompts.py              # Prompt templates and system prompts
├── data.py                 # Sample FAQs and policy documents
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── example.py              # Example usage
├── test_api.sh            # API test script
└── README.md              # This file
```

## How It Works

### 1. Query Processing Flow

1. **Validation**: Query is validated to ensure it's within scope (loan-related)
2. **Data Retrieval**: 
   - Customer data fetched from bank API
   - Relevant FAQs and policies retrieved from vector DB using semantic search
3. **Prompt Construction**: Structured prompt created with:
   - System prompt (strict rules and guidelines)
   - Customer data (account, loans, EMI details)
   - Retrieved context (FAQs and policies)
   - User query
4. **LLM Generation**: Prompt sent to LLM for response generation
5. **Response**: Personalized, contextual answer returned to user

### 2. Prompt Strategy

#### System Prompt
Contains strict rules:
- Only answer loan-related questions
- Never provide information about new accounts/loans
- Use only provided context
- Be professional and accurate
- Never ask for sensitive information

#### Structured Templates
Inject data in organized sections:
```
=== CONTEXT INFORMATION ===
CUSTOMER DATA: [Account and loan details]
RELEVANT FAQs: [Retrieved from vector DB]
RELEVANT POLICIES: [Retrieved from vector DB]

=== USER QUERY ===
[Natural language question]

=== INSTRUCTIONS ===
[Specific instructions for response format]
```

### 3. RAG Implementation

Uses keyword-based search for semantic matching (demo implementation):
- **FAQs Collection**: Common loan-related questions and answers
- **Policies Collection**: Bank policies for different loan types
- **Keyword Matching**: Finds relevant documents based on query keywords
- **Context Injection**: Top results injected into LLM prompt
- **Production Note**: For production systems, use ChromaDB or similar vector databases with proper embeddings

## Sample Data

The system includes mock data for demonstration:

### Customers
- **CUST001**: John Doe with 1 home loan
- **CUST002**: Jane Smith with 1 personal loan and 1 car loan

### FAQs
- What is EMI?
- How is EMI calculated?
- Can I prepay my loan?
- What are prepayment charges?
- And more...

### Policies
- Home Loan Policy (prepayment, interest rates)
- Personal Loan Policy (eligibility, prepayment)
- Car Loan Policy (loan amount, tenure)
- General Loan Policies (payments, charges)

## Customization

### Adding New FAQs/Policies
Edit `data.py` to add new FAQs or policy documents. The vector database will automatically index them.

### Changing LLM Provider
Modify `llm_service.py` to integrate with different LLM providers (Anthropic, local models, etc.)

### Integrating Real Bank APIs
Replace the mock `BankAPIClient` in `bank_api_client.py` with actual API integration.

## Security Considerations

- Never commits API keys to repository
- Validates query scope to prevent misuse
- Does not ask for sensitive information (passwords, OTPs)
- Mock data only for demonstration

## Future Enhancements

- [ ] Multi-turn conversation support with context memory
- [ ] Support for multiple languages
- [ ] Integration with real banking APIs
- [ ] User authentication and authorization
- [ ] Transaction history and analytics
- [ ] Voice interface support
- [ ] Advanced prepayment recommendations using ML

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.