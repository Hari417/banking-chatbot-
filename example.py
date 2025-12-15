"""Example usage of the banking chatbot."""
from chatbot_service import BankingChatbot


def main():
    """Demonstrate chatbot functionality."""
    print("=" * 60)
    print("BANKING CHATBOT DEMO")
    print("=" * 60)
    
    # Initialize chatbot
    chatbot = BankingChatbot()
    
    # Example customer
    customer_id = "CUST001"
    
    # Example queries
    queries = [
        "What's my current EMI and can I prepay this month?",
        "What is EMI?",
        "How much prepayment charges will I have to pay?",
        "When is my next EMI due?",
        "What is my outstanding loan amount?"
    ]
    
    print(f"\nCustomer ID: {customer_id}\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'-' * 60}")
        print(f"Query {i}: {query}")
        print(f"{'-' * 60}")
        
        result = chatbot.process_query(customer_id, query)
        
        if result.get("success"):
            print(f"\nResponse:\n{result['response']}")
            
            if result.get("context_used"):
                context = result["context_used"]
                print(f"\n[Context used: {context['faqs_count']} FAQs, {context['policies_count']} policies]")
        else:
            print(f"\nError: {result.get('response', 'Unknown error')}")
    
    # Demonstrate prepayment calculation
    print(f"\n\n{'=' * 60}")
    print("PREPAYMENT CALCULATION DEMO")
    print(f"{'=' * 60}")
    
    loan_id = "LOAN001"
    prepayment_amount = 100000.00
    
    print(f"\nCalculating prepayment for Loan ID: {loan_id}")
    print(f"Prepayment Amount: ₹{prepayment_amount:,.2f}\n")
    
    result = chatbot.calculate_prepayment(customer_id, loan_id, prepayment_amount)
    
    if result.get("success"):
        print(f"Response:\n{result['response']}")
        
        if result.get("calculation"):
            calc = result["calculation"]
            print(f"\n[Detailed Calculation]")
            print(f"Total to Pay: ₹{calc['total_amount_to_pay']:,.2f}")
            print(f"New Outstanding: ₹{calc['new_outstanding']:,.2f}")
    else:
        print(f"Error: {result.get('response', 'Unknown error')}")
    
    # Get customer summary
    print(f"\n\n{'=' * 60}")
    print("CUSTOMER SUMMARY")
    print(f"{'=' * 60}\n")
    
    summary = chatbot.get_customer_summary(customer_id)
    
    if summary:
        print(f"Name: {summary['customer_name']}")
        print(f"Account Number: {summary['account_number']}")
        print(f"Account Balance: ₹{summary['account_balance']:,.2f}")
        print(f"\nTotal Loans: {summary['total_loans']}")
        
        for loan in summary['loans']:
            print(f"\n  {loan['type']} ({loan['loan_id']})")
            print(f"    Outstanding: ₹{loan['outstanding']:,.2f}")
            print(f"    EMI: ₹{loan['emi']:,.2f}")
            print(f"    Next EMI Date: {loan['next_emi_date']}")
    
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
