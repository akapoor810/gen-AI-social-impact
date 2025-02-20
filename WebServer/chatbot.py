from llmproxy import *

if __name__ == '__main__':
    pdf_upload(path = 'AMB-After-Visit-Summary.PDF',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'ED-After-Visit-Summary.PDF',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'Past-Visit-Details.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    sys_instructions = """Review the medical records I have provided. Summarize
    them in language that is accessible for a general audience and not using
    overly technical medical vocabulary. Present recommendations for how I can
    augment my diet in order to avoid future related medical issues. Include 
    information about specific nutrients.
    
    Ask the user if they want any recommendations for recipes to achieve the
    nutrient goals you outline. If they respond yes, formulate a string in the 
    following format: 'QUERY: """

    print("Hi! How can I help you today?")
    question = input("Response: ")
    

    session_num = 0
    while True:
        chat_res = generate(model = '4o-mini',
            system = sys_instructions,
            query = question,
            temperature=0.0,
            lastk=session_num,
            session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
            rag_usage=True,
            rag_threshold='0.5',
            rag_k=5)
        
        print("Response: ", chat_res['response'])
        print("RAG Context: ", chat_res['rag_context'])
        session_num += 1
        question = input("Prompt: ")