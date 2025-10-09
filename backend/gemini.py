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
from backend.pipelines import (
    rest_pipeline,
    unit_pipeline,
)


# Initialize logger
logger = setup_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
logger.info("Flask app initialized.")

def validate_request_data(data)->bool:
    """
    Validate the incoming request data.
    Requirements:
    - Must contain 'api_code' key with non-empty string value.
    """
    try:
        if "api_code" not in data:
            logger.warning("Request missing api_code parameter")
            return False

        api_code = data["api_code"]
        logger.debug(f"Received API code of length: {len(api_code)} characters")

        return isinstance(api_code, str) and len(api_code.strip()) > 0
    except Exception as e:
        logger.error(f"Error validating request data: {str(e)}")
        return False
    
def get_gemini_key()->str:
    """
    Retrieve the Gemini API key from environment variables.

    Returns:
        The Gemini API key as a string.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return None
    return api_key


def setup_llm(api_key:str=None)-> ChatGoogleGenerativeAI:
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
    api_key = api_key or get_gemini_key()

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


@app.route("/unit-test/gemini", methods=["POST"])
def generate_unit_test():
    """
    Fonction principale pour générer un test unitaire Python complet à partir d'un code source Python.

    Cette fonction enchaîne toutes les étapes:
    1. Analyse du code source
    2. Génération d'un test de base
    3. Amélioration du test avec des scénarios avancés

    Retourne:
        Le code Python du test unitaire amélioré ou None si une erreur survient
    """

    logger.info("Unit test endpoint /unit-test/gemini called")
    
    data = request.get_json()
    logger.debug(f"Request received with content type: {request.content_type}")

    if "api_code" not in data:
        logger.warning("Request missing api_code parameter")
        return jsonify({"error": "Missing api_code parameter"}), 400

    api_code = data["api_code"]
    logger.debug(f"Received API code of length: {len(api_code)} characters")

    api_key = get_gemini_key()
    if api_key is None:
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
        api_info = unit_pipeline.analyze_code(llm, api_code)
        if not api_info:
            logger.error("API analysis failed!")
            raise Exception("API analysis failed")

        logger.info(f"API analysis successful")
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)[:500]}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        basic_test = unit_pipeline.generate_basic_test(llm, api_code, api_info)
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)

        # Étape 3: Améliorer le test
        skipping_enhancement = False
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            enhanced_test = unit_pipeline.enhance_test(llm, api_code, basic_test)

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
        logger.error(f"Error occurred while generating unit test pipeline: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500


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
        api_info = rest_pipeline.analyze_api_code(llm, api_code)
        if not api_info:
            logger.error("API analysis failed!")
            raise Exception("API analysis failed")

        logger.info(f"API analysis successful")
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)[:500]}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        basic_test = rest_pipeline.generate_basic_test(llm, api_code, api_info)
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)

        # Étape 3: Améliorer le test
        skipping_enhancement = True
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            enhanced_test = rest_pipeline.enhance_test(llm, api_code, basic_test)

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


if __name__ == "__main__":
    app.run(debug=True)
