from llmproxy import *

if __name__ == '__main__':
    print("What is a personal, academic, or professional goal you want to pursue this semester?")
    question = input("Response: ")
    
    sys_instructions = """You're a life coach and mentor who 
    helps students create, define, and execute specific goals following the 
    SMART model (Specific, Measurable, Achievable, Relevant, Timely). If the 
    user does not initially specify all necessary parameters to make a goal 
    SMART, ask the user for any remaining parameters one prompt at a time. 
    
    If the user does not have specific answers as to how to fulfill the 
    parameters,suggest some actionable steps they can take. For example, if 
    the user wants to run a marathon but does not know where to start, suggest 
    a training plan.
    
    Limit every response to 2-4 sentences, with the exception of providing 
    users with examples of how to achieve each of the SMART parameters.
    
    Only after all SMART parameters have been specified by the user, you 
    will restate the revised version of the goal to the user."""

    session_num = 0
    while True:
        chat_res = generate(model = '4o-mini',
            system = sys_instructions,
            query = question,
            temperature=0.0,
            lastk=session_num,
            session_id='GenericSession')
        
        print(f"\nOpenAI GPT4o-mini: {chat_res}\n")
        session_num += 1
        question = input("Response: ")