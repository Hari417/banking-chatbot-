"""Mock bank API client for account and loan details."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


class BankAPIClient:
    """Client for interacting with internal banking APIs."""
    
    def __init__(self):
        """Initialize the bank API client with mock data."""
        self._mock_data = self._initialize_mock_data()
    
    def _initialize_mock_data(self) -> Dict:
        """Initialize mock customer data for demonstration."""
        return {
            "CUST001": {
                "customer_id": "CUST001",
                "name": "John Doe",
                "account_number": "ACC123456789",
                "account_balance": 125000.00,
                "loans": [
                    {
                        "loan_id": "LOAN001",
                        "loan_type": "Home Loan",
                        "principal_amount": 5000000.00,
                        "outstanding_amount": 4250000.00,
                        "interest_rate": 8.5,
                        "emi_amount": 42500.00,
                        "emi_date": 5,
                        "tenure_months": 240,
                        "remaining_months": 180,
                        "next_emi_date": self._get_next_emi_date(5),
                        "prepayment_allowed": True,
                        "prepayment_charges": 2.0,
                        "status": "active"
                    }
                ]
            },
            "CUST002": {
                "customer_id": "CUST002",
                "name": "Jane Smith",
                "account_number": "ACC987654321",
                "account_balance": 85000.00,
                "loans": [
                    {
                        "loan_id": "LOAN002",
                        "loan_type": "Personal Loan",
                        "principal_amount": 500000.00,
                        "outstanding_amount": 320000.00,
                        "interest_rate": 12.0,
                        "emi_amount": 15000.00,
                        "emi_date": 15,
                        "tenure_months": 48,
                        "remaining_months": 24,
                        "next_emi_date": self._get_next_emi_date(15),
                        "prepayment_allowed": True,
                        "prepayment_charges": 3.0,
                        "status": "active"
                    },
                    {
                        "loan_id": "LOAN003",
                        "loan_type": "Car Loan",
                        "principal_amount": 800000.00,
                        "outstanding_amount": 450000.00,
                        "interest_rate": 9.5,
                        "emi_amount": 18500.00,
                        "emi_date": 10,
                        "tenure_months": 60,
                        "remaining_months": 30,
                        "next_emi_date": self._get_next_emi_date(10),
                        "prepayment_allowed": True,
                        "prepayment_charges": 2.5,
                        "status": "active"
                    }
                ]
            }
        }
    
    def _get_next_emi_date(self, emi_date: int) -> str:
        """Calculate the next EMI date based on current date."""
        today = datetime.now()
        if today.day < emi_date:
            next_date = datetime(today.year, today.month, emi_date)
        else:
            # Move to next month
            if today.month == 12:
                next_date = datetime(today.year + 1, 1, emi_date)
            else:
                next_date = datetime(today.year, today.month + 1, emi_date)
        return next_date.strftime("%Y-%m-%d")
    
    def get_account_details(self, customer_id: str) -> Optional[Dict]:
        """
        Retrieve account details for a customer.
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            Dictionary containing account details or None if not found
        """
        customer = self._mock_data.get(customer_id)
        if not customer:
            return None
        
        return {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "account_number": customer["account_number"],
            "account_balance": customer["account_balance"]
        }
    
    def get_loan_details(self, customer_id: str, loan_id: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Retrieve loan details for a customer.
        
        Args:
            customer_id: Unique customer identifier
            loan_id: Optional specific loan ID to retrieve
            
        Returns:
            List of loan details or None if customer not found
        """
        customer = self._mock_data.get(customer_id)
        if not customer:
            return None
        
        loans = customer.get("loans", [])
        
        if loan_id:
            loans = [loan for loan in loans if loan["loan_id"] == loan_id]
        
        return loans if loans else None
    
    def get_all_customer_data(self, customer_id: str) -> Optional[Dict]:
        """
        Retrieve all data for a customer (account + loans).
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            Dictionary containing all customer data or None if not found
        """
        return self._mock_data.get(customer_id)
    
    def calculate_prepayment_amount(self, customer_id: str, loan_id: str, prepayment_amount: float) -> Optional[Dict]:
        """
        Calculate prepayment details including charges.
        
        Args:
            customer_id: Unique customer identifier
            loan_id: Loan identifier
            prepayment_amount: Amount to prepay
            
        Returns:
            Dictionary with prepayment calculation or None
        """
        loans = self.get_loan_details(customer_id, loan_id)
        if not loans:
            return None
        
        loan = loans[0]
        
        if not loan["prepayment_allowed"]:
            return {
                "allowed": False,
                "message": "Prepayment not allowed for this loan"
            }
        
        prepayment_charge = (prepayment_amount * loan["prepayment_charges"]) / 100
        total_amount = prepayment_amount + prepayment_charge
        new_outstanding = loan["outstanding_amount"] - prepayment_amount
        
        return {
            "allowed": True,
            "prepayment_amount": prepayment_amount,
            "prepayment_charge": prepayment_charge,
            "prepayment_charge_percentage": loan["prepayment_charges"],
            "total_amount_to_pay": total_amount,
            "current_outstanding": loan["outstanding_amount"],
            "new_outstanding": max(0, new_outstanding),
            "loan_type": loan["loan_type"]
        }
