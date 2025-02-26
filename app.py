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
    
    # return jsonify({
    #     "text": response_text,
    #     "attachments": [{
    #         "text": "Would you like to share your results via email?",
    #         "actions": [
    #             {
    #                 "type": "button",
    #                 "text": "Share via Email",
    #                 "msg": f"/share {user_id}",
    #                 "msg_in_chat_window": True
    #             }
    #         ]
    #     }]
    # })

@app.route('/share', methods=['POST'])
def agent_email():
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
    Parameters: src, dst, subject, content
    example usage: send_email('abc@gmail.com', 'xyz@gmail.com', 'greetings', 'hi, I hope you are well')"""

    
    query = """
    Send an email to X to patient's medical information?
    Use the tools provided if you want
    """

    response = generate(model = '4o-mini',
        system = system,
        query = query,
        temperature=0.7,
        lastk=10,
        session_id='DEMO_AGENT_EMAIL',
        rag_usage = False)

    try:
        return response['response']
    except Exception as e:
        print(f"Error occured with parsing output: {response}")
        raise e
    return 
    
    # user_result = "Your medical summary is ready."
    
    # send_email(email, "Your Medical Summary", user_result)
    
    # return jsonify({"text": "Your results have been shared via email!"})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run(threaded=True)
