from flask import send_file
import threading
import schedule
import time
import os
import json
from flask import Flask, request, jsonify, Response
from llmproxy import *
import re
from duckduckgo_search import DDGS 
from bs4 import BeautifulSoup
import requests
import random

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


#WEEKLY TOOL FUNCTIONS
def websearch(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
    return [r["href"] for r in results]

def get_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove non-content tags for a cleaner text
        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())[:1500]
    return f"Failed to fetch {url}, status code: {response.status_code}"

def youtube_search(query):
    with DDGS() as ddgs:
        results = ddgs.text(f"{query} site:youtube.com", max_results=5)
    return [r["href"] for r in results if "youtube.com/watch" in r["href"]]

def tiktok_search(query):
    with DDGS() as ddgs:
        results = ddgs.text(f"{query} site:tiktok.com", max_results=5)
    return [r["href"] for r in results if "tiktok.com" in r["href"]]

def instagram_search(query):
    hashtag = query.replace(" ", "")
    with DDGS() as ddgs:
        results = ddgs.text(f"#{hashtag} site:instagram.com", max_results=5)
    return [r["href"] for r in results if "instagram.com" in r["href"]]

# --- TOOL PARSER ---
def extract_tool(text):
    for tool in ["websearch", "get_page", "youtube_search", "tiktok_search", "instagram_search"]:
        match = re.search(fr'{tool}\([^)]*\)', text)
        if match:
            return match.group()
    
    return


# --- SEND EMAIL FUNCTION ---
def send_email(dst, subject, content):
    print("destination email", dst)
    print("subject", subject)
    print("content", content)

    import os, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import json
 
    # Email configuration
    smtp_server = "smtp-tls.eecs.tufts.edu"  # e.g., mail.yourdomain.com
    smtp_port = 587  # Usually 587 for TLS, 465 for SSL
    sender_email = "akapoo02@eecs.tufts.edu"
    receiver_email = dst
    password = "anikacs@tufts810"

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    body = content
    msg.attach(MIMEText(body, "plain"))

    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection (use only if the server supports TLS)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        print("there was an error")
        return f"Error: {e}" 


# --- WEEKLY UPDATE FUNCTION ---
def agent_weekly_update(user_info, health_info):
    """
    Create a system message using the user and health info, then call the LLM agent.
    The agent returns a tool call (e.g., youtube_search("gut health smoothies")).
    """
    system = f"""
You are an AI agent designed to handle weekly health content updates for users with specific health conditions.

In addition to your own intelligence, you are given access to a set of tools that let you fetch personalized health content from various online platforms.

Your job is to use the right tool to deliver a helpful and engaging content recommendation **based on the user's health condition and preferences**.

Think step-by-step about which platform is best for this week's update, and then return the correct tool call using the examples provided.

ONLY respond with a tool call like: youtube_search("gut health smoothies")

### USER INFORMATION ###
- Name: {user_info.get('name')}
- Health condition: {health_info.get('condition')}
- Preferred platform: {user_info.get('news_pref')}
- Preferred news sources: {", ".join(user_info.get('news_sources', []))}

### PROVIDED TOOLS INFORMATION ###

##1. Tool to perform a YouTube video search
Name: youtube_search
Parameters: query
Example usage: youtube_search("crohn's anti-inflammatory meals")

##2. Tool to search TikTok for short-form video content
Name: tiktok_search
Parameters: query
Example usage: tiktok_search("what I eat with IBS")

##3. Tool to search Instagram posts/reels via hashtags
Name: instagram_search
Parameters: query
Example usage: instagram_search("gut healing routine")

##4. Tool to perform a websearch using DuckDuckGo
Name: websearch
Parameters: query
Example usage: websearch("best probiotics for gut health site:bbc.com")
Example usage: websearch("latest Crohn's breakthroughs site:nytimes.com")

ONLY respond with one tool call. Do NOT explain or add any extra text.
Make your query specific, relevant to the condition, and useful.

Each time you search, make sure the search query is different from the previous week's content.
"""
    response = generate(
        model='4o-mini',
        system=system,
        query="What should I send this user this week?",
        temperature=0.9,
        lastk=30,
        session_id='HEALTH_UPDATE_AGENT',
        rag_usage=False
    )
    print(f"🔍 Raw agent response: {response}")
    return response['response']

# --- WEEKLY UPDATE INTERNAL HELPER ---
def weekly_update_internal(user, session_dict):
    """
    Generate the weekly update for a given user.
    Returns a dictionary with the update results including a "text" key for display.
    """
    if user not in session_dict:
        return {"text": "User not found in session."}
    
    user_session = session_dict[user]
    user_info = {
        "name": user,
        "news_sources": user_session.get("news_sources", ["bbc.com", "nytimes.com"]),
        "news_pref": user_session.get("news_pref", "Research News")
    }
    health_info = {
        "condition": user_session.get("condition", "unknown condition")
    }
    
    try:
        agent_response = agent_weekly_update(user_info, health_info)
        print(f"✅ Final agent response: {agent_response}")

        tool_call = extract_tool(agent_response)

        if not tool_call:
            print("⚠️ No valid tool call found. Using fallback.")
            condition = health_info.get("condition")
            pref = user_info.get("news_pref", "Research News").lower()
            tool_map = {
                'youtube': f'youtube_search("{condition} tips")',
                'tiktok': f'tiktok_search("{condition} tips")',
                'instagram reel': f'instagram_search("{condition} tips")',
                'research news': f'websearch("{condition} tips")'
            }
            key = pref if pref in tool_map else "research news"
            tool_call = tool_map.get(key)

        print(f"🔁 Final tool to execute: {tool_call}")
        results = eval(tool_call)
        output = "\n".join(f"• {item}" for item in results)
        text_response = f"Here is your weekly health content digest\n{tool_call}:\n{output}"
        return {
            "text": text_response,
            "agent_response": agent_response,
            "executed_tool": tool_call,
            "results": output
        }
    except Exception as e:
        import traceback
        print("❌ Exception during weekly update:")
        traceback.print_exc()
        return {"text": f"Error: {str(e)}"}


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
        "emergency_email": "📱 What is your doctor's email?",
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
        session_dict[user]["onboarding_stage"] = "emergency_email"
        return {"text": questions["emergency_email"]}

    elif stage == "emergency_email":
        session_dict[user]["emergency_email"] = message
        save_sessions(session_dict)
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
        valid_conditions = ["Crohn's", "Type II Diabetes"]

        if message not in valid_conditions:
            return {"text": "Please click one of the buttons above to continue."}

        session_dict[user]["condition"] = message
        session_dict[user]["onboarding_stage"] = "done"
        save_sessions(session_dict)

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
            Step 2: Ask 3 symptom-related questions that are specific to their condition. Start every question with "Question [what number question you're on])". Ask one question at a time, acknowleding and responding to the user's response before posing the next question. Do not ask all the questions at once.
            Step 3: After every question, **evaluate the user's response**.
            - If their symptoms are normal, reassure them and offer general wellness tips.
            - If their symptoms are abnormal, express concern and provide advice to alleviate discomfort based on your knowledge of their condition.  
            - Begin every response with your advice with "👩‍⚕️ DocBot's Advice: "
            - If the symptoms are **severe**, gently ask the user if they would like to contact their **emergency contact** (**{session_dict[user]['emergency_email']}**).  
            - Address any follow-up questions the user might have before moving on to the question.
            Step 4: After you have concluded asking all 3 questions and answered any follow-up questions from the user, ask, "Would you like to contact your doctor about anything we've discussed, or other symptoms?"
            Step 5: Once the user has provided the subject and content parameters of the email, respond with: "Subject of email: [subject]\nContent of email: [content of email]\nPlease confirm if you're ready to send the email to {session_dict[user]["emergency_email"]}".

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
        rag_threshold='0.5',
        rag_k=5
    )
    # TODO: Determine k value. play around with RAG threshold
    response_text = response.get("response", "⚠️ Sorry, I couldn't process that. Could you rephrase?").strip() if isinstance(response, dict) else response.strip()

    advice = ""
    next_question = ""

    # Extract advice (everything from 'DocBot's Advice:' to just before the next 'Question')
    advice_match = re.search(r"DocBot's Advice:(.*?)(?=Question #\d|$)", response_text, re.DOTALL | re.IGNORECASE)
    # Extract the next question (starting with 'Question #')
    question_match = re.search(r"(Question #\d.*)", response_text, re.DOTALL)
    advice = advice_match.group(1).strip() if advice_match else "Unable to extract advice."
    if advice != "Unable to extract advice.":
        next_question = question_match.group(1).strip() if question_match else ""

    print(response_text)
    print("extracted advice" + advice)
    print("extracted Question" + next_question)
    

    if "docbot's advice" in response_text.lower():
        qa_response = qa_agent(message, advice, user, session_dict)

        if "approved" in qa_response.lower():
            print("in approved")
            pass    
        elif "needs revision" in qa_response.lower():
            match = re.search(r"Suggested revision:\s*(.*)", qa_response)
            if match:
                advice = match.group(1).strip()
                if "next_question" != "END":
                    response_text = "DocBot's Advice: " + advice + "\n\n" + next_question
                else:
                    response_text = advice
            else:
                print("No revised message found.")

        elif "rejected" in qa_response.lower():
            response_text = f"I'm not sure how to evaluate those systems. 🙁 Would you like to contact your doctor at {session_dict[user]['emergency_email']}?"


    if "would you like to contact your doctor" in response_text.lower():
        buttons = [
            {
                "type": "button",
                "text": "Yes ✅",
                "msg": "Yes_email",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_yes"
            },
            {
                "type": "button",
                "text": "No ❌",
                "msg": "No_email",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_no"
            }
        ]
        return {
            "text": response_text + "\n" + "👩‍⚕️ Do you want to contact your Doctor?",
            "attachments": [
                {
                    "collapsed": False,
                    "color": "#e3e3e3",
                    "actions": buttons
                }
            ]
        }
    

    if "Subject of email:" in response_text:
        match = re.search(r"Subject of email[:*\s]*(\S.*)", response_text)  # Capture actual text after "*Subject of email:*"
        if match:
            subject = match.group(1).strip()  # Remove extra spaces
            session_dict[user]['email_subject'] = subject
            save_sessions(session_dict)
    if "Content of email:" in response_text:
        match = re.search(r"Content of email[:*\s]*(\S.*)", response_text)  # Capture actual text after "*Content of email:*"
        if match:
            content = match.group(1).strip()  # Remove extra spaces
            session_dict[user]['email_content'] = content
            save_sessions(session_dict)
    

    if "Please confirm " in response_text:
        buttons = [
            {
                "type": "button",
                "text": "Send it! ✅",
                "msg": "Yes_confirm",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_yes"
            },
            {
                "type": "button",
                "text": "Don't send... ❌",
                "msg": "No_confirm",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_no"
            }
        ]
    
        return {
            "text": response_text,
            "attachments": [
                {
    
                    "collapsed": False,
                    "color": "#e3e3e3",
                    "actions": buttons
                }
            ]
        }
    
    if "Yes_confirm" in message:
        subject = session_dict[user]['email_subject']
        content = session_dict[user]['email_content']
        eval(f"send_email({session_dict[user]["emergency_email"]}, {subject}, {content})")

        response_text = f"Email successfully sent to your doctor at {session_dict[user]["emergency_email"]}!"
        
        session_dict[user]['email_subject'] = ""
        session_dict[user]['email_content'] = ""
        session_dict[user].get("onboarding_stage") == "done"

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
            - Flag any misinformation, unsupported claims, or dangerous suggestions based on your knowledge of the condition.

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
            `"Approved. The message is safe, relevant, and well-phrased."`

            - If the advice has **minor issues**, suggest a revision:
            `"Needs revision: [brief explanation]. Suggested revision: [revised message]"`

            - If the advice contains **major issues**, flag it:
            `"Rejected: [brief explanation of the safety concern or misinformation]"`
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
            Rejected: Suggesting insulin without knowing blood sugar levels could be dangerous. Low blood sugar should not be treated with insulin.  

            Suggested revision:  
            "Dizziness and confusion can be signs of low blood sugar. If you suspect this, try eating something with sugar, like juice or candy. If you don't feel better soon, seek medical help immediately."
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

    return response_text
    
    
    
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



def email_doc(query, user, session_dict):
    print("IN EMAIL DOC")
    sid = session_dict[user]["session_id"]

    system = f"""
    You are an AI agent designed to handle user requests.
    In addition to your own intelligence, you are given access to a set of tools.

    Think step-by-step, breaking down the task into a sequence small steps.

    If you can't resolve the query based on your intelligence, ask the user to execute a tool on your behalf and share the results with you.
    If you want the user to execute a tool on your behalf, strictly only respond with the tool's name and parameters.

    The name of the provided tools and their parameters are given below.
    The output of tool execution will be shared with you so you can decide your next steps.

    ### PROVIDED TOOLS INFORMATION ###
    ##1. Tool to send an email
    Name: send_email
    Parameters: dst, subject, content
    example usage: send_email('xyz@gmail.com', 'greetings', 'hi, I hope you are well'). 
    You are already given the dst parameter. It is {session_dict[user]["emergency_email"]}.
    Once you obtain the subject parameter, respond with: "Subject of email: [subject]"
    The user may require assistance writing the content of the email. Once you obtain the content parameter, respond with: "Content of email: [content of email]"
    After the user has provided all the parameters, respond with: "Subject of email: [subject]\nContent of email: [content of email]"
    Once you have all the parameters to send an email, respond with "Please confirm if you're ready to send the email to {session_dict[user]["emergency_email"]}. 
    """
    if not query:
        return jsonify({"status": "ignored"})

    response = generate(
        model = '4o-mini',
        system = system,
        query = query,
        temperature=0.7,
        lastk=5,
        session_id=sid,
        rag_usage = False)

    response_text = response.get("response", "⚠️ Sorry, I couldn't process that. Could you rephrase?").strip() if isinstance(response, dict) else response.strip()

    subject = content = ""

    if "Subject of email:" in response_text:
        match = re.search(r"Subject of email[:*\s]*(\S.*)", response_text)  # Capture actual text after "*Subject of email:*"
        if match:
            subject = match.group(1).strip()  # Remove extra spaces
    if "Content of email:" in response_text:
        match = re.search(r"Content of email[:*\s]*(\S.*)", response_text)  # Capture actual text after "*Content of email:*"
        if match:
            content = match.group(1).strip()  # Remove extra spaces
    

    if "Yes_confirm" in query:
        eval(f"send_email({session_dict[user]["emergency_email"]}, {subject}, {content})")

        response_text = f"Email successfully sent to your doctor at {session_dict[user]["emergency_email"]}!"
        session_dict[user].get("onboarding_stage") == "done"
        save_sessions(session_dict)
        

    response_obj = {
        "text": response_text
    }
    
    if "Please confirm " in response_text:
        buttons = [
            {
                "type": "button",
                "text": "Send it! ✅",
                "msg": "Yes_confirm",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_yes"
            },
            {
                "type": "button",
                "text": "Don't send... ❌",
                "msg": "No_confirm",
                "msg_in_chat_window": True,
                "msg_processing_type": "sendMessage",
                "button_id": "choose_no"
            }
        ]
        
        response_obj = {
            "text": response_text,
            "attachments": [
                {
    
                    "collapsed": False,
                    "color": "#e3e3e3",
                    "actions": buttons
                }
            ]
        }

    print("response" + response_text)
    print(f"object: {response_obj["text"]}")
    return response_obj
    



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
        print("🔄 Restarted onboarding.")


    if session_dict[user]["onboarding_stage"] != "done":
        response = first_interaction(message, user, session_dict)
        
    elif (message == "No_email") or message == "No_confirm":
        response = {"text": "Alright! That concludes your daily wellness check 😊. Talk to you tomorrow!"}
    
    elif message.lower() == "weekly update":
        if session_dict[user].get("onboarding_stage") == "done":
            update_response = weekly_update_internal(user, session_dict)
            return jsonify(update_response)
        else:
            return jsonify({"text": "Please complete onboarding before requesting a weekly update."})

    else:
        # schedule.every().day.at("09:00").do(llm_daily)
        response = llm_daily(message, user, session_dict)

    
    # Save session data at the end of the request
    save_sessions(session_dict)
    return jsonify(response)


### --- RUN THE FLASK APP --- ###
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)