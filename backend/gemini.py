import os
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
from flask import jsonify, Flask, request
from dotenv import load_dotenv

from logger import setup_logger
from config_class import EndpointInfo, ApiAnalysis
from prompts.rest_prompt import (
    RestAssuredPrompts,
)
from db.services.test_case import TestCaseService

# Initialize logger
logger = setup_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
logger.info("Flask app initialized.")

test_case_service = TestCaseService()
logger.info("TestCaseService initialized.")


def setup_llm(api_key=None)-> ChatGoogleGenerativeAI:
    """
    Configure et retourne l'instance du modèle LLM.

    Arguments:
        api_key: Clé API Google Gemini (facultative, sinon utilise la variable d'environnement)

    Retourne:
        Une instance du modèle Gemini configurée

    Lève:
        ValueError: Si aucune clé API n'est trouvée
    """
    # Utiliser la clé fournie ou rechercher dans les variables d'environnement
    api_key = api_key or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        logger.error(
            "Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement"
        )
        raise ValueError(
            "Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement"
        )

    model = "gemini-2.5-flash"
    logger.info(f"Using Gemini model: {model}")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,  # Valeur basse pour des résultats cohérents
        top_p=0.95,  # Légèrement créatif tout en restant focalisé
        max_tokens=4096,  # Longueur maximale pour les réponses complètes
    )


def analyze_api_code(llm, api_code):
    """
    Analyse le code API pour extraire des informations structurées.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java Spring Boot à analyser

    Retourne:
        Dictionnaire contenant les informations structurées sur l'API ou None en cas d'erreur
    """
    try:
        logger.info("Starting API code analysis...")
        # Utiliser l'API du model avec LangChain
        api_analysis_prompt = RestAssuredPrompts.get_api_analysis_prompt().prompt
        chain = api_analysis_prompt | llm
        logger.info("Prompt chain created.")
        response = chain.invoke({"api_code": api_code})

        # Extraire le JSON de la réponse (peut être encapsulé dans des blocs de code)
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content)
        if json_match:
            logger.debug("JSON block found in response.")
            json_str = json_match.group(1)  # Si un bloc JSON est trouvé, on l'extrait
        else:
            logger.debug("No JSON block found, using full response content.")
            json_str = response.content  # Sinon, on prend tout le texte brute

        # Nettoyer et parser le JSON
        api_info = json.loads(json_str)
        logger.info(
            f"API analysis completed successfully: {api_info['controller_name']} with {len(api_info['endpoints'])} endpoints"
        )
        return api_info
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        logger.debug(
            f"Response received: {response.content if 'response' in locals() else 'N/A'}"
        )
        logger.exception("Full traceback:")
        return None


def generate_basic_test(llm: ChatGoogleGenerativeAI, api_code, api_info):
    """
    Génère un test RestAssured de base pour l'API.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java de l'API
        api_info: Informations structurées sur l'API

    Retourne:
        Code Java du test RestAssured généré
    """
    logger.info("Generating basic RestAssured test...")
    # Convertir api_info en chaîne formatée pour le prompt
    api_info_str = json.dumps(api_info, indent=2)

    # Génération du test
    basic_test_prompt = RestAssuredPrompts.get_basic_test_prompt().prompt
    chain = basic_test_prompt | llm
    logger.debug("Prompt chain for basic test created.")
    response = chain.invoke({"api_code": api_code, "api_info": api_info_str})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Max tokens allowed: {llm.max_output_tokens}"
    )

    # Extraire le code Java de la réponse
    java_match = re.search(r"```(?:java)?\s*([\s\S]*?)\s*```", response.content)
    if java_match:
        logger.debug("Java code block found in response.")
        test_code = java_match.group(1).strip()
        logger.info(f"Basic test generated successfully: {len(test_code)} characters")
        return test_code

    # Si pas de bloc de code, retourner tout le texte
    logger.warning("No Java code block found in response, returning raw content")
    logger.debug(f"Response: {response}")
    return response.content.strip()


def enhance_test(llm: ChatGoogleGenerativeAI, api_code, basic_test):
    """
    Améliore le test de base avec des scénarios avancés et des techniques sophistiquées.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java de l'API
        basic_test: Code du test de base généré précédemment

    Retourne:
        Code Java du test RestAssured amélioré
    """
    logger.info("Enhancing test with advanced scenarios")

    # Générer le test amélioré
    advanced_test_prompt = RestAssuredPrompts.get_advanced_test_prompt().prompt
    chain = advanced_test_prompt | llm
    logger.debug("Invoking LLM for test enhancement")
    response = chain.invoke({"api_code": api_code, "basic_test": basic_test})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Max tokens allowed: {llm.max_output_tokens}"
    )

    filled_prompt = advanced_test_prompt.format_prompt(
        api_code=api_code, basic_test=basic_test
    ).text
    logger.debug(f"Enhancement prompt length: {len(filled_prompt)} characters")
    logger.debug(f"Final enhancement prompt:\n{filled_prompt}")

    # Extraire le code Java de la réponse
    java_match = re.search(r"```(?:java)?\s*([\s\S]*?)\s*```", response.content)
    if java_match:
        logger.debug("Java code block found in enhanced test response")
        enhanced_code = java_match.group(1).strip()
        logger.info(f"Test enhanced successfully: {len(enhanced_code)} characters")
        return enhanced_code

    # Si pas de bloc de code, retourner tout le texte
    logger.warning(
        "No Java code block found in enhanced test response, returning raw content"
    )
    logger.debug(f"Response: {response}")
    logger.debug(
        f"Enhanced test preview: {response.content[:500]}{'...' if len(response.content) > 500 else ''}"
    )
    return response.content.strip()


@app.route("/rest-assured-test/gemini", methods=["POST"])
def generate_restassured_test():
    """
    Fonction principale pour générer un test RestAssured complet à partir d'un code API Spring Boot.

    Cette fonction enchaîne toutes les étapes:
    1. Analyse du code API
    2. Génération d'un test de base
    3. Amélioration du test avec des scénarios avancés

    Retourne:
        Le code Java du test RestAssured amélioré ou None si une erreur survient
    """
    logger.info("REST API endpoint /rest-assured-test/gemini called")

    data = request.get_json()
    logger.debug(f"Request received with content type: {request.content_type}")

    if "api_code" not in data:
        logger.warning("Request missing api_code parameter")
        return jsonify({"error": "Missing api_code parameter"}), 400

    api_code = data["api_code"]
    logger.debug(f"Received API code of length: {len(api_code)} characters")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return (
            jsonify({"error": "Missing GEMINI_API_KEY in environment variables"}),
            400,
        )

    try:
        # Initialiser le modèle de langage
        logger.info("Setting up LLM...")
        llm = setup_llm(api_key)
        logger.info("LLM setup complete.")

        # Étape 1: Analyser l'API
        logger.info("Step 1: Analyzing API code")
        api_info = analyze_api_code(llm, api_code)
        if not api_info:
            logger.error("API analysis failed!")
            raise Exception("API analysis failed")

        logger.info(f"API analysis successful")
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)[:500]}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        basic_test = generate_basic_test(llm, api_code, api_info)
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)

        # Étape 3: Améliorer le test
        skipping_enhancement = True
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            enhanced_test = enhance_test(llm, api_code, basic_test)

            logger.info("Enhanced test generation successful")
            logger.debug(
                "Enhanced test preview: "
                + (
                    enhanced_test[:500] + "..."
                    if len(enhanced_test) > 500
                    else enhanced_test
                )
            )

            logger.info("Test generation completed successfully")
            return jsonify({"generated_test": enhanced_test})
        else:
            return jsonify({"generated_test": basic_test})

    except Exception as e:
        logger.error(f"Error occurred while generating test: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500


@app.route("/db/testcases", methods=["POST"])
def create_test_case():
    data = request.json

    # Vérifier si la requête contient des données JSON
    if not data:
        logger.warning("Request body is empty")
        return jsonify({"error": "Request body is required"}), 400

    # Vérifier la présence des champs requis
    required_fields = ['testType', 'sourceCode', 'testCase']
    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]
    
    if missing_fields:
        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    # Validation des types de données
    if not isinstance(data.get('testType'), str):
        return jsonify({"error": "testType must be a string"}), 400
        
    if not isinstance(data.get('sourceCode'), str):
        return jsonify({"error": "sourceCode must be a string"}), 400
        
    if not isinstance(data.get('testCase'), str):
        return jsonify({"error": "testCase must be a string"}), 400
    
    try:
        result = test_case_service.create_test_case(
            test_type=data.get('testType'),
            source_code=data.get('sourceCode'),
            test_case=data.get('testCase')
        )
        
        return jsonify({
            "id": str(result.id),
            "testType": result.test_type,
            "createdAt": result.created_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({"error": f"Failed to create test case: {str(e)}"}), 500

@app.route("/db/testcases", methods=["GET"])
def get_test_cases():
    try: 
        # Récupération et validation des paramètres de requête
        test_type = request.args.get('testType')
        limit = request.args.get('limit')
        offset = request.args.get('offset')

        # Validation des paramètres numériques
        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    return jsonify({"error": "limit must be a positive integer"}), 400
            except ValueError:
                return jsonify({"error": "limit must be a valid integer"}), 400
                
        if offset:
            try:
                offset = int(offset)
                if offset < 0:
                    return jsonify({"error": "offset must be a non-negative integer"}), 400
            except ValueError:
                return jsonify({"error": "offset must be a valid integer"}), 400
        
        # Vous pouvez adapter le service pour prendre en compte ces paramètres ou un dict de filtre
        # Pour le moment, nous utilisons l'appel existant retournant tout les cas de test
        test_cases = test_case_service.get_test_cases()
            
        # Filtrer par type de test si spécifié
        if test_type:
            test_cases = [tc for tc in test_cases if tc.test_type == test_type]
         
        # Appliquer pagination si spécifiée
        if offset and limit:
            test_cases = test_cases[offset:offset+limit]
        elif limit:
            test_cases = test_cases[:limit]
    
        # Formatage de la réponse
        return jsonify([{
            "id": str(tc.id),
            "testType": tc.test_type,
            "sourceCode": tc.source_code,
            "testCase": tc.test_case,
            "createdAt": tc.created_at.isoformat()
        } for tc in test_cases])

        except Exception as e:
            logger.error(f"Error retrieving test cases: {str(e)}")
            logger.exception("Full traceback:")
            return jsonify({"error": f"Failed to retrieve test cases: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
