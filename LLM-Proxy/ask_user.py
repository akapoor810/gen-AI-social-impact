from llmproxy import *

if __name__ == '__main__':
    question = input("Please enter a question: ")
    sys_instructions = input("Please specify any system instructions: ")

    chat_res = generate(model = '4o-mini',
        system = sys_instructions,
        query = question,
        temperature=0.0,
        lastk=0,
        session_id='GenericSession')
    
    claude_res = generate(model = 'anthropic.claude-3-haiku-20240307-v1:0',
        system = sys_instructions,
        query = question,
        temperature=0.0,
        lastk=0,
        session_id='GenericSession')

    phi_res = generate(model = 'azure-phi3',
        system = sys_instructions,
        query = question,
        temperature=0.0,
        lastk=0,
        session_id='GenericSession')

    print(f"OpenAI GPT4o-mini: {chat_res}\n")
    print(f"Anthropic Claude Haiku: {claude_res}\n")
    print(f"Microsoft Phi3: {phi_res}")