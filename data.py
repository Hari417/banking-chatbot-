"""Sample data for loan FAQs and policy documents."""

LOAN_FAQS = [
    {
        "question": "What is EMI?",
        "answer": "EMI stands for Equated Monthly Installment. It is a fixed payment amount made by a borrower to a lender at a specified date each calendar month. EMIs are used to pay off both interest and principal each month, so that over a specified number of years, the loan is paid off in full."
    },
    {
        "question": "How is EMI calculated?",
        "answer": "EMI is calculated using the formula: EMI = [P x R x (1+R)^N]/[(1+R)^N-1], where P = Principal loan amount, R = Monthly interest rate (annual rate/12/100), N = Loan tenure in months. The EMI includes both principal and interest components."
    },
    {
        "question": "Can I prepay my loan?",
        "answer": "Yes, most loans allow prepayment. However, prepayment charges may apply depending on your loan type and terms. Home loans typically have 2-3% prepayment charges, personal loans have 3-5%, and car loans have 2.5-4%. Check your loan agreement for specific terms."
    },
    {
        "question": "What are prepayment charges?",
        "answer": "Prepayment charges are fees charged by the lender when you pay off your loan before the agreed tenure. These charges typically range from 2% to 5% of the outstanding principal amount, depending on the loan type and terms."
    },
    {
        "question": "When is my EMI due date?",
        "answer": "Your EMI due date is specified in your loan agreement. It's typically a fixed date each month (e.g., 5th, 10th, or 15th). You can find your specific EMI date in your loan details or account statement."
    },
    {
        "question": "What happens if I miss an EMI payment?",
        "answer": "Missing an EMI payment can have serious consequences: 1) Late payment charges will be applied (typically 2% of EMI amount), 2) Your credit score will be negatively impacted, 3) You may receive penalty notices, 4) After 90 days of non-payment, the loan may be classified as NPA (Non-Performing Asset)."
    },
    {
        "question": "Can I increase my EMI amount?",
        "answer": "Yes, you can increase your EMI amount to pay off your loan faster. This helps reduce the total interest paid over the loan tenure. Contact your bank to modify your EMI amount. There are usually no charges for increasing EMI."
    },
    {
        "question": "What is the difference between principal and interest?",
        "answer": "Principal is the original loan amount you borrowed, while interest is the cost of borrowing that money. Your EMI contains both components. Early in the loan tenure, a larger portion goes toward interest, while later, more goes toward principal."
    },
    {
        "question": "Can I get a loan statement?",
        "answer": "Yes, you can request a loan statement anytime through online banking, mobile app, or by visiting a branch. The statement shows all transactions, EMI payments, outstanding balance, and other loan details."
    },
    {
        "question": "What is loan tenure?",
        "answer": "Loan tenure is the time period over which you agree to repay the loan. It's typically measured in months or years. Longer tenure means lower EMI but higher total interest, while shorter tenure means higher EMI but lower total interest."
    }
]

POLICY_DOCUMENTS = [
    {
        "title": "Home Loan Policy",
        "section": "Prepayment Terms",
        "content": "Home loan customers can prepay their outstanding loan amount at any time. Prepayment charges of 2% of the outstanding principal apply for loans less than 3 years old. No prepayment charges apply for loans older than 3 years. Minimum prepayment amount is Rs. 10,000. Prepayment can be done through online banking, mobile app, or branch visit."
    },
    {
        "title": "Home Loan Policy",
        "section": "Interest Rate",
        "content": "Home loan interest rates range from 8.0% to 10.5% per annum, depending on the loan amount, tenure, and customer profile. Interest rates are subject to change based on RBI policy and bank's internal assessment. Customers can choose between fixed and floating interest rates."
    },
    {
        "title": "Personal Loan Policy",
        "section": "Prepayment Terms",
        "content": "Personal loan prepayment is allowed after 6 months from loan disbursement. Prepayment charges of 3% to 5% of the outstanding principal apply. Full foreclosure is permitted with appropriate charges. Partial prepayment minimum amount is Rs. 5,000."
    },
    {
        "title": "Personal Loan Policy",
        "section": "Eligibility",
        "content": "Personal loans are available to salaried and self-employed individuals aged 21-60 years. Minimum income requirement is Rs. 25,000 per month for salaried and Rs. 3 lakhs annual income for self-employed. Credit score of 750 or above preferred."
    },
    {
        "title": "Car Loan Policy",
        "section": "Prepayment Terms",
        "content": "Car loan prepayment charges are 2.5% of outstanding principal for loans less than 2 years old. No charges after 2 years. Minimum prepayment amount is Rs. 10,000. Full foreclosure allowed with 12 months notice or applicable charges."
    },
    {
        "title": "Car Loan Policy",
        "section": "Loan Amount and Tenure",
        "content": "Car loans are available for up to 90% of the vehicle's on-road price. Maximum loan amount is Rs. 50 lakhs. Tenure ranges from 12 to 84 months. Interest rates start from 9.0% per annum."
    },
    {
        "title": "General Loan Policy",
        "section": "EMI Payment Methods",
        "content": "EMI payments can be made through: 1) Auto-debit from savings account (recommended), 2) Online payment through internet banking, 3) Mobile app payment, 4) NEFT/RTGS, 5) Branch payment. Ensure sufficient balance on EMI due date to avoid late payment charges."
    },
    {
        "title": "General Loan Policy",
        "section": "Late Payment Charges",
        "content": "Late payment charges apply if EMI is not paid by the due date: 1) 2% of EMI amount for delays up to 30 days, 2) 3% for delays of 31-60 days, 3) 5% for delays beyond 60 days. Additionally, penal interest of 2% per annum may apply on overdue amounts."
    },
    {
        "title": "General Loan Policy",
        "section": "Loan Account Management",
        "content": "Customers can manage their loan accounts through online banking and mobile app. Available features include: View loan details, Check outstanding balance, View EMI schedule, Download statements, Request NOC (No Objection Certificate), Update contact details, and Make prepayments."
    },
    {
        "title": "General Loan Policy",
        "section": "Customer Support",
        "content": "For loan-related queries, customers can: 1) Use the chatbot for instant support, 2) Call customer care at 1800-XXX-XXXX, 3) Email loansupport@bank.com, 4) Visit nearest branch. Support available 24/7 through digital channels."
    }
]
