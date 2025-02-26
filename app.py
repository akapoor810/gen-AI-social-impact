import os
import requests
import json
import threading
from flask import Flask, request, jsonify
from llmproxy import generate
from concurrent.futures import ThreadPoolExecutor

# Initialize executor for handling concurrent users
executor = ThreadPoolExecutor(max_workers=10)

app = Flask(__name__)

# Email sending function adapted from example_agent_tool.py
def send_email(src, dst, subject, content):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Email configuration
    smtp_server = "smtp-tls.eecs.tufts.edu"  # Modify for your email server
    smtp_port = 587  # Usually 587 for TLS, 465 for SSL
    sender_email = src
    receiver_email = dst

    # Get email password from environment variables for security
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        # Fall back to config file if environment variable not set
        try:
            with open('config.json', 'r') as file:
                config = json.load(file)
            password = config.get('password')
        except:
            return "Error: Email password not found"

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
        server.starttls()  # Secure the connection
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        return f"Error: {e}"

# Function to send message to RocketChat
def send_to_rocketchat(channel, message, attachments=None):
    url = "https://chat.genaiconnect.net/api/v1/chat.postMessage"
    
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": os.environ.get("RC_token"),
        "X-User-Id": os.environ.get("RC_userId")
    }
    
    payload = {
        "channel": channel,
        "text": message
    }
    
    if attachments:
        payload["attachments"] = attachments
        
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Tool extraction function adapted from example_agent_tool.py
def extract_tool(text):
    import re

    match = re.search(r'send_email\([^)]*\)', text)
    if match:
        return match.group()
    
    return None

# Agent function to handle email requests
def agent_email(query, user_id):
    system = """
    You are an AI medical assistant that can help patients with their medical records.
    You can also help send emails on behalf of patients to their healthcare providers.
    
    If the user asks to send an email, follow these steps:
    1. Ask who they want to send the email to (if not provided)
    2. Ask what subject they want for the email (if not provided)
    3. Ask what content they want in the email (if not provided)
    4. Summarize the email details and ask for confirmation
    5. Once confirmed, use the send_email tool
    
    When you need to use the tool, respond with ONLY the tool call in this format:
    send_email('user@email.com', 'recipient@email.com', 'Email Subject', 'Email Content')
    
    For any non-email related questions, respond as a helpful medical assistant.
    """

    response = generate(
        model='4o-mini',
        system=system,
        query=query,
        temperature=0.7,
        lastk=10,
        session_id=f'EMAIL_AGENT_{user_id}',
        rag_usage=False
    )

    try:
        return response['response']
    except Exception as e:
        print(f"Error occurred with parsing output: {response}")
        return f"I'm sorry, I encountered an error: {str(e)}"

# Process user message asynchronously
def process_message(user, user_id, message):
    # Check if message is email-related
    if "email" in message.lower() or "send" in message.lower() and "message" in message.lower():
        response_text = agent_email(message, user_id)
        
        # Check if response contains a tool call
        tool = extract_tool(response_text)
        if tool:
            try:
                # Execute the tool
                result = eval(tool)
                # Send confirmation back to user
                return f"✅ {result}"
            except Exception as e:
                return f"I encountered an error while trying to send the email: {str(e)}"
        else:
            # Add share button if needed
            if "would you like to share" in response_text.lower() or "share these results" in response_text.lower():
                attachments = [{
                    "actions": [{
                        "type": "button",
                        "text": "Share Results",
                        "msg": "Yes, please share my results",
                        "msg_in_chat_window": True
                    }]
                }]
                # Send message with button
                send_to_rocketchat(f"@{user}", response_text, attachments)
                return None  # Already sent via RocketChat API
            return response_text
    else:
        # Regular medical assistance
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
        encouraging and engaging tone to uplift patients during this time of
        recovery.
        
        If the user might benefit from sharing their results, mention that they can
        click the "Share Results" button to share via email.
        """
        
        response = generate(
            model='4o-mini',
            system=sys_instructions,
            query=message,
            temperature=0.0,
            lastk=50,
            session_id=f'MEDICAL_ASSISTANT_{user_id}',
            rag_usage=True,
            rag_threshold='0.3',
            rag_k=5
        )
        
        response_text = response['response']
        
        # Check if we should add a share button
        if "records" in message.lower() or "results" in message.lower() or "summary" in message.lower():
            attachments = [{
                "actions": [{
                    "type": "button",
                    "text": "Share Results",
                    "msg": "I'd like to share my medical results via email",
                    "msg_in_chat_window": True
                }]
            }]
            # Send message with button
            send_to_rocketchat(f"@{user}", response_text, attachments)
            return None  # Already sent via RocketChat API
            
        return response_text

@app.route('/')
def hello_world():
    return jsonify({"text": 'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    user_id = data.get("user_id", "unknown_user")
    message = data.get("text", "")
    
    # Ignore bot messages or empty messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    print(f"Message from {user}: {message}")
    
    # Handle button clicks
    if message.startswith("I'd like to share my medical results") or message.startswith("Yes, please share my results"):
        # Submit to executor to handle concurrently
        future = executor.submit(
            agent_email, 
            f"The user {user} wants to share their medical results via email. Ask them who they want to send it to.", 
            user_id
        )
        response_text = future.result()
        return jsonify({"text": response_text})
    
    # Submit to executor to handle concurrently
    future = executor.submit(process_message, user, user_id, message)
    response_text = future.result()
    
    # If None is returned, message was already sent via RocketChat API
    if response_text is None:
        return jsonify({"status": "sent_via_api"})
        
    return jsonify({"text": response_text})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    # Use threaded=True for better handling of concurrent requests
    app.run(threaded=True)