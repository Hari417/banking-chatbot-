"""Prompt templates for the banking chatbot with strict system prompts."""

SYSTEM_PROMPT = """You are a professional banking support assistant for an established bank. Your role is to help existing customers manage their loans.

STRICT RULES YOU MUST FOLLOW:
1. ONLY answer questions related to loans, EMIs, prepayment, and account management
2. NEVER provide information about opening new accounts or applying for new loans
3. ALWAYS use the provided customer data and policy information in your response
4. NEVER make up information - only use data from the context provided
5. If information is not available in the context, clearly state that you don't have that information
6. ALWAYS be polite, professional, and concise
7. For numerical calculations, show the breakdown clearly
8. NEVER ask for sensitive information like passwords or OTPs
9. If a query is outside your scope, politely redirect to appropriate channels

YOUR CAPABILITIES:
- Answer questions about existing loans and EMIs
- Provide information about prepayment options and charges
- Explain loan policies and terms
- Help customers understand their account status
- Calculate prepayment amounts with charges

RESPONSE GUIDELINES:
- Use clear, simple language
- Be specific and accurate
- Provide actionable information
- Include relevant policy details when applicable
- Format numbers with proper currency symbols (₹)"""


def create_query_prompt(user_query: str, customer_data: dict, retrieved_context: dict) -> str:
    """
    Create a structured prompt for the LLM with retrieved context and customer data.
    
    Args:
        user_query: The user's natural language query
        customer_data: Customer account and loan data from API
        retrieved_context: Retrieved FAQs and policies from vector DB
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = []
    
    # Add context section
    prompt_parts.append("=== CONTEXT INFORMATION ===\n")
    
    # Add customer data if available
    if customer_data:
        prompt_parts.append("CUSTOMER DATA:")
        if "name" in customer_data:
            prompt_parts.append(f"Customer Name: {customer_data['name']}")
        if "account_number" in customer_data:
            prompt_parts.append(f"Account Number: {customer_data['account_number']}")
        if "account_balance" in customer_data:
            prompt_parts.append(f"Account Balance: ₹{customer_data['account_balance']:,.2f}")
        
        if "loans" in customer_data and customer_data["loans"]:
            prompt_parts.append("\nLOAN DETAILS:")
            for loan in customer_data["loans"]:
                prompt_parts.append(f"\nLoan ID: {loan['loan_id']}")
                prompt_parts.append(f"  Type: {loan['loan_type']}")
                prompt_parts.append(f"  Outstanding Amount: ₹{loan['outstanding_amount']:,.2f}")
                prompt_parts.append(f"  EMI Amount: ₹{loan['emi_amount']:,.2f}")
                prompt_parts.append(f"  EMI Date: {loan['emi_date']} of each month")
                prompt_parts.append(f"  Next EMI Date: {loan['next_emi_date']}")
                prompt_parts.append(f"  Interest Rate: {loan['interest_rate']}% p.a.")
                prompt_parts.append(f"  Remaining Months: {loan['remaining_months']}")
                prompt_parts.append(f"  Prepayment Allowed: {'Yes' if loan['prepayment_allowed'] else 'No'}")
                if loan['prepayment_allowed']:
                    prompt_parts.append(f"  Prepayment Charges: {loan['prepayment_charges']}%")
        
        prompt_parts.append("")
    
    # Add retrieved FAQs
    if retrieved_context.get("faqs"):
        prompt_parts.append("RELEVANT FAQs:")
        for i, faq in enumerate(retrieved_context["faqs"][:3], 1):
            prompt_parts.append(f"\nFAQ {i}:")
            prompt_parts.append(faq["content"])
        prompt_parts.append("")
    
    # Add retrieved policies
    if retrieved_context.get("policies"):
        prompt_parts.append("RELEVANT POLICIES:")
        for i, policy in enumerate(retrieved_context["policies"][:3], 1):
            prompt_parts.append(f"\nPolicy {i}:")
            prompt_parts.append(policy["content"])
        prompt_parts.append("")
    
    # Add the actual query
    prompt_parts.append("=== USER QUERY ===")
    prompt_parts.append(user_query)
    prompt_parts.append("")
    prompt_parts.append("=== INSTRUCTIONS ===")
    prompt_parts.append("Based on the context information provided above, answer the user's query accurately and professionally.")
    prompt_parts.append("Use ONLY the information from the context. If you need information not available in the context, clearly state that.")
    prompt_parts.append("Format your response in a clear, friendly manner suitable for a customer.")
    
    return "\n".join(prompt_parts)


def create_prepayment_calculation_prompt(loan_data: dict, prepayment_amount: float, calculation_result: dict) -> str:
    """
    Create a prompt for explaining prepayment calculations.
    
    Args:
        loan_data: Loan details
        prepayment_amount: Amount to prepay
        calculation_result: Prepayment calculation from API
        
    Returns:
        Formatted prompt for clear explanation
    """
    prompt_parts = []
    
    prompt_parts.append("=== PREPAYMENT CALCULATION ===\n")
    prompt_parts.append(f"Loan Type: {calculation_result['loan_type']}")
    prompt_parts.append(f"Prepayment Amount Requested: ₹{prepayment_amount:,.2f}")
    prompt_parts.append(f"\nBREAKDOWN:")
    prompt_parts.append(f"- Prepayment Amount: ₹{calculation_result['prepayment_amount']:,.2f}")
    prompt_parts.append(f"- Prepayment Charges ({calculation_result['prepayment_charge_percentage']}%): ₹{calculation_result['prepayment_charge']:,.2f}")
    prompt_parts.append(f"- Total Amount to Pay: ₹{calculation_result['total_amount_to_pay']:,.2f}")
    prompt_parts.append(f"\nIMPACT:")
    prompt_parts.append(f"- Current Outstanding: ₹{calculation_result['current_outstanding']:,.2f}")
    prompt_parts.append(f"- New Outstanding: ₹{calculation_result['new_outstanding']:,.2f}")
    prompt_parts.append(f"- Amount Reduced: ₹{calculation_result['current_outstanding'] - calculation_result['new_outstanding']:,.2f}")
    
    prompt_parts.append("\n=== INSTRUCTIONS ===")
    prompt_parts.append("Explain this prepayment calculation to the customer in a clear and friendly manner.")
    prompt_parts.append("Mention the benefits of prepayment and confirm if they would like to proceed.")
    
    return "\n".join(prompt_parts)


FALLBACK_RESPONSES = {
    "out_of_scope": "I apologize, but I can only assist with questions related to your existing loans, EMIs, and account management. For other banking services, please contact our customer care at 1800-XXX-XXXX or visit your nearest branch.",
    "no_customer_data": "I don't have access to your account information at the moment. Please ensure you're logged in or contact customer support for assistance.",
    "insufficient_context": "I don't have enough information to answer that question accurately. Could you please rephrase your question or contact our customer care at 1800-XXX-XXXX for detailed assistance?",
    "error": "I apologize, but I encountered an issue processing your request. Please try again or contact our customer support team."
}
