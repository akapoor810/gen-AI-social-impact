from llmproxy import *
from example_agent_tool import extract_tool

# Tool to send an email
# This has been written based on the Tufts EECS email infrastructure
# Can be modified for other email clients (e.g., gmail, yahoo)
def send_email(dst, subject, content):
    import os, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import json
 
    # Email configuration
    smtp_server = "smtp.eecs.tufts.edu"  # e.g., mail.yourdomain.com
    smtp_port = 587  # Usually 587 for TLS, 465 for SSL
    sender_email = "akapoo02@eecs.tufts.edu"
    receiver_email = dst

    # Add email password to config.json
    with open('config.json', 'r') as file:
        config = json.load(file)

    password = config['password']

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    body = content
    msg.attach(MIMEText(body, "plain"))

    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection (use only if the server supports TLS)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        print("there was an error")
        return f"Error: {e}" 


# Tool to perform a websearch using duckduckgo
def websearch(query):
    from duckduckgo_search import DDGS

    # Initialize the search client
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))

    return [result["href"] for result in results]


# agent program to handle user requests
def agent_email(query):
    
    system = """
    You are an AI agent designed to handle user requests.
    In addition to your own intelligence, you are given access to a set of tools.

    Think step-by-step, breaking down the task into a sequence small steps.

    If you can't resolve the query based on your intelligence, ask the user to execute a tool on your behalf and share the results with you.
    If you want the user to execute a tool on your behalf, strictly only respond with the tool's name and parameters.
    Example response for using tool: websearch('weather in boston today')

    The name of the provided tools and their parameters are given below.
    The output of tool execution will be shared with you so you can decide your next steps.

    ### PROVIDED TOOLS INFORMATION ###
    ##1. Tool to send an email
    Name: send_email
    Parameters: dst, subject, content
    example usage: send_email('xyz@gmail.com', 'greetings', 'hi, I hope you are well')

    """

    response = generate(model = '4o-mini',
        system = system,
        query = query,
        temperature=0.7,
        lastk=10,
        session_id='DEMO_AGENT_EMAIL',
        rag_usage = False)

    try:
        print(response)
        return response['response']
    except Exception as e:
        print(f"Error occured with parsing output: {response}")
        raise e








if __name__ == '__main__':
    pdf_upload(path = 'AMB-After-Visit-Summary.PDF',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
    pdf_upload(path = 'Past-Visit-Details.pdf',
        session_id = 'comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        strategy = 'smart')
    
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

    while True:
        question = input("Prompt: ")
        if "email" in question.lower():
            # Need to substitute X with someone's name
            query = """
            Send an email to X sharing information from medical records
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
        
        response = generate(model = '4o-mini',
            system = sys_instructions,
            query = question,
            temperature=0.0,
            lastk=100,
            session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
            rag_usage=True,
            rag_threshold='0.3',
            rag_k=5)



        print(response['response'])