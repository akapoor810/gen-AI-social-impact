from llmproxy import *

if __name__ == '__main__':
    pdf_upload(path = 'cracking-the-coding-interview.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'system-design-interview.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'sean-prashad-patterns.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'designgurus-system-design.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'algomaster-patterns.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    sys_instructions = """You are a career coach and interview coach for new
    graduates aspiring to become software engineers at top technical companies
    such as FAANG, Microsoft, Bloomberg, and more. You should aim to be as 
    detailed and thorough as possible in your responses and prepare your
    users to be able to solve any coding or system design problem they 
    encounter in interviews."""

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
            rag_threshold='0.3',
            rag_k=5)
        
        print("Response: ", chat_res['response'])
        print("RAG Context: ", chat_res['rag_context'])
        session_num += 1
        question = input("Prompt: ")