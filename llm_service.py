"""LLM service for orchestrating responses using OpenAI."""
from typing import Dict, Optional
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import config
from prompts import SYSTEM_PROMPT, FALLBACK_RESPONSES


class LLMService:
    """Service for interacting with LLM (OpenAI GPT)."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.model = config.LLM_MODEL
        self.temperature = config.LLM_TEMPERATURE
        self.client = None
        
        if OPENAI_AVAILABLE and config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your-api-key-here":
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                print(f"OpenAI initialization warning: {str(e)}")
                self.client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The formatted prompt with context
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        if not self.client:
            return self._create_demo_response(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            return self._create_demo_response(prompt)
    
    def _create_demo_response(self, prompt: str) -> str:
        """
        Create a demo response when OpenAI API is not available.
        This is useful for demonstration without a real API key.
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            Demo response
        """
        # Extract key information from prompt
        if "EMI" in prompt and "prepay" in prompt.lower():
            return """Based on your loan details, here's the information about your EMI and prepayment:

**Current EMI Details:**
Your current EMI is being paid regularly. Please refer to the loan details shown above for specific amounts.

**Prepayment Information:**
Yes, you can prepay your loan this month. Here's what you need to know:
- Prepayment is allowed for your loan type
- Prepayment charges will apply as per your loan terms (typically 2-3% for home loans)
- You can make prepayment through online banking, mobile app, or branch visit
- Minimum prepayment amount requirements apply

**Next Steps:**
If you'd like to proceed with prepayment, please specify the amount you wish to prepay, and I can calculate the exact charges and new outstanding amount for you.

Is there anything specific about prepayment you'd like to know more about?"""
        
        elif "prepayment" in prompt.lower() or "prepay" in prompt.lower():
            return """**Prepayment Information:**

Prepayment allows you to pay off your loan faster and save on interest. Here are the key points:

- **Eligibility**: Most loans allow prepayment after a certain period
- **Charges**: Prepayment charges typically range from 2-5% depending on loan type
- **Benefits**: Reduces total interest paid and loan tenure
- **Process**: Can be done through online banking, mobile app, or branch

For your specific loan, please check the loan details section for exact prepayment charge percentage and terms.

Would you like me to calculate the prepayment amount for a specific sum?"""
        
        elif "EMI" in prompt:
            return """**EMI Information:**

Your EMI (Equated Monthly Installment) details are shown in the loan information above. 

Key points about EMI:
- EMI includes both principal and interest components
- Due date is fixed each month as per your loan agreement
- Auto-debit is the recommended payment method to avoid missing payments
- Late payments attract penalties and affect credit score

If you need any specific information about your EMI or want to make changes, please let me know!"""
        
        else:
            return """Thank you for your query. I'm here to help you with your loan and account management.

Based on the information available, I can assist you with:
- EMI details and payment schedules
- Loan outstanding amounts and tenure
- Prepayment options and calculations
- Policy information about your loans
- Account balance and transaction details

Please feel free to ask specific questions about your loans or account!"""
    
    def validate_query_scope(self, query: str) -> Dict[str, any]:
        """
        Validate if the query is within the chatbot's scope.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with validation result
        """
        query_lower = query.lower()
        
        # Out of scope keywords
        out_of_scope = [
            "new account", "open account", "new loan application",
            "credit card", "debit card", "apply for",
            "password", "otp", "pin"
        ]
        
        # In scope keywords
        in_scope = [
            "emi", "loan", "prepay", "prepayment", "outstanding",
            "balance", "account", "payment", "interest", "tenure"
        ]
        
        # Check for out of scope
        for keyword in out_of_scope:
            if keyword in query_lower:
                return {
                    "in_scope": False,
                    "reason": "out_of_scope",
                    "message": FALLBACK_RESPONSES["out_of_scope"]
                }
        
        # Check for in scope
        for keyword in in_scope:
            if keyword in query_lower:
                return {
                    "in_scope": True,
                    "confidence": "high"
                }
        
        # Uncertain queries - allow but with lower confidence
        return {
            "in_scope": True,
            "confidence": "low"
        }
