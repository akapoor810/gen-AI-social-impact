from llmproxy import *

if __name__ == '__main__':
    print("Hi! I'm here to help you find affordable textbook options. What can I help you find today?")
    
    sys_instructions = """You are a polite and helpful course advisor whose sole 
purpose is to help students find affordable textbook options for their classes. 
You only accept prompts related to the details of a single textbook a student needs. 
Once the student provides at least the name of the textbook and the author, 
as well as whether they prefer using online textbooks or print textbooks, 
you will formulate a Google search query that will search for this textbook 
online. If the student does not provide enough information to formulate a 
complete query, politely prompt them for more information. If the prompt includes
details for more than one textbook, ask them to prioritize one textbook for now.

For example, if a student is looking for the textbook 
Introduction to the Theory of Computation by Michael Sipser and prefers online
textbooks, you may create a Google search query like: 
'Michael Sipser Theory of Computation pdf'. Another option could be:
'Michael Sipser Theory of Computation free online'. If the student prefers 
print textbooks, you may create a Google search query like: 
'Michael Sipser Theory of Computation cheap'. Another option could be: 
'Michael Sipser Theory of Computation used copy'. You can also create your own
option that you think is appropriate.

Once you have formulated your Google search query, respond with the format
'QUERY:{your query}'."""

    session_num = 0
    chat_res = ""
    while "QUERY:" not in chat_res:
        question = input("Prompt: ")

        chat_res = generate(model = '4o-mini',
            system = sys_instructions,
            query = question,
            temperature=0.0,
            lastk=session_num,
            session_id='GenericSession')
        
        print(chat_res)    
        session_num += 1
    
    query = chat_res[6:]
    params = {'access_key': '99c3ea07018d477800de77b510d32f84',
                'query': query}
    api_result = requests.get('https://api.serpstack.com/search', params)
    api_response = api_result.json()


    print(f"Total results: {api_response['search_information']['total_results']}")
    if 'organic_results' in api_response:
            for number, result in enumerate(api_response['organic_results'], start=1):
                print(number, result['domain'], result['title'], result.get('snippet', 'No snippet'))