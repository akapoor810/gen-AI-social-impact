import requests
from flask import Flask, request, jsonify
from llmproxy import *

app = Flask(__name__)

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

    # Generate medical summary and nutritional recommendations
    sys_instructions = """
    You are a friendly medical assistant that works with patients. Use an
    encouraging and uplifting tone to empathize with patients going through
    the recovery process. Keep responses digestible, limit them to 2-5 sentences.

    You only answer questions related to the medical records provided.
    Summarize the medical records in accessible language. Do not include any
    personal identification information of the patient, including
    Medical Record Number (MRN) and Clinical Service Number (CSN).
    Only include information related to their injury or illness diagnosis.
    If the user asks an unrelated question, remind them to stay on topic and
    ask questions related to the current medical records.
    
    After helping a user understand their medical records, ask them if they 
    would like to share their results in an email with someone. Ask them to
    respond with either "No thanks" or "Yes, send email." Then continue the 
    conversation related to the patient's medical history.
    """

    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query=message,
        temperature=0.0,
        lastk=50,
        session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )

    if "Yes send email" or "Yes, send email" or "Send email" in response:
        # Need to substitute X with someone's name
        query = """
        Send an email to X requesting an extension on asg1?
        Use the tools provided if you want
        """
        while True:
            print("sending email")
            response = agent_email(query)

            # print Response
            print(response)

            user_input = input("Enter Y to continue, N to exit, or provide hint to agent: ").strip().upper()
            if user_input == 'N':
                break
            elif user_input == 'Y':

                # extract tool from agent_email's response
                tool = extract_tool(response)

                # if tool found, execute it using `eval`
                # https://docs.python.org/3/library/functions.html#eval
                if tool:
                    response = eval(tool)
                    print(f"Output from tool: {response}\n\n")        
            else:
                response = user_input

            # Response becomes input for next iteration 
            query = response
            
    response_text = response['response']
    
    return jsonify({"text": response_text})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()
