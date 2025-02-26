from flask import Flask, render_template, request, jsonify
from llmproxy import *

app = Flask(__name__)

sys_instructions = """You are a career coach and interview coach for new
    graduates aspiring to become software engineers at top technical companies
    such as FAANG, Microsoft, Bloomberg, and more. You should aim to be as 
    detailed and thorough as possible in your responses and prepare your
    users to be able to solve any coding or system design problem they 
    encounter in interviews. Your language of choice is Python should the user
    ask you to code a solution."""

session_num = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        global session_num
        data = request.get_json()  # Get JSON data instead of form data
        question = data['question']
        
        chat_res = generate(model = '4o-mini',
            system = sys_instructions,
            query = question,
            temperature=0.0,
            lastk=session_num,
            session_id='rag-id',
            rag_usage=True,
            rag_threshold='0.3',
            rag_k=5
        )
        
        session_num += 1
        return jsonify({'response': chat_res['response']})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    pdf_upload(path = 'cracking-the-coding-interview.pdf',
        session_id = 'rag-id',
        strategy = 'smart')
    
    pdf_upload(path = 'system-design-interview.pdf',
        session_id = 'rag-id',
        strategy = 'smart')
    
    pdf_upload(path = 'sean-prashad-patterns.pdf',
        session_id = 'rag-id',
        strategy = 'smart')
    
    pdf_upload(path = 'designgurus-system-design.pdf',
        session_id = 'rag-id',
        strategy = 'smart')
    
    pdf_upload(path = 'algomaster-patterns.pdf',
        session_id = 'rag-id',
        strategy = 'smart')
    
    app.run(debug=True)