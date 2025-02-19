from llmproxy import pdf_upload

if __name__ == '__main__':
    response = pdf_upload(path = 'greentim.pdf',
        strategy = 'smart')

    print(response)
