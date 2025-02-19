from flask import Flask, render_template, request, jsonify
from llmproxy import *
import requests

app = Flask(__name__)


sys_instructions = """You are a polite and helpful course advisor whose sole 
purpose is to help students find affordable textbook options for their classes. 
You only accept prompts related to the details of a single textbook a student needs. 
Once the student provides at least the name of the textbook and the author, 
as well as whether they prefer using online textbooks or print textbooks, 
you will formulate a Google search query that will search for this textbook 
online. Any other publication information is also welcome in the prompt if 
the student has access to it. If the student does not provide enough 
information to formulate a complete query, politely prompt them for more 
information. If the prompt includes details for more than one textbook, 
ask them to prioritize one textbook for now.

For example, if a student is looking for the textbook 
Introduction to the Theory of Computation by Michael Sipser and prefers online
textbooks, you may create a Google search query like: 
'Michael Sipser Theory of Computation pdf'. Another option could be:
'Michael Sipser Theory of Computation free online'. If the student prefers 
print textbooks, you may create a Google search query like: 
'Michael Sipser Theory of Computation cheap'. Another option could be: 
'Michael Sipser Theory of Computation used copy'. You can also create your own
option that you think is appropriate.

Respond with the Google search query you formulated."""

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
        
        params = {'access_key': '99c3ea07018d477800de77b510d32f84',
                  'query': chat_res}
        api_result = requests.get('http://api.serpstack.com/search', params)
        api_response = api_result.json()

        print(f"Total results: {api_response['search_information']['total_results']}")
        for number, result in enumerate(api_response['organic_results'], start=1):
            print(number, result ['title'])

        session_num += 1
        return jsonify({'response': chat_res})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)