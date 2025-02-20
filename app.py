import requests
from flask import Flask, request, jsonify
from llmproxy import *

app = Flask(__name__)

@app.route('/')
def hello_world():
   return jsonify({"text": 'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    pdf_upload(path='AMB-After-Visit-Summary.PDF',
               session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
               strategy='smart')

    pdf_upload(path='Past-Visit-Details.pdf',
               session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
               strategy='smart')

    sys_instructions = """You are a friendly medical assistant that works
    with patients of all ages and with all types of medical histories. 
    You only answer questions related to the medical records provided. 
    Summarize the medical records in language that is accessible for a 
    general audience. If the user asks an unrelated 
    question, remind them that you only answer queries related to the medical
    records provided.
    
    Ask the user if they are interested in nutritional recommendations to 
    augment their diet to protect against related medical issues in the future. 
    Include information about specific nutrients to supplement their 
    diet with."""

    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})

    print(f"Message from {user}: {message}")

    # Generate a response using LLMProxy
    response = generate(
        model='4o-mini',
        system=sys_instructions,
        query=message,
        temperature=0.0,
        lastk=0,
        session_id='comp150-cdr-2025s-Ic636oMxYQJviNamr6P6DAmWO45leqi3ZRcBLrl2',
        rag_usage=True,
        rag_threshold='0.3',
        rag_k=5
    )

    response_text = response['response']
    print(response_text)

    # Check if chatbot suggested nutritional recommendations
    if "Would you like nutritional recommendations?" in response_text:
        return jsonify({
            "text": response_text,
            "attachments": [
                {
                    "text": "Would you like nutritional recommendations?",
                    "actions": [
                        {
                            "type": "button",
                            "text": "Yes, tell me more",
                            "msg": "/nutrition_yes"
                        },
                        {
                            "type": "button",
                            "text": "No thanks",
                            "msg": "/nutrition_no"
                        }
                    ]
                }
            ]
        })

    return jsonify({"text": response_text})

@app.route('/nutrition_yes', methods=['POST'])
# Handles the user's request for nutritional recommendations.
def handle_nutrition_yes():
    data = request.get_json()
    user = data.get("user_name", "Unknown")

    recommended_nutrients = ["iron", "vitamin D", "omega-3"]  # Example, could be dynamically generated
    recipe_results = []

    for nutrient in recommended_nutrients:
        recipes = fetch_recipes(nutrient)
        if recipes:
            recipe_results.append(f"**{nutrient.upper()}**-rich recipes:\n" +
                                  "\n".join([f"- [{r['name']}]({r['url']})" for r in recipes]))

    response_text = "Here are some recipes to help you get the recommended nutrients:\n" + "\n\n".join(recipe_results)

    return jsonify({"text": response_text})

@app.route('/nutrition_no', methods=['POST'])
def handle_nutrition_no():
    """Handles the user's rejection of nutritional recommendations."""
    return jsonify({"text": "No problem! Let me know if you need anything else."})

def fetch_recipes(nutrient):
    """Fetches recipes rich in a specific nutrient using the Spoonacular API."""
    SPOONACULAR_API_KEY = "dc28300308864f298356dedd38813ca2"
    
    # Mapping nutrients to Spoonacular query parameters
    nutrient_mapping = {
        "iron": "minIron=5",       # Adjust threshold as needed
        "vitamin D": "minVitaminD=10",
        "vitamin C": "minVitaminC=10",
        "omega-3": "minOmega3=0.5",
        "calcium": "minCalcium=100",
        "magnesium": "minMagnesium=50",
        "zinc": "minZinc=5",
        "fiber": "minFiber=5",
        "protein": "minProtein=15",
        "folate": "minFolate=100",
        "B12": "minVitaminB12=2",
        "potassium": "minPotassium=300"
    }

    if nutrient not in nutrient_mapping:
        return []

    url = f"https://api.spoonacular.com/recipes/findByNutrients?{nutrient_mapping[nutrient]}&number=3&apiKey={SPOONACULAR_API_KEY}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [{"name": recipe["title"], "url": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']}"} for recipe in data]
    else:
        return []


@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()