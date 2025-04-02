from flask import send_file
import threading
import schedule
import time
import os
import json
from flask import Flask, request, jsonify, Response
from llmproxy import *
import re

app = Flask(__name__)

# JSON file to store user sessions
SESSION_FILE = "session_store.json"


### --- SESSION MANAGEMENT FUNCTIONS --- ###
def load_sessions():
    """Load stored sessions from a JSON file."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as file:
            try:
                session_data = json.load(file)
                print(f"Loaded session data: {session_data}")
                return session_data
            except json.JSONDecodeError:
                print("Error loading session data, returning empty dict.")
                return {}  # If file is corrupted, return an empty dict
    print("No session file found. Returning empty dictionary.")
    return {}

def save_sessions(session_dict):
    """Save sessions to a JSON file."""
    print(f"Saving session data: {session_dict}")
    with open(SESSION_FILE, "w") as file:
        json.dump(session_dict, file, indent=4)
    print("Session data saved.")



### --- RAG UPLOAD FUNCTION --- ###
def rag_upload(condition, user, session_dict):
    sid = session_dict[user]["session_id"]
    if "diabetes" in condition.lower():
        pdf_upload(path = 'HCS-Booklet-Diabetes Type 2 Guidebook.pdf',
        session_id = sid,
        strategy = 'smart')
        
        pdf_upload(path = 'standards-of-care-2023.pdf',
        session_id = sid,
        strategy = 'smart')
    
    else:
        pdf_upload(path = 'ACG-Crohns-Guideline-Summary.pdf',
        session_id = sid,
        strategy = 'smart')

        pdf_upload(path = 'crohns-disease.pdf',
        session_id = sid,
        strategy = 'smart')

        pdf_upload(path = 'living-with-crohns-disease.pdf',
        session_id = sid,
        strategy = 'smart')


### --- DAILY INTERACTION FUNCTION --- ###
def llm_daily(message, user, session_dict):
    """Handles routine wellness check: 
        - Collects daily symptoms through personalized questions
        - Formulates advice and passes to QA agent before returning
        - Activates expert in the loop if it determines symptoms are abnormal.
    """
    sid = session_dict[user]["session_id"]

    response = generate(
        model="4o-mini",
        system=f"""
            ### **Role & Purpose**  
            You are a compassionate and professional **nurse** performing a routine **wellness check** on a patient.  
            Your goal is to **assess the patient's well-being** by asking relevant questions based on their condition, 
            evaluating their responses, and offering appropriate advice.  

            ### **Behavior & Workflow**  
            First: **Always start with a friendly greeting** and acknowledge the user's condition (**{session_dict[user]['condition']}**).  
            Second: **Ask the user if they've taken their medications, if they have any (list of medications is **{session_dict[user]['medications']}**).
            Third: **Ask symptom-related questions** that are specific to their condition.  
            Fourth: **Evaluate the user's response** to determine if their symptoms are:
            - **Normal symptoms** → Reassure the patient and offer general wellness tips.
            - **Abnormal symptoms** → Express concern and provide advice to alleviate discomfort.  
            Finally: If symptoms are **severe**, gently ask the user if they would like to contact their **emergency contact** (**{session_dict[user]['emergency_email']}**).  

            ### **Response Guidelines**  
            - Only respond to queries related to the user's condition and current symptoms. If the user gets off track
            remind them that you are here to assess their well-being and take their current symptoms.
            - **Tone:** Maintain a warm, empathetic, and professional tone.  
            - **Clarity:** Use simple, easy-to-understand language.  
            - **Avoid Diagnosis:** Do **not** diagnose conditions—only assess symptoms and offer general wellness advice.  
            - **Encourage Action:** If symptoms worsen, encourage the user to seek medical help.  

            ### **Example Interactions**  
            **Scenario 1: User with Type II Diabetes**  
            🗣 **User:** "I feel a bit dizzy and tired today."  
            🤖 **Bot:** "Dizziness and fatigue can sometimes occur with diabetes. Have you checked your blood sugar levels? If they are too high or too low, try adjusting your meal or fluid intake accordingly. If dizziness persists, you may want to rest and hydrate. Would you like me to notify your emergency contact, [John Doe]?  

            **Scenario 2: User with Crohn's Disease**  
            🗣 **User:** "I have been experiencing a lot of abdominal pain and diarrhea today."  
            🤖 **Bot:** "That sounds uncomfortable. Severe abdominal pain and diarrhea could indicate a Crohn's flare-up. Staying hydrated is important—try drinking electrolyte-rich fluids. If the pain worsens or you notice any bleeding, it might be best to reach out to your doctor. Would you like me to notify your emergency contact, [Sarah Smith]?  

            ### **Memory & Context Handling**  
            - Retrieve the user's condition from **{session_dict[user]['condition']}** to personalize the questions.  
            - Retrieve the user's **emergency contact** from **{session_dict[user]['emergency_email']}** if symptoms seem severe.  
            - Do **not** forget the session details within a single conversation.
        """,

        query=message,
        temperature=0.7,
        lastk=10,
        session_id=sid,
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )
    # TODO: Determine k value. Determine how to pass advice response to QA agent
    # play around with RAG threshold
    response_text = response.get("response", "⚠️ Sorry, I couldn't process that. Could you rephrase?").strip() if isinstance(response, dict) else response.strip()
    print(response_text)

    # Create the response object with the basic text
    response_obj = {
        "text": response_text
    }

    save_sessions(session_dict)
    return response_obj



# def run_scheduler():
#     """
#     Runs an infinite loop to check and execute scheduled jobs.
#     It should be run in a separate thread to avoid blocking the Flask server.
#     Executes scheduled tasks every minute.
#     """
#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Check every minute


# def scheduled_task():
#     """
#     This function is scheduled to run every day at 9 AM.
#     It loads user sessions, calls `llm_daily()` for each user, and saves the results.
#     Modifies `session_dict` and saves session data.
#     """
#     session_dict = load_sessions()  # Load session data
#     for user in session_dict.keys():
#         llm_daily("Daily scheduled message", user, session_dict)  # Call LLM function
#     save_sessions(session_dict)  # Save updated sessions


# schedule.every().day.at("09:00").do(scheduled_task)

# # Start the scheduler in a separate background thread
# scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
# scheduler_thread.start()


### --- FLASK ROUTE TO HANDLE USER REQUESTS --- ###
# """Handles user messages and manages session storage."""
@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    message = data.get("text", "").strip()
    user = data.get("user_name", "Unknown")

    # Load sessions at the beginning of each request
    session_dict = load_sessions()
    
    print("Current session dict:", session_dict)
    print("Current user:", user)

    # Initialize user session if it doesn't exist
    if user not in session_dict or "restart" in message.lower():
        print("new user", user)
        session_dict[user] = {
            "session_id": f"{user}-session",
            "onboarding_stage": "done", # "condition",
            "condition": "diabetes", # ""
            "age": 21,  # 0
            "weight": 150,  # 0
            "medications": ["insulin", "metformin", "sulfonylureas"], # [""]
            "emergency_email": "anika.kapoor810@gmail.com",    # ""
            "news_pref": "insulin news" # ""
        }
        save_sessions(session_dict)  # Save immediately after creating new session
        print(session_dict[user]["condition"])
        rag_upload(session_dict[user]["condition"], user, session_dict)

    if session_dict[user]["onboarding_stage"] != "done":
        response = {"text": "Calling first_interaction()" }
        # response = first_interaction(message, user)
    else:
        # schedule.every().day.at("09:00").do(llm_daily)
        response = llm_daily(message, user, session_dict)
    
    # Save session data at the end of the request
    save_sessions(session_dict)
    return jsonify(response)


### --- RUN THE FLASK APP --- ###
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)