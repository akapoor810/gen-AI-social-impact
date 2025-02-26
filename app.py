import requests
from flask import Flask, request, jsonify
from llmproxy import generate
from example_send_msg_to_rc import send_email, send_typing_indicator  # Added typing indicator function
import threading

app = Flask(__name__)

# Store user session data
task_sessions = {}

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    user_id = data.get("user_id")
    
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    print(f"Message from {user}: {message}")
    
    # Show typing indicator
    send_typing_indicator(user_id, typing=True)
    
    sys_instructions = """
    You are a friendly medical assistant that works with patients.
    You only answer questions related to the medical records provided.
    Summarize the medical records in accessible language. Do not include any
    personal identification information of the patient, only information
    related to their injury or illness diagnosis.
    Do not include Medical Record Number (MRN) or Clinical Service Number (CSN).
    If the user asks an unrelated question, remind them to stay on topic and
    ask questions related to the current medical records.
    Keep your responses relatively short, between 2-4 sentences. Use an
    encouraging and engaging tone to uplift patients during this time of recovery.
    """
    
    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query=message,
        temperature=0.0,
        lastk=50,
        session_id=f"session-{user_id}",
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )
    
    response_text = response['response']
    
    # Stop typing indicator
    send_typing_indicator(user_id, typing=False)
    
    # Store session response
    task_sessions[user_id] = response_text
    
    return jsonify({
        "text": response_text,
        "attachments": [{
            "text": "Would you like a human to review your results before sharing via email?",
            "actions": [
                {
                    "type": "button",
                    "text": "Request Human Review",
                    "msg": f"/review {user_id}",
                    "msg_in_chat_window": True
                },
                {
                    "type": "button",
                    "text": "Share via Email",
                    "msg": f"/share {user_id}",
                    "msg_in_chat_window": True
                }
            ]
        }]
    })

@app.route('/review', methods=['POST'])
def request_human_review():
    data = request.get_json()
    user_id = data.get("user_id")
    
    if user_id not in task_sessions:
        return jsonify({"text": "No results found for review."})
    
    user_result = task_sessions[user_id]
    
    return jsonify({"text": "A human assistant will review your response shortly.", "attachments": [{
        "text": f"Review needed for user {user_id}: {user_result}",
        "actions": [{
            "type": "button",
            "text": "Approve and Send",
            "msg": f"/approve {user_id}",
            "msg_in_chat_window": True
        }]
    }]})

@app.route('/approve', methods=['POST'])
def approve_and_send():
    data = request.get_json()
    user_id = data.get("user_id")
    email = data.get("email")
    
    if user_id not in task_sessions:
        return jsonify({"text": "No results found to share."})
    
    user_result = task_sessions[user_id]
    
    def send_email_task():
        send_email(email, "Your Medical Summary", user_result)
    
    threading.Thread(target=send_email_task).start()
    
    return jsonify({"text": "Your results have been approved and shared via email!"})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run(threaded=True)