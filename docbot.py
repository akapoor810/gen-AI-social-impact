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



### --- ONBOARDING FUNCTION --- ###
def first_interaction(message, user, session_dict):
    print("MY MES" + message)
    questions = {
        "condition": "🏪 What condition do you have? (Type II Diabetes, Crohn’s disease, or both)",
        "age": "👋 Hi, I'm DocBot — your health assistant!\n"
                "I'll help you track symptoms, remind you about meds 💊, and send you health tips 📰.\n\n"
                "Let's start with a few quick questions.\n 🎂 How old are you?",
        "weight": "⚖️ What's your weight (in kg)?",
        "medications": "💊 What medications are you currently taking? [medication 1, medication 2, etc]",
        "emergency_contact": "📱 Who should we contact in case of emergency? [email]",
        "news_pref": "📰 What kind of weekly health updates would you like?\nOptions: Instagram Reel 📱, TikTok 🎵, or Research News 🧪"
    }

    stage = session_dict[user].get("onboarding_stage", "condition")

    if stage == "condition":
        session_dict[user]["condition"] = message
        session_dict[user]["onboarding_stage"] = "age"
        return {"text": questions["age"]}

    elif stage == "age":
        if not message.isdigit():
            return {"text": "❗ Please enter a valid age (a number)."}
        session_dict[user]["age"] = int(message)
        session_dict[user]["onboarding_stage"] = "weight"
        return {"text": questions["weight"]}

    elif stage == "weight":
        cleaned = message.lower().replace("kg", "").strip()

        if not cleaned.replace('.', '', 1).isdigit():
            return {"text": "❗ Please enter a valid weight (a number in kg)."}
        
        session_dict[user]["weight"] = cleaned
        session_dict[user]["onboarding_stage"] = "medications"
        return {"text": questions["medications"]}

    elif stage == "medications":
        session_dict[user]["medications"] = [med.strip() for med in message.split(",")]
        session_dict[user]["onboarding_stage"] = "emergency_contact"
        return {"text": questions["emergency_contact"]}

    elif stage == "emergency_contact":
        session_dict[user]["emergency_contact"] = message
        session_dict[user]["onboarding_stage"] = "news_pref"

        buttons = [
            {
                "type": "button",
                "text": "🎥 YouTube",
                "msg": "YouTube",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "youtube_button"
            },
            {
                "type": "button",
                "text": "📸 IG Reel",
                "msg": "Instagram Reel",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "insta_button"
            },
            {
                "type": "button",
                "text": "🎵 TikTok",
                "msg": "TikTok",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "tiktok_button"
            },
            {
                "type": "button",
                "text": "🧪 Research",
                "msg": "Research News",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "research_button"
            }
        ]

        return {
            "text": "📰 What kind of weekly health updates would you like?",
            "attachments": [
                {
                    "collapsed": False,
                    "color": "#e3e3e3",
                    "actions": buttons
                }
            ]
        }

    elif stage == "news_pref":
        valid_options = ["YouTube", "Instagram Reel", "TikTok", "Research News"]

        if message not in valid_options:
            return {"text": "Please click one of the buttons above to continue."}

        session_dict[user]["news_pref"] = [message]
        session_dict[user]["onboarding_stage"] = "condition1"


        buttons = [
            {
                "type": "button",
                "text": "Crohn's",
                "msg": "Crohn's",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_condition_crohns"
            },
            {
                "type": "button",
                "text": "Type II Diabetes",
                "msg": "Type II Diabetes",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_condition_diabetes"
            }
        ]
        return {
            "text": "🏪 What condition do you have?",
            "attachments": [
                {
                    "collapsed": False,
                    "color": "#e3e3e3",
                    "actions": buttons
                }
            ]
        }
    
    elif stage == "condition1":
        print(message)
        valid_conditions = ["Crohn's", "Type II Diabetes"]

        if message not in valid_conditions:
                    return {"text": "Please click one of the buttons above to continue."}

        session_dict[user]["condition"] = message
        session_dict[user]["onboarding_stage"] = "done"

        return llm_daily(message, user, session_dict)
    


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

            Step 1: Start with: "Hi {user} 👋! Let's begin your daily wellness check for {session_dict[user]['condition']} 📋.
            First off, have you taken your daily doses of {session_dict[user]['medications']} 💊?"
            If the user confirms they have taken their medications, move to Step 2.
            Else, remind them to take their medications.
            Step 2: **Ask 2-3 symptom-related questions** that are specific to their condition. Ask one question at a time, acknowleding and responding to the user's response before posing the next question. Do not ask all the questions at once.
            Step 3: After every question, **evaluate the user's response**.
            - If their symptoms are normal, reassure them and offer general wellness tips.
            - If their symptoms are abnormal, express concern and provide advice to alleviate discomfort based on your knowledge of their condition.  
            - Begin every response with your advice with "DocBot's Advice: "
            - If the symptoms are **severe**, gently ask the user if they would like to contact their **emergency contact** (**{session_dict[user]['emergency_email']}**).  

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
        lastk=5,
        session_id=sid,
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )
    # TODO: Determine k value. Determine how to pass advice response to QA agent
    # play around with RAG threshold
    response_text = response.get("response", "⚠️ Sorry, I couldn't process that. Could you rephrase?").strip() if isinstance(response, dict) else response.strip()
    print(response_text)
    

    if "docbot's advice" in response_text.lower():
        qa_response = qa_agent(message, response_text, user, session_dict)

        if "accepted" in qa_response.lower():
            pass    
        elif "needs revision" in qa_response.lower():
            match = re.search(r"Suggested revision:\s*(.*)", qa_response)
            if match:
                response_text = match.group(1).strip()
            else:
                print("No revised message found.")
        elif "rejected" in qa_response.lower():
            response_text = f"I'm not sure how to evaluate those systems. 🙁 Would you like me to contact your emergency contact at {session_dict[user]['emergency_email']}?"
            

    # Create the response object with the basic text
    response_obj = {
        "text": response_text
    }


    save_sessions(session_dict)
    return response_obj



def qa_agent(message, agent_response, user, session_dict):
    sid = session_dict[user]["session_id"]

    response = generate(
        model="4o-mini",
        system=f"""
            ### Role:
                You are a highly knowledgeable and cautious **quality assurance assistant** reviewing medical advice 
                generated by another AI agent. Your primary responsibility is to **evaluate the safety, appropriateness, 
                and tone** of the medical responses provided to users with chronic conditions (e.g., diabetes, Crohn's disease).

                ---

                ### Objectives:
                1. **Ensure Medical Safety**
                - Verify that the advice does not suggest a diagnosis or prescribe treatment.
                - Confirm that the response encourages users to consult a healthcare provider for serious or unclear symptoms.
                - Check for misinformation, unsupported claims, or dangerous suggestions based on your knowledge of the condition.

                2. **Check Relevance and Completeness**
                - Ensure the advice is relevant to the user's condition and symptoms.
                - Identify if any critical symptoms or next steps were missed.
                - Confirm the message includes compassionate guidance for users in distress.

                3. **Evaluate Tone and Language**
                - Ensure the tone is empathetic, respectful, and calming.
                - Confirm the language is clear, concise, and free of technical jargon unless properly explained.

                ---

                ### Guidelines:
                - If the advice is **safe, appropriate, and helpful**, respond with:
                `"✅ Approved. The message is safe, relevant, and well-phrased."`

                - If the advice has **minor issues**, suggest a revision:
                `"⚠️ Needs revision: [brief explanation]. Suggested revision: [revised message]"`

                - If the advice contains **major issues**, flag it:
                `"❌ Rejected: [brief explanation of the safety concern or misinformation]"`

                ---

                ### Input:
                You will be given:
                - The **user's condition** and reported **symptoms**.
                - The **original advice** generated by the primary AI agent.

                ---

                ### Example:

                **User Condition:** Diabetes  
                **User Message:** “I feel dizzy and confused.”  
                **Primary Agent Response:**  
                _"You might be experiencing low blood sugar. Try drinking juice or eating something sweet. If it doesn't help, take insulin or call your doctor."_

                **Your Evaluation:**  
                ❌ Rejected: Suggesting insulin without knowing blood sugar levels could be dangerous. Low blood sugar should not be treated with insulin.  

                Suggested revision:  
                _"Dizziness and confusion can be signs of low blood sugar. If you suspect this, try eating something with sugar, like juice or candy. If you don't feel better soon, seek medical help immediately."_
        """,

        query=f"User Condition: {session_dict[user]['condition']}. User Message: {message}. Primary Agent Response: {agent_response}",
        temperature=0.3,
        lastk=5,
        session_id=sid,
        rag_usage=True,
        rag_threshold='0.7',
        rag_k=10
    )

    response_text = response.get("response", "⚠️ Sorry, I couldn't process that. Could you rephrase?").strip() if isinstance(response, dict) else response.strip()
    print(f"qa agent said: {response_text}")

    # Create the response object with the basic text
    response_obj = {
        "text": response_text
    }

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
            "onboarding_stage": "condition",
            "condition": "",
            "age": 0,
            "weight": 0,
            "medications": [],
            "emergency_email": "",
            "news_pref": ""
        }
        save_sessions(session_dict)  # Save immediately after creating new session
        print(session_dict[user]["condition"])
        rag_upload(session_dict[user]["condition"], user, session_dict)
        response = "🔄 Restarted onboarding.\n"


    if session_dict[user]["onboarding_stage"] != "done":
        response += first_interaction(message, user, session_dict)
    else:
        # schedule.every().day.at("09:00").do(llm_daily)
        response = llm_daily(message, user, session_dict)
    
    # Save session data at the end of the request
    save_sessions(session_dict)
    return jsonify(response)


### --- RUN THE FLASK APP --- ###
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)