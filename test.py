import requests

response_main = requests.get("https://subjective-corenda-anika810-2b6c4d1c.koyeb.app/")
print('Web Application Response:\n', response_main.text, '\n\n')


data = {"text":"tell me about tufts"}
response_llmproxy = requests.post("https://subjective-corenda-anika810-2b6c4d1c.koyeb.app/query", json=data)
print('LLMProxy Response:\n', response_llmproxy.text)
