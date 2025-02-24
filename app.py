import requests
from flask import Flask, request, jsonify
from llmproxy import *

app = Flask(__name__)
SPOONACULAR_API_KEY = "dc28300308864f298356dedd38813ca2"

@app.route('/')
def hello_world():
    return jsonify({"text": 'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    print(f"Message from {user}: {message}")

    # Generate medical summary and nutritional recommendations
    sys_instructions = """
    You are a friendly medical assistant that works with patients. 
    You only answer questions related to the medical records provided.
    Summarize the medical records in accessible language. Do not include any
    personal identification information of the patient, only information 
    related to their injury or illness diagnosis.
    If the user asks an unrelated question, remind them to stay on topic and
    ask questions related to the current medical records.
    
    Identify any key medical concerns and recommend specific nutrients to improve health.
    Ask the user if they are interested in recipe suggestions for these nutrients.
    """

    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query=message,
        temperature=0.0,
        lastk=50,
        session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )

    response_text = response['response']
    # recommended_nutrients = extract_nutrients(response_text)
    
    # if recommended_nutrients:
    #     return jsonify({
    #         "text": response_text + "\n\nWould you like recipes based on these recommendations?",
    #         "attachments": [
    #             {
    #                 "actions": [
    #                     {"text": "Yes, tell me more", "callback_id": "nutrition_yes", "type": "button"},
    #                     {"text": "No thanks", "callback_id": "nutrition_no", "type": "button"}
    #                 ]
    #             }
    #         ]
    #     })
    
    return jsonify({"text": response_text})

@app.route('/button-response', methods=['POST'])
# def button_response():
#     data = request.get_json()
#     action = data.get("callback_id")
#     user = data.get("user_name", "Unknown")
    
#     if action == "nutrition_yes":
#         recommended_nutrients = extract_nutrients(data.get("text", ""))
#         recipe_suggestions = get_recipe_suggestions(recommended_nutrients)
#         return jsonify({"text": recipe_suggestions})
    
#     return jsonify({"text": "Got it! Let me know if you need anything else."})


# def extract_nutrients(response_text):
#     """Extracts recommended nutrients from chatbot response."""
#     nutrient_keywords = ["iron", "vitamin D", "vitamin C", "omega-3", "calcium", "magnesium", "zinc", "fiber", "protein", "folate", "B12", "potassium"]
#     return [nutrient for nutrient in nutrient_keywords if nutrient.lower() in response_text.lower()]


# def get_recipe_suggestions(nutrients):
#     """Fetches recipe suggestions based on nutrients."""
#     recipes = []
#     for nutrient in nutrients:
#         recipes += fetch_recipes(nutrient)
    
#     if recipes:
#         return "Here are some recipes based on your recommended nutrients:\n\n" + "\n".join(f"- [{r['name']}]({r['url']})" for r in recipes)
#     else:
#         return "Sorry, I couldn't find recipes for the recommended nutrients."


# def fetch_recipes(nutrient):
#     """Fetches recipes rich in a specific nutrient using Spoonacular API."""
#     nutrient_mapping = {
#         "iron": "minIron=5",
#         "vitamin D": "minVitaminD=10",
#         "vitamin C": "minVitaminC=10",
#         "omega-3": "minOmega3=0.5",
#         "calcium": "minCalcium=100",
#         "magnesium": "minMagnesium=50",
#         "zinc": "minZinc=5",
#         "fiber": "minFiber=5",
#         "protein": "minProtein=15",
#         "folate": "minFolate=100",
#         "B12": "minVitaminB12=2",
#         "potassium": "minPotassium=300"
#     }
    
#     if nutrient not in nutrient_mapping:
#         return []
    
#     url = f"https://api.spoonacular.com/recipes/findByNutrients?{nutrient_mapping[nutrient]}&number=3&apiKey={SPOONACULAR_API_KEY}"
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         data = response.json()
#         return [{"name": recipe["title"], "url": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']}"} for recipe in data]
#     else:
#         return []

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()
