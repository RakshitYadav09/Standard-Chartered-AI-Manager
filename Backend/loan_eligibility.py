# loan_eligibility.py
class LoanEligibilityEngine:
    def __init__(self):
        # Define loan eligibility criteria
        self.criteria = {
            'minimum_credit_score': 700,
            'minimum_income': 50000,  # Monthly income in INR
            'maximum_dti_ratio': 0.5,  # Debt-to-Income ratio
            'minimum_employment_years': 2,
            'loan_to_value_ratio': 0.8  # For secured loans
        }
    
    def calculate_dti_ratio(self, monthly_income, monthly_expenses):
        """Calculate Debt-to-Income ratio"""
        if monthly_income <= 0:
            return 1.0  # Maximum ratio if income is zero or negative
        return monthly_expenses / monthly_income
    
    def calculate_emi(self, loan_amount, interest_rate, tenure_years):
        """Calculate EMI for the loan"""
        monthly_interest_rate = interest_rate / (12 * 100)
        tenure_months = tenure_years * 12
        emi = loan_amount * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure_months) / (((1 + monthly_interest_rate) ** tenure_months) - 1)
        return emi
    
    def check_eligibility(self, applicant_data):
        """Check loan eligibility based on applicant data"""
        results = {
            'status': None,
            'factors': [],
            'recommendations': []
        }
        
        # Extract relevant data
        try:
            credit_score = int(applicant_data.get('financial', {}).get('credit_score', 0))
            monthly_income = int(applicant_data.get('employment', {}).get('net_monthly_salary', 0))
            monthly_expenses = int(applicant_data.get('financial', {}).get('monthly_expenses', 0))
            work_experience = int(applicant_data.get('employment', {}).get('work_experience', 0))
            loan_amount = int(applicant_data.get('loan_request', {}).get('loan_amount', 0))
            loan_term = int(applicant_data.get('loan_request', {}).get('loan_term', 0))
            interest_rate = float(applicant_data.get('loan_request', {}).get('interest_rate', 0))
            property_value = int(applicant_data.get('loan_request', {}).get('property_value', 0))
        except (ValueError, TypeError):
            # Handle conversion errors
            results['status'] = "REJECTED"
            results['factors'].append("Missing or invalid financial information")
            return results
        
        # Calculate DTI ratio
        dti_ratio = self.calculate_dti_ratio(monthly_income, monthly_expenses)
        
        # Calculate EMI for the requested loan
        emi = self.calculate_emi(loan_amount, interest_rate, loan_term)
        
        # Calculate Loan-to-Value ratio for secured loans
        ltv_ratio = loan_amount / property_value if property_value > 0 else 1.0
        
        # Check against criteria
        if credit_score < self.criteria['minimum_credit_score']:
            results['factors'].append(f"Credit score ({credit_score}) below minimum requirement ({self.criteria['minimum_credit_score']})")
            results['recommendations'].append("Work on improving your credit score")
        
        if monthly_income < self.criteria['minimum_income']:
            results['factors'].append(f"Monthly income below minimum requirement")
            results['recommendations'].append("Consider applying for a smaller loan amount")
        
        if dti_ratio > self.criteria['maximum_dti_ratio']:
            results['factors'].append(f"Debt-to-income ratio too high")
            results['recommendations'].append("Reduce your monthly expenses or debt obligations")
        
        if work_experience < self.criteria['minimum_employment_years']:
            results['factors'].append(f"Work experience below minimum requirement")
            results['recommendations'].append("Consider providing additional employment stability proof")
        
        if ltv_ratio > self.criteria['loan_to_value_ratio']:
            results['factors'].append(f"Loan amount too high relative to property value")
            results['recommendations'].append("Consider a smaller loan amount or providing additional collateral")
        
        # Check if EMI is affordable (less than 50% of income)
        if emi > (monthly_income * 0.5):
            results['factors'].append(f"EMI would be too high relative to income")
            results['recommendations'].append("Consider a longer loan term or smaller loan amount")
        
        # Determine overall status
        if not results['factors']:
            results['status'] = "APPROVED"
        elif len(results['factors']) <= 1:
            results['status'] = "CONDITIONALLY_APPROVED"
        elif len(results['factors']) <= 2:
            results['status'] = "REJECTED_WITH_CONDITIONS"
        else:
            results['status'] = "REJECTED"
        
        return results
