document.addEventListener('DOMContentLoaded', function() {
    const conversationHistory = document.getElementById('conversation-history');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const applicantDataContainer = document.getElementById('applicant-data');
    const generateReportButton = document.getElementById('generate-report-button');
    const reportModal = document.getElementById('report-modal');
    const reportContent = document.getElementById('report-content');
    const closeButton = document.querySelector('.close-button');

    let applicantData = {
        "personal_information": {
          "date_of_birth": "1992-07-15",
          "gender": "Male",
          "father_name": "Rakesh Sharma",
          "address": "101, Rajendra Nagar, Mumbai, Maharashtra, 400001",
          "permanent_address": "501, Andheri West, Mumbai, Maharashtra, 400058"
        },
        "identification": {
          "aadhaar_number": "1234-5678-9012",
          "pan_number": "ABCDE1234F",
          "voter_id": "MH/09/987/654321",
          "passport_number": "P9876543",
          "passport_issued_state": "Maharashtra",
          "passport_expiry_date": "2032-10-05",
          "pan_issue_date": "2011-08-19"
        },
        "contact": {
          "phone": "+91 98765 43210",
          "email": "amit.sharma@email.com"
        },
        "employment": {
          "employer_name": "Tata Consultancy Services (TCS)",
          "job_title": "Senior Software Developer",
          "employment_type": "Full-time",
          "annual_salary": "Rs18,00,000",
          "work_experience": "8 years",
          "employer_contact": {
            "email": "hr@tcs.com",
            "phone": "+91 22 6789 1234"
          },
          "employee_id": "TCS56789",
          "date_of_joining": "2016-05-10",
          "work_location": "TCS Campus, Mumbai",
          "basic_salary": "Rs75,000",
          "hra": "Rs30,000",
          "pf_contribution": "Rs8,500",
          "net_monthly_salary": "150000"
        },
        "financial": {
          "bank_name": "ICICI Bank",
          "account_number": "345678901234",
          "account_type": "Savings",
          "credit_score": 620,
          "monthly_income": "Rs1,50,000",
          "monthly_expenses": "Rs50,000",
          "account_opening_date": "2014-06-20",
          "average_balance_3m": "Rs4,00,000",
          "recent_transactions": []
        },
        "loan_request": {
          "loan_amount": "Rs10,00,000",
          "loan_purpose": "Purchase of a New Car",
          "loan_term": "5 years",
          "interest_rate": "9.2%",
          "down_payment": "Rs2,00,000",
          "car_model": "Hyundai Creta SX",
          "ex_showroom_price": "Rs12,00,000",
          "on_road_price": "Rs14,00,000",
          "dealer_name": "Hyundai Motors, Mumbai",
          "dealer_contact": "+91 22 5678 9012",
          "property_value": "Rs10,00,000"
        }
      };

    
    let conversation = [];

    // Initialize conversation
    addMessage("Hello! I'm your AI loan assistant. Let's start your loan application. What's your full name?", 'ai');

    sendButton.addEventListener('click', handleUserInput);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleUserInput();
    });

    generateReportButton.addEventListener('click', generateReport);
    closeButton.addEventListener('click', () => reportModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === reportModal) reportModal.style.display = 'none';
    });

    async function handleUserInput() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';

        // Send user response to backend
        try {
            const response = await fetch('/api/process-response', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_response: message, applicant_data: applicantData})
            });

            const data = await response.json();
            applicantData = data.applicant_data;
            updateApplicantDataDisplay();

            if (data.needs_clarification) {
                addMessage(data.clarification_question, 'ai');
            } else {
                getNextQuestion();
            }
        } catch (error) {
            console.error("Error processing user input:", error);
            addMessage("Sorry, something went wrong. Please try again.", 'ai');
        }
    }

    function readAloud(text) {
        // Check if the browser supports speech synthesis
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US'; // Set the language (adjust as needed)
            utterance.rate = 1; // Set the speaking rate (1 is normal speed)
            utterance.pitch = 1; // Set the pitch (1 is normal pitch)
            window.speechSynthesis.speak(utterance);
        } else {
            console.warn("Speech synthesis is not supported in this browser.");
        }
    }

    async function getNextQuestion() {
        try {
            const response = await fetch('/api/next-question', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({applicant_data: applicantData, conversation_history: conversation})
            });

            const data = await response.json();
            addMessage(data.question, 'ai');
        } catch (error) {
            console.error("Error fetching next question:", error);
            addMessage("Sorry, something went wrong. Please try again.", 'ai');
        }
    }

    function addMessage(text, sender) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', `${sender}-message`);
        messageEl.textContent = text;
        conversationHistory.appendChild(messageEl);
        conversationHistory.scrollTop = conversationHistory.scrollHeight;
        conversation.push({sender, message: text});
        if (sender === 'ai') {
            readAloud(text);
        }
    }

    function updateApplicantDataDisplay() {
        applicantDataContainer.innerHTML = '';
        
        for (const category in applicantData) {
            if (Object.keys(applicantData[category]).length === 0) continue;

            const categoryEl = document.createElement('div');
            categoryEl.classList.add('category');

            const titleEl = document.createElement('div');
            titleEl.classList.add('category-title');
            titleEl.textContent = category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            categoryEl.appendChild(titleEl);

            for (const field in applicantData[category]) {
                const fieldEl = document.createElement('div');
                fieldEl.classList.add('field');

                const nameEl = document.createElement('div');
                nameEl.classList.add('field-name');
                nameEl.textContent = field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) + ':';
                
                const valueEl = document.createElement('div');
                valueEl.classList.add('field-value');
                valueEl.textContent = applicantData[category][field];

                fieldEl.appendChild(nameEl);
                fieldEl.appendChild(valueEl);
                categoryEl.appendChild(fieldEl);
            }

            applicantDataContainer.appendChild(categoryEl);
        }
    }

    async function generateReport() {
        try {
            const response = await fetch('/api/generate-report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({applicant_data: applicantData})
            });

            const report = await response.json();
            
            displayReport(report);

            // Close the browser window
            setTimeout(() => {
                if (confirm("The report has been generated. Do you want to close this window?")) {
                    window.location.href = "http://localhost:3000/status";
                }
            }, 1000);
            
        } catch (error) {
            console.error("Error generating report:", error);
            addMessage("Sorry, something went wrong while generating the report.", 'ai');
        }
    }

    function displayReport(report) {
        reportContent.innerHTML = `<h3>Loan Eligibility Report</h3>
                                   <p><strong>Status:</strong> ${report.eligibility_assessment.status}</p>
                                   <h4>Applicant Data:</h4>`;

        for (const category in report.applicant_data) {
            if (Object.keys(report.applicant_data[category]).length === 0) continue;

            let catHtml = `<strong>${category.replace('_',' ').toUpperCase()}</strong><ul>`;
            
            for (const field in report.applicant_data[category]) {
                catHtml += `<li>${field.replace('_',' ').toUpperCase()}: ${report.applicant_data[category][field]}</li>`;
            }
            
            catHtml += '</ul>';
            
            reportContent.innerHTML += catHtml;
        }

        if (report.eligibility_assessment.factors.length > 0) {
            reportContent.innerHTML += `<h4>Factors:</h4><ul>${report.eligibility_assessment.factors.map(f => `<li>${f}</li>`).join('')}</ul>`;
        }

        if (report.eligibility_assessment.recommendations.length > 0) {
            reportContent.innerHTML += `<h4>Recommendations:</h4><ul>${report.eligibility_assessment.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>`;
        }

        reportModal.style.display = 'block';
    }
});
