#!/bin/bash

# Test script for the Banking Chatbot API

echo "========================================"
echo "Banking Chatbot API Test Script"
echo "========================================"
echo ""

BASE_URL="http://localhost:5000"

# Check if server is running
echo "1. Health Check"
echo "----------------------------------------"
curl -X GET "$BASE_URL/health" -H "Content-Type: application/json"
echo -e "\n"

# Test chat endpoint
echo "2. Chat Query - EMI and Prepayment"
echo "----------------------------------------"
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "query": "What is my current EMI and can I prepay this month?"
  }'
echo -e "\n\n"

# Test chat endpoint - FAQ query
echo "3. Chat Query - What is EMI"
echo "----------------------------------------"
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "query": "What is EMI?"
  }'
echo -e "\n\n"

# Test prepayment calculation
echo "4. Prepayment Calculation"
echo "----------------------------------------"
curl -X POST "$BASE_URL/prepayment/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "loan_id": "LOAN001",
    "prepayment_amount": 100000
  }'
echo -e "\n\n"

# Test customer summary
echo "5. Customer Summary"
echo "----------------------------------------"
curl -X GET "$BASE_URL/customer/CUST001/summary" \
  -H "Content-Type: application/json"
echo -e "\n\n"

# Test FAQ search
echo "6. Search FAQs"
echo "----------------------------------------"
curl -X POST "$BASE_URL/search/faqs" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is prepayment?",
    "n_results": 2
  }'
echo -e "\n\n"

# Test policy search
echo "7. Search Policies"
echo "----------------------------------------"
curl -X POST "$BASE_URL/search/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "prepayment charges for home loan",
    "n_results": 2
  }'
echo -e "\n\n"

echo "========================================"
echo "Test completed!"
echo "========================================"
