import requests
from flask import Flask, request, jsonify
from llmproxy import *
from example_agent_tool import extract_tool

app = Flask(__name__)

# global variable {user}
session_dict = {}

@app.route('/')
def hello_world():
    return jsonify({"text": 'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    print(f"Message from {user}: {message}")
    if user not in session_dict:
        session_dict[user] = "{user}-session"
    sid = session_dict[user]


    # RAG
    pdf_upload(path = 'AMB-After-Visit-Summary.PDF',
        session_id = 'sid',
        strategy = 'smart')
    
    pdf_upload(path = 'Past-Visit-Details.pdf',
        session_id = 'sid',
        strategy = 'smart')


    sys_instructions = """
    You are a friendly medical assistant that works with patients. Use an
    encouraging and uplifting tone to empathize with patients going through
    the recovery process. Make the response as engaging as possible and include
    relevant emojis to convey an upbeat and positive attitude.
    Keep responses digestible, limit them to 2-5 sentences. Make the UI of 
    your response aesthetically pleasing.

    You only answer questions related to the medical records that are provided.
    Summarize the medical records in accessible language. Do not include any
    personal identification information of the patient, including
    Medical Record Number (MRN) and Clinical Service Number (CSN).
    Only include information related to their injury or illness diagnosis.
    If the user asks an unrelated question, remind them to stay on topic and
    ask questions related to the current medical records.
    
    After helping a user understand their medical records, ask them if they 
    would like to share their results in an email with someone. Ask them to
    respond with either "No" or "Yes, send email." Then continue the 
    conversation related to the patient's medical history.

    If the user wants to send the prepared draft of the email, ask them to 
    confirm sending by responding with "Confirm".

    Begin every conversation by introducing yourself and explicitly explaining 
    your purpose and what you do. Offer to assist the user with any relevant 
    queries. 
    """

    if "email" in message.lower():
    # or message == "yes_email": #respond with a button for possible further interaction
        response = agent_email(message, sid)
        return jsonify({"text": response})
        
        # response = { "text": response_text,
        #             "attachments": [
        #                     {
        #                     "text": "You have selected: ✅ Yes!",
        #                     "actions": [
        #                         {
        #                         "type": "button",
        #                         "text": "Thanks for the feedback 😃",
        #                         "msg": "post_yes_clicked",
        #                         "msg_in_chat_window": True,
        #                         "msg_processing_type": "sendMessage"
        #                         }
        #                     ]
        #                     }
        #                 ]
        #             }
        
    if "confirm" in message.lower():
        response = agent_email(message, sid)
        
        tool = extract_tool(response)
        print("Confirming sending email: ", response, tool)
        if tool:
            response = eval(tool)
        return jsonify({"text": response})

    # elif message == "no_email": # respond with a text
    #     response = {
    #                 "text": "You have selected: ❌ No! Let us know if you want to send an email in the future."
    #     }
    # else:
        #Generate a response (you can integrate with AI/chatbot here)
    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query=message,
        temperature=0.0,
        lastk=3,
        session_id=sid,
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )

    response_text = response['response']
    response = {
                "text": response_text,
                "attachments": [
                    {
                        "title": "Email Options",
                        "text": "Would you like to email these results to someone?",
                        "actions": [
                            {
                                "type": "button",
                                "text": "✅ Yes",
                                "msg": "yes_email",
                                "msg_in_chat_window": True,
                                "msg_processing_type": "sendMessage",
                                "button_id": "yes_button"
                            },
                            {
                                "type": "button",
                                "text": "❌ No",
                                "msg": "no_email",
                                "msg_in_chat_window": True,
                                "msg_processing_type": "sendMessage"
                            }
                        ]
                    }
                ]
    }

    response_text = response['response']
    return jsonify({"text": response_text})




# Tool to send an email
# This has been written based on the Tufts EECS email infrastructure
# Can be modified for other email clients (e.g., gmail, yahoo)
def send_email(dst, subject, content):

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


# agent program to handle user requests
def agent_email(query, sid):
    
    system = """
    You are an AI agent designed to handle user requests.
    In addition to your own intelligence, you are given access to a set of tools.

    Think step-by-step, breaking down the task into a sequence small steps.

    If you can't resolve the query based on your intelligence, ask the user to execute a tool on your behalf and share the results with you.
    If you want the user to execute a tool on your behalf, strictly only respond with the tool's name and parameters.
    Example response for using tool: websearch('weather in boston today')

    The name of the provided tools and their parameters are given below.
    The output of tool execution will be shared with you so you can decide your next steps.

    ### PROVIDED TOOLS INFORMATION ###
    ##1. Tool to send an email
    Name: send_email
    Parameters: dst, subject, content
    example usage: send_email('xyz@gmail.com', 'greetings', 'hi, I hope you are well'). 
    Once you have all the parameters to send an email, ask the user to confirm 
    they want to send the email by typing "Confirm". 
    If the user types "Confirm," begin your response with 
    "send_email(dst, subject, content)" with the parameters filled in 
    appropriately.

    """
    if not query:
        return jsonify({"status": "ignored"})

    response = generate(model = '4o-mini',
        system = system,
        query = query,
        temperature=0.7,
        lastk=5,
        session_id=sid,
        rag_usage = False)

    try:
        return response['response']
    except Exception as e:
        print(f"Error occured with parsing output: {response}")
        raise e


@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()
