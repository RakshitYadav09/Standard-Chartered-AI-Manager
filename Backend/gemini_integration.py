# gemini_integration.py
import google.generativeai as genai
import os
import json
import re
import dotenv as load_dotenv

load_dotenv.load_dotenv()

class GeminiAI:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
            
        genai.configure(api_key=api_key)
        
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            print("Falling back to Gemini 1.5 Pro")
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        system_prompt = """
       You are an AI loan manager at a bank. Your job is to help customers apply for loans by:

    Gathering key loan and personal details in a conversational manner.
    Verifying identity and financial details.
    Assessing loan eligibility based on provided information.
    Providing a final loan application report without asking extra questions.

If data is insufficient, ask only for missing details concisely. Keep responses natural, professional, and structured. Provide JSON output when requested.

Required information for loan application:
- credit_score (financial.credit_score)
- monthly_income (employment.net_monthly_salary)
- monthly_expenses (financial.monthly_expenses)
- work_experience (employment.work_experience)
- loan_amount (loan_request.loan_amount)
- loan_term (loan_request.loan_term)
- interest_rate (loan_request.interest_rate)
- property_value (loan_request.property_value)

If all required information is present, respond with 'all info is complete' and proceed with assessment.
If any required information is missing, ask only for the missing information.
        """
        
        self.chat = self.model.start_chat(history=[])
        self.chat.send_message(system_prompt)
        
    def update_context(self, applicant_data):
        if not applicant_data:
            return
            
        context = "Current applicant information:\n"
        for category, details in applicant_data.items():
            if isinstance(details, dict):
                context += f"\n{category.replace('_', ' ').title()}:\n"
                for key, value in details.items():
                    if value:
                        context += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        self.chat.send_message(f"[SYSTEM] {context}")
        
    def get_next_question(self, applicant_data, conversation_history):
        self.update_context(applicant_data)
        
        # First check if all required information is present
        required_fields = self.check_required_fields(applicant_data)
        
        if not required_fields:
            return "All information is complete. I can now proceed with your loan assessment."
        
        prompt = f"""
        Based on the applicant information so far, what's the next question I should ask to progress their loan application?
        
        The following information is still missing:
        {', '.join(required_fields)}
        
        Do not include any prefix like "AI:" or other identifiers and don't tell anything about the next logical question.
    
        Recent conversation:
        {conversation_history}
        
        Ask only ONE brief and conversational question focused on gathering the missing information.
        """
        
        response = self.chat.send_message(prompt)
        return response.text
    
    def check_required_fields(self, applicant_data):
        """Check if all required fields are present in the applicant data."""
        missing_fields = []
        
        required_fields = {
            'financial.credit_score': 'credit_score',
            'employment.net_monthly_salary': 'monthly_income',
            'financial.monthly_expenses': 'monthly_expenses',
            'employment.work_experience': 'work_experience',
            'loan_request.loan_amount': 'loan_amount',
            'loan_request.loan_term': 'loan_term',
            'loan_request.interest_rate': 'interest_rate',
            'loan_request.property_value': 'property_value'
        }
        
        for path, field_name in required_fields.items():
            category, field = path.split('.')
            if not applicant_data.get(category, {}).get(field, None):
                missing_fields.append(field_name)
        
        return missing_fields
    
    def handle_user_response(self, user_response, applicant_data):
        prompt = f"""
        The user responded: "{user_response}"

        Extract relevant information from this response to update their application data.
        
        Respond strictly in this JSON format without markdown or extra text:
        
        {{
          "data_updates": {{
            "category": {{
              "field": "value"
            }}
          }},
          "needs_clarification": false,
          "clarification_question": ""
        }}

        If clarification is needed or no data is found, adjust accordingly.
        """

        response = self.chat.send_message(prompt)
        
        # Robust JSON extraction
        json_str = self.extract_json(response.text)
        
        try:
            data = json.loads(json_str)
            return data
        except Exception as e:
            print(f"JSON parsing error: {e}")
            print(f"Gemini raw response: {response.text}")
            return {
                "data_updates": {},
                "needs_clarification": True,
                "clarification_question": "I'm sorry, I had trouble understanding your last response clearly. Could you please rephrase?"
            }

    def assess_loan_eligibility(self, applicant_data):
        self.update_context(applicant_data)
        
        # First ensure all required information is present
        missing_fields = self.check_required_fields(applicant_data)
        if missing_fields:
            return f"I still need information about your {', '.join(missing_fields)} before I can assess your loan eligibility."
        
        prompt = """
        Based on the applicant's information provided so far, provide a brief conversational assessment of their loan eligibility status (APPROVED, CONDITIONALLY APPROVED, NEEDS MORE INFORMATION, or REJECTED).
        
        Keep your response concise and friendly.
        """
        
        response = self.chat.send_message(prompt)
        return response.text
    
    @staticmethod
    def extract_json(text):
        # Remove markdown code block formatting if present
        json_match = re.search(r'```json\s+(.*?)\s+```', text, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            json_str = json_match.group(1).strip()
            return json_str
        
        # Try plain code block
        json_match_plain = re.search(r'```\s+(.*?)\s+```', text, re.DOTALL)
        if json_match_plain:
            json_str = json_match_plain.group(1).strip()
            return json_str
        
        # Fallback: Try extracting first valid JSON object directly
        json_match_simple = re.search(r'\{.*\}', text, re.DOTALL)
        
        if json_match_simple:
            return json_match_simple.group(0).strip()
        
        # If no JSON found at all
        raise ValueError("No valid JSON found in Gemini's response.")