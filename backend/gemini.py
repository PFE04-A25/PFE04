import os
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
from flask import jsonify, Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

from logger import setup_logger
from config_class import EndpointInfo, ApiAnalysis
from prompts.rest_prompt import (
    RestAssuredPrompts,
)
from code_manipulation import java as java_utils

from execute import JavaTestExecutor


# Initialize logger
logger = setup_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
CORS(
    app, origins=["http://localhost:3000", "http://localhost:3001"]
)  # Enable CORS for Next.js frontend
logger.info("Flask app initialized with CORS.")


def setup_llm(api_key=None) -> ChatGoogleGenerativeAI:
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
        max_tokens=8192,  # Longueur maximale pour les réponses complètes
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
    else:
        logger.warning("No Java code block found in response, returning raw content")
        test_code = response.content.strip()

    # Nettoyer le code des marqueurs markdown résiduels
    test_code = java_utils.clean_java_code(test_code)

    # Corriger les annotations Spring Boot pour spécifier la classe d'application
    test_code = java_utils.fix_spring_boot_test_annotation(test_code)

    logger.info(f"Basic test generated successfully: {len(test_code)} characters")
    return test_code


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
    else:
        logger.warning(
            "No Java code block found in enhanced test response, returning raw content"
        )
        enhanced_code = response.content.strip()

    # Nettoyer le code des marqueurs markdown résiduels
    enhanced_code = java_utils.clean_java_code(enhanced_code)

    # Corriger les annotations Spring Boot pour spécifier la classe d'application
    enhanced_code = java_utils.fix_spring_boot_test_annotation(enhanced_code)

    logger.info(f"Test enhanced successfully: {len(enhanced_code)} characters")
    return enhanced_code


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de vérification de santé pour les tests automatisés"""
    return jsonify({
        "status": "healthy",
        "service": "gemini-api",
        "message": "Service Gemini is running",
        "endpoints": [
            "/rest-assured-test/gemini",
            "/execute-tests",
            "/execution-status/<execution_id>",
            "/execution-metrics/<execution_id>"
        ]
    }), 200


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


executor = None # temporary global executor instance en attendant l'implémentation complète de la DB

@app.route("/execute-tests", methods=["POST"])
def execute_tests():
    """Endpoint pour exécuter les tests Java et retourner un ID d'exécution"""
    try:
        data = request.get_json()
        test_code = data.get("test_code", "")
        api_code = data.get("api_code", "")
        language = "java" #TODO - ajouter une méthode dynamique de choisir le language

        if not test_code.strip():
            return jsonify({"error": "Test code is required"}), 400

        if language.lower() == "java":
            # Générer un executeur de test java
            executor = JavaTestExecutor(
                logger=logger, test_code=test_code, api_code=api_code
            )
        elif language.lower() == "python":
            return jsonify({"error": "Python execution not implemented yet"}), 501
        execution_id = executor.id

        # Lancer l'exécution en arrière-plan
        thread = executor.get_thread()
        thread.start()

        logger.info(f"Started test execution with ID: {execution_id}")
        return jsonify(
            {
                "execution_id": execution_id,
                "status": "started",
                "message": "Test execution started",
            }
        )

    except Exception as e:
        logger.error(f"Error starting test execution: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/execution-status/<execution_id>", methods=["GET"])
def get_execution_status(execution_id):
    """Endpoint pour récupérer le statut et les résultats d'une exécution"""
    try:
        # Check temporaire en attendant l'implémentation complète de la DB
        if executor is None:
            return jsonify({"error": "No test execution in progress"}), 404
        if isinstance(executor, JavaTestExecutor):
            if execution_id not in executor.test_executions.keys():
                return jsonify({"error": "Execution ID not found"}), 404
            else:
                test_executions = executor.test_executions
        else:
            return jsonify({"error": "Unsupported executor type"}), 500

        execution_data = test_executions[execution_id]

        return jsonify(
            {
                "execution_id": execution_id,
                "status": execution_data["status"],
                "logs": execution_data["logs"],
                "metrics": execution_data["metrics"],
                "start_time": execution_data.get("start_time"),
                "end_time": execution_data.get("end_time"),
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving execution status: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/execution-metrics/<execution_id>", methods=["GET"])
def get_detailed_metrics(execution_id):
    """Endpoint pour récupérer les métriques détaillées avec analyse de couverture"""
    try:
        # Check temporaire en attendant l'implémentation complète de la DB
        if executor is None:
            return jsonify({"error": "No test execution in progress"}), 404
        if isinstance(executor, JavaTestExecutor):
            if execution_id not in executor.test_executions.keys():
                return jsonify({"error": "Execution ID not found"}), 404
            else:
                test_executions = executor.test_executions
        else:
            return jsonify({"error": "Unsupported executor type"}), 500

        execution_data = test_executions[execution_id]
        metrics = execution_data.get("metrics", {})

        # Analyser les métriques de qualité
        quality_analysis = {
            "coverage_quality": "poor",  # poor, fair, good, excellent
            "test_completeness": "insufficient",  # insufficient, minimal, adequate, comprehensive
            "overall_score": 0.0,  # 0-100
        }

        # Évaluer la qualité de la couverture
        line_coverage = metrics.get("line_coverage", 0)
        branch_coverage = metrics.get("branch_coverage", 0)

        if line_coverage >= 90 and branch_coverage >= 85:
            quality_analysis["coverage_quality"] = "excellent"
        elif line_coverage >= 80 and branch_coverage >= 70:
            quality_analysis["coverage_quality"] = "good"
        elif line_coverage >= 60 and branch_coverage >= 50:
            quality_analysis["coverage_quality"] = "fair"
        else:
            quality_analysis["coverage_quality"] = "poor"

        # Évaluer la complétude des tests
        tests_per_endpoint = metrics.get("tests_per_endpoint", 0)
        endpoints_count = metrics.get("endpoints_count", 0)

        if tests_per_endpoint >= 3:
            quality_analysis["test_completeness"] = "comprehensive"
        elif tests_per_endpoint >= 2:
            quality_analysis["test_completeness"] = "adequate"
        elif tests_per_endpoint >= 1:
            quality_analysis["test_completeness"] = "minimal"
        else:
            quality_analysis["test_completeness"] = "insufficient"

        # Score global (pondéré)
        coverage_score = (
            line_coverage * 0.4
            + branch_coverage * 0.4
            + metrics.get("instruction_coverage", 0) * 0.2
        )
        test_score = min(
            100, tests_per_endpoint * 25
        )  # 25 points par test par endpoint, max 100

        quality_analysis["overall_score"] = coverage_score * 0.7 + test_score * 0.3

        # Recommandations
        recommendations = []

        if line_coverage < 70:
            recommendations.append("Augmenter la couverture de lignes (cible: 80%+)")
        if branch_coverage < 60:
            recommendations.append(
                "Améliorer la couverture des branches - tester tous les cas if/else/switch"
            )
        if tests_per_endpoint < 2:
            recommendations.append(
                "Ajouter plus de tests par endpoint (recommandé: 2-3 tests minimum)"
            )
        if endpoints_count > 0 and metrics.get("tests_run", 0) == 0:
            recommendations.append(
                "Aucun test détecté - implémenter des tests pour tous les endpoints"
            )

        if not recommendations:
            recommendations.append(
                "Excellente couverture de tests ! Continuer les bonnes pratiques."
            )

        return jsonify(
            {
                "execution_id": execution_id,
                "metrics": metrics,
                "quality_analysis": quality_analysis,
                "recommendations": recommendations,
                "coverage_summary": {
                    "line_coverage": f"{line_coverage:.1f}%",
                    "branch_coverage": f"{branch_coverage:.1f}%",
                    "instruction_coverage": f"{metrics.get('instruction_coverage', 0):.1f}%",
                    "tests_per_endpoint": f"{tests_per_endpoint:.1f}",
                    "total_endpoints": endpoints_count,
                    "total_tests": metrics.get("tests_run", 0),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving detailed metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
