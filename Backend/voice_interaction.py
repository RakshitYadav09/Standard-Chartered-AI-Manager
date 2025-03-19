# voice_based_chatbot.py
import pyttsx3
import json
import os
import speech_recognition as sr
import time
import winsound  # For Windows sound
from gemini_integration import GeminiAI
from loan_eligibility import LoanEligibilityEngine
from dotenv import load_dotenv

class VoiceBasedChatbot:
    def __init__(self):
        load_dotenv()
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 200)  # Slowed down for better clarity
        self.tts_engine.setProperty('volume', 0.9)
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('voice', voices[0].id)

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize Gemini AI and loan eligibility engine
        self.ai = GeminiAI()
        self.eligibility_engine = LoanEligibilityEngine()

        # Load applicant data
        self.applicant_data = self.load_applicant_data()

        # Conversation history
        self.conversation_history = []
        
        # Status indicators
        self.listening_sound_enabled = True

    def speak(self, text):
        """Convert text to speech and play it"""
        print(f"AI: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def play_listening_sound(self):
        """Play a sound to indicate listening has started"""
        try:
            # Play a beep sound (frequency, duration)
            # First beep: higher pitch
            winsound.Beep(1000, 150)
            time.sleep(0.05)
            # Second beep: higher pitch
            winsound.Beep(1200, 150)
            
            # Say "Listening" with TTS
            self.tts_engine.say("Listening")
            self.tts_engine.runAndWait()
            
        except Exception as e:
            print(f"Could not play listening sound: {e}")

    def listen(self):
        """Listen to user's voice input and convert to text"""
        with sr.Microphone() as source:
            # Adjust for ambient noise
            print("Adjusting for ambient noise, please wait...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Play sound and visual indicator that we're listening
            print("\n=== LISTENING NOW ===")
            
            # Play the listening sound
            if self.listening_sound_enabled:
                self.play_listening_sound()
            
            try:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                
                # Play a sound to indicate listening has stopped
                try:
                    winsound.Beep(800, 150)  # Lower pitch for end
                except:
                    pass
                    
                print("Processing audio...")
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
                
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for speech.")
                self.speak("I didn't hear anything. Let me ask again.")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio.")
                self.speak("I couldn't understand what you said. Could you please repeat?")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                self.speak("I'm having trouble connecting to the speech recognition service.")
                return None
            finally:
                print("=== LISTENING ENDED ===\n")

    def load_applicant_data(self, file_path='applicant_data_structured.json'):
        """Load applicant data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {
                "personal_information": {},
                "identification": {},
                "employment": {},
                "financial": {},
                "loan_request": {}
            }

    def save_applicant_data(self, file_path='applicant_data_structured.json'):
        """Save updated applicant data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.applicant_data, file, indent=2, ensure_ascii=False)
            print(f"Applicant data saved to {file_path}")
        except Exception as e:
            print(f"Error saving applicant data: {e}")

    def update_applicant_data(self, updates):
        """Update applicant data with new information"""
        if not updates:
            return

        for category, details in updates.items():
            if category not in self.applicant_data:
                self.applicant_data[category] = {}

            if isinstance(details, dict):
                for key, value in details.items():
                    self.applicant_data[category][key] = value

    def start_conversation(self):
        """Start the voice-based conversation"""
        greeting = "Hello! I'm your AI loan assistant. Let's start your loan application using voice interaction. I'll make a sound and say 'Listening' when it's your turn to speak."
        self.speak(greeting)

        conversation_active = True
        max_turns = 30
        current_turn = 0

        while conversation_active and current_turn < max_turns:
            current_turn += 1

            recent_history = "\n".join(self.conversation_history[-6:]) if self.conversation_history else ""
            next_question = self.ai.get_next_question(self.applicant_data, recent_history)

            # Ask the question via TTS
            self.speak(next_question)
            self.conversation_history.append(f"AI: {next_question}")

            # Get user's voice response
            user_input = self.listen()
            
            if not user_input:
                # Already handled in listen() method with appropriate messages
                current_turn -= 1  # Retry this turn again without incrementing count
                continue

            if any(word in user_input.lower() for word in ["exit", "quit", "stop", "end", "bye"]):
                conversation_active = False
                break

            self.conversation_history.append(f"User: {user_input}")

            try:
                response_data = self.ai.handle_user_response(user_input, self.applicant_data)

                if response_data.get("needs_clarification", False):
                    clarification_question = response_data.get("clarification_question", "Could you please clarify?")
                    self.speak(clarification_question)
                    
                    # Get clarification with audio cue
                    clarification_response = self.listen()

                    if clarification_response:
                        clarification_data = self.ai.handle_user_response(clarification_response, self.applicant_data)
                        if "data_updates" in clarification_data:
                            self.update_applicant_data(clarification_data["data_updates"])

                if "data_updates" in response_data:
                    self.update_applicant_data(response_data["data_updates"])

            except Exception as e:
                print(f"Error processing response: {e}")
                self.speak("I'm having trouble processing that. Let's continue.")

            # Periodically check eligibility after every 5 turns
            if current_turn % 5 == 0:
                loan_info = self.applicant_data.get("loan_request", {})
                financial_info = self.applicant_data.get("financial", {})

                if loan_info.get("loan_amount") and financial_info.get("monthly_income"):
                    self.speak("I have enough information to assess your loan eligibility now. Would you like to hear it?")
                    
                    # Listen for response with audio cue
                    eligibility_response = self.listen()

                    if eligibility_response and any(word in eligibility_response.lower() for word in ["yes", "sure", "okay"]):
                        gemini_assessment = self.ai.assess_loan_eligibility(self.applicant_data)
                        eligibility_result = self.eligibility_engine.check_eligibility(self.applicant_data)

                        # Provide assessment via TTS
                        self.speak(gemini_assessment)

                        # Ask to continue or end session
                        self.speak("Would you like to continue or end our session?")
                        
                        # Listen for response with audio cue
                        continue_response = self.listen()

                        if continue_response and any(word in continue_response.lower() for word in ["end", "stop", "finish"]):
                            conversation_active = False

            # Save data periodically every 2 turns
            if current_turn % 2 == 0:
                self.save_applicant_data()

        # End of conversation handling
        closing_message = "Thank you for using our loan application service. Your details have been saved. Goodbye!"
        self.speak(closing_message)
        self.save_applicant_data()

if __name__ == "__main__":
    chatbot = VoiceBasedChatbot()
    chatbot.start_conversation()