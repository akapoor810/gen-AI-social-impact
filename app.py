import requests
from flask import Flask, request, jsonify
from llmproxy import generate
from example_send_msg_to_rc import send_email

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    user_id = data.get("user_id")
    
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    print(f"Message from {user}: {message}")
    
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
    
    return jsonify({
        "text": response_text,
        "attachments": [{
            "text": "Would you like to share your results via email?",
            "actions": [
                {
                    "type": "button",
                    "text": "Share via Email",
                    "msg": f"/share {user_id}",
                    "msg_in_chat_window": True
                }
            ]
        }]
    })

@app.route('/share', methods=['POST'])
def share_via_email():
    data = request.get_json()
    user_id = data.get("user_id")
    email = data.get("email")
    
    if not email:
        return jsonify({"text": "Please provide an email address to send the results."})
    
    user_result = "Your medical summary is ready."
    
    send_email(email, "Your Medical Summary", user_result)
    
    return jsonify({"text": "Your results have been shared via email!"})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run(threaded=True)
