from llmproxy import generate

if __name__ == '__main__':
    response = generate(model = '4o-mini',
        system = 'Answer my question in a funny manner',
        query = 'Who are the Jumbos?',
        temperature=0.0,
        lastk=0,
        session_id='GenericSession')

    print(response)