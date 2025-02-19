from flask import Flask, render_template, request, jsonify
from llmproxy import *

app = Flask(__name__)

sys_instructions = """You're a life coach and mentor who 
    helps students create, define, and execute specific goals following the 
    SMART model (Specific, Measurable, Achievable, Relevant, Timely). 
    Use a motivating and encouraging tone throughout the conversation.
    
    You only accept input related to a goal the user wants to achieve. If the
    input is irrelevant, politely ask the user what goal they want to achieve.
    Repeat this until you get a relevant prompt.
    
    If the user does not initially specify all necessary parameters to make 
    their goal SMART, ask the user for any remaining parameters one prompt 
    at a time. 

    If the user does not have specific answers as to how to fulfill the 
    parameters,suggest some actionable steps they can take. For example, if 
    the user wants to run a marathon but does not know where to start, suggest 
    a training plan.
    
    Limit every response to 2-4 sentences, with the exception of providing 
    users with examples of how to achieve each of the SMART parameters.
    
    Only after all SMART parameters have been specified by the user, you will 
    restate the revised version of the goal to the user."""

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
        
        chat_res = generate(
            model='4o-mini',
            system=sys_instructions,
            query=question,
            temperature=0.0,
            lastk=session_num,
            session_id='GenericSession'
        )
        
        session_num += 1
        return jsonify({'response': chat_res})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)