"""Main chatbot service that orchestrates LLM, RAG, and bank APIs."""
from typing import Dict, Optional
from bank_api_client import BankAPIClient
from vector_db_service import VectorDBService
from llm_service import LLMService
from prompts import create_query_prompt, create_prepayment_calculation_prompt, FALLBACK_RESPONSES


class BankingChatbot:
    """
    Main chatbot service that orchestrates:
    - LLM for natural language understanding and generation
    - Vector DB for RAG (retrieving FAQs and policies)
    - Bank APIs for customer data
    """
    
    def __init__(self):
        """Initialize the chatbot with all required services."""
        self.bank_api = BankAPIClient()
        self.vector_db = VectorDBService()
        self.llm = LLMService()
    
    def process_query(self, customer_id: str, query: str) -> Dict:
        """
        Process a user query with full orchestration.
        
        Args:
            customer_id: Customer identifier
            query: Natural language query from user
            
        Returns:
            Dictionary with response and metadata
        """
        # Step 1: Validate query scope
        validation = self.llm.validate_query_scope(query)
        if not validation.get("in_scope", True):
            return {
                "response": validation.get("message", FALLBACK_RESPONSES["out_of_scope"]),
                "success": False,
                "reason": validation.get("reason")
            }
        
        # Step 2: Retrieve customer data from bank API
        customer_data = self.bank_api.get_all_customer_data(customer_id)
        if not customer_data:
            return {
                "response": FALLBACK_RESPONSES["no_customer_data"],
                "success": False,
                "reason": "customer_not_found"
            }
        
        # Step 3: Retrieve relevant context from vector DB (RAG)
        retrieved_context = self.vector_db.search_all(query, n_results=6)
        
        # Step 4: Check if this is a prepayment calculation request
        if self._is_prepayment_calculation_query(query):
            return self._handle_prepayment_query(customer_id, query, customer_data)
        
        # Step 5: Create structured prompt with all context
        prompt = create_query_prompt(query, customer_data, retrieved_context)
        
        # Step 6: Generate response using LLM
        response = self.llm.generate_response(prompt)
        
        return {
            "response": response,
            "success": True,
            "customer_id": customer_id,
            "query": query,
            "context_used": {
                "faqs_count": len(retrieved_context.get("faqs", [])),
                "policies_count": len(retrieved_context.get("policies", []))
            }
        }
    
    def _is_prepayment_calculation_query(self, query: str) -> bool:
        """Check if query is asking for prepayment calculation."""
        query_lower = query.lower()
        calculation_keywords = ["calculate", "how much", "amount"]
        prepayment_keywords = ["prepay", "prepayment", "foreclose"]
        
        has_calculation = any(kw in query_lower for kw in calculation_keywords)
        has_prepayment = any(kw in query_lower for kw in prepayment_keywords)
        
        return has_calculation and has_prepayment
    
    def _handle_prepayment_query(self, customer_id: str, query: str, customer_data: Dict) -> Dict:
        """Handle prepayment calculation queries."""
        # For now, return guidance on prepayment
        # In a real system, this would extract the amount from query
        loans = customer_data.get("loans", [])
        if not loans:
            return {
                "response": "You don't have any active loans for prepayment.",
                "success": False
            }
        
        loan = loans[0]  # Use first loan for demo
        response = f"""To calculate prepayment for your {loan['loan_type']}, I need the prepayment amount.

**Your Current Loan Details:**
- Outstanding Amount: ₹{loan['outstanding_amount']:,.2f}
- Prepayment Allowed: {'Yes' if loan['prepayment_allowed'] else 'No'}
- Prepayment Charges: {loan['prepayment_charges']}%

Please specify the amount you'd like to prepay, and I'll calculate the total amount including charges."""
        
        return {
            "response": response,
            "success": True,
            "action_required": "specify_prepayment_amount"
        }
    
    def calculate_prepayment(self, customer_id: str, loan_id: str, prepayment_amount: float) -> Dict:
        """
        Calculate prepayment with charges.
        
        Args:
            customer_id: Customer identifier
            loan_id: Loan identifier
            prepayment_amount: Amount to prepay
            
        Returns:
            Dictionary with calculation and explanation
        """
        # Get calculation from bank API
        calculation = self.bank_api.calculate_prepayment_amount(
            customer_id, loan_id, prepayment_amount
        )
        
        if not calculation:
            return {
                "response": "Unable to calculate prepayment. Please check your loan details.",
                "success": False
            }
        
        if not calculation.get("allowed"):
            return {
                "response": calculation.get("message"),
                "success": False
            }
        
        # Get loan data for context
        loans = self.bank_api.get_loan_details(customer_id, loan_id)
        loan_data = loans[0] if loans else {}
        
        # Create prompt for explanation
        prompt = create_prepayment_calculation_prompt(loan_data, prepayment_amount, calculation)
        
        # Generate friendly explanation
        response = self.llm.generate_response(prompt, max_tokens=400)
        
        return {
            "response": response,
            "success": True,
            "calculation": calculation
        }
    
    def get_customer_summary(self, customer_id: str) -> Optional[Dict]:
        """
        Get a summary of customer's account and loans.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Dictionary with customer summary
        """
        customer_data = self.bank_api.get_all_customer_data(customer_id)
        if not customer_data:
            return None
        
        summary = {
            "customer_name": customer_data["name"],
            "account_number": customer_data["account_number"],
            "account_balance": customer_data["account_balance"],
            "total_loans": len(customer_data.get("loans", [])),
            "loans": []
        }
        
        for loan in customer_data.get("loans", []):
            summary["loans"].append({
                "loan_id": loan["loan_id"],
                "type": loan["loan_type"],
                "outstanding": loan["outstanding_amount"],
                "emi": loan["emi_amount"],
                "next_emi_date": loan["next_emi_date"]
            })
        
        return summary
