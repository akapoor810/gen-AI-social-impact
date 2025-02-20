import requests
from flask import Flask, request, jsonify
from llmproxy import *

app = Flask(__name__)

@app.route('/')
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    pdf_upload(path = 'AMB-After-Visit-Summary.PDF',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'Past-Visit-Details.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    sys_instructions = """You are a medical assistant. 
    Review the medical records I have provided. Summarize
    them in language that is accessible for a general audience and not using
    overly technical medical vocabulary. Present recommendations for how I can
    augment my diet in order to avoid future related medical issues. Include 
    information about specific nutrients. Respond in all normal case."""

    data = request.get_json() 

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    print(data)

    # Ignore bot messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})

    print(f"Message from {user} : {message}")


    # Generate a response using LLMProxy
    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query= message,
        temperature=0.0,
        lastk=0,
        session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )

    response_text = response['response']
    
    # Send response back
    print(response_text)

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()