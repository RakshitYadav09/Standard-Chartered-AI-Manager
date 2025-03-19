# conversation_manager.py
from gemini_integration import GeminiAI
from loan_eligibility import LoanEligibilityEngine
import json
from datetime import datetime
import dotenv as load_dotenv

load_dotenv.load_dotenv()


class DynamicConversationManager:
    def __init__(self):
        self.ai = GeminiAI()
        self.eligibility_engine = LoanEligibilityEngine()
        self.applicant_data = self.load_applicant_data()
        self.conversation_history = []
        self.required_fields = self.get_required_fields()

    def load_applicant_data(self, file_path='applicant_data_structured.json'):
        """Load applicant data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File {file_path} not found. Starting with empty data.")
            return {
                "personal_information": {},
                "identification": {},
                "employment": {},
                "financial": {},
                "loan_request": {}
            }

    def save_applicant_data(self, file_path='applicant_data_structured.json'):
        """Save updated applicant data to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(self.applicant_data, file, indent=2)

    def get_required_fields(self):
        """Define the required fields for the conversation"""
        return [
            "personal_information.date_of_birth",
            "personal_information.gender",
            "employment.net_monthly_salary",
            "financial.credit_score",
            "loan_request.loan_amount",
            "loan_request.loan_term",
            "loan_request.interest_rate",
            "loan_request.property_value"
        ]

    def is_data_complete(self):
        """Check if all required fields are filled"""
        for field in self.required_fields:
            keys = field.split('.')
            data = self.applicant_data
            for key in keys:
                data = data.get(key, None)
                if data is None:
                    return False
        return True

    def get_missing_fields(self):
        """Get a list of missing fields"""
        missing_fields = []
        for field in self.required_fields:
            keys = field.split('.')
            data = self.applicant_data
            for key in keys:
                data = data.get(key, None)
                if data is None:
                    missing_fields.append(field)
                    break
        return missing_fields

    def update_applicant_data(self, field, value):
        """Update applicant data with the provided value"""
        keys = field.split('.')
        data = self.applicant_data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def start_conversation(self):
        """Start the dynamic conversation with the applicant (text-based only)"""
        print("Starting text-based conversation...")
        while not self.is_data_complete():
            missing_fields = self.get_missing_fields()
            if not missing_fields:
                break

            # Ask questions for missing fields
            for field in missing_fields:
                field_name = field.split('.')[-1].replace('_', ' ').capitalize()
                user_response = input(f"Please provide your {field_name}: ")
                self.update_applicant_data(field, user_response)

                # Save the conversation history
                self.conversation_history.append({
                    "field": field,
                    "user_response": user_response,
                    "timestamp": datetime.now().isoformat()
                })

                # Check if data is complete after each response
                if self.is_data_complete():
                    print("All required information has been collected.")
                    break

        # Save the updated applicant data
        self.save_applicant_data()
        print("Conversation completed. Applicant data saved.")

    def provide_final_assessment(self):
        """Provide final loan eligibility assessment"""
        eligibility_result = self.eligibility_engine.check_eligibility(self.applicant_data)
        gemini_assessment = self.ai.assess_loan_eligibility(self.applicant_data)

        # Prepare final report
        final_report = f"Loan Eligibility Report:\n\n{gemini_assessment}\n"
        
        if eligibility_result["status"] == "APPROVED":
            final_report += "\nCongratulations! Your loan application has been approved."
        elif eligibility_result["status"] == "CONDITIONALLY APPROVED":
            final_report += "\nYour loan application has been conditionally approved. Here are some recommendations:"
            for recommendation in eligibility_result.get("recommendations", []):
                final_report += f"\n- {recommendation}"
        elif eligibility_result["status"] == "NEEDS_MORE_INFO":
            final_report += "\nWe need more information to complete your application:"
            for factor in eligibility_result.get("factors", []):
                final_report += f"\n- {factor}"
        else:
            final_report += "\nUnfortunately, your loan application has been rejected due to the following reasons:"
            for factor in eligibility_result.get("factors", []):
                final_report += f"\n- {factor}"

        # Print the report
        print(final_report)

    def save_json_report(self, file_path='loan_report.json'):
        """Save the loan report to a JSON file"""
        report = self.generate_json_report()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(report, file, indent=2)
            print(f"\nLoan eligibility report saved to {file_path}")
            return report
        except Exception as e:
            print(f"Error saving report: {e}")
            return None

    def generate_json_report(self):
        """Generate a JSON report with applicant data and eligibility assessment"""
        eligibility_result = self.eligibility_engine.check_eligibility(self.applicant_data)
        
        report = {
            "applicant_data": self.applicant_data,
            "eligibility_assessment": {
                "status": eligibility_result["status"],
                "factors": eligibility_result.get("factors", []),
                "recommendations": eligibility_result.get("recommendations", [])
            },
            "report_date": datetime.now().strftime("%B %d, %Y, %I:%M %p %Z")
        }
        
        return report