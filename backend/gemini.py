import os
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
from flask import jsonify, Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

from logger import get_logger
from config_class import EndpointInfo, ApiAnalysis
from pipelines import(
    rest_pipeline,
    unit_pipeline,
)
from db.services.test_case import TestCaseService
from code_manipulation import java as java_utils

from execute import JavaTestExecutor


class EnhancedTestGenerationError(Exception):
    """Custom exception for errors during enhanced test generation."""
    pass

# Initialize logger
logger = get_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
CORS(
    app, origins=["http://localhost:3000", "http://localhost:3001"]
)  # Enable CORS for Next.js frontend
logger.info("Flask app initialized with CORS.")
logger.info("Flask app initialized.")

# Deprecated, was used to test DB implementation
test_case_service = TestCaseService()
logger.info("TestCaseService initialized.")

# Should instead use the Services class to init all services needed
from db.services import Services
db_services = Services()

def get_gemini_key() -> str:
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
        max_tokens=8192,  # Longueur maximale pour les réponses complètes
    )


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

        # **Note**  
        # Le scope de notre projet est exclusivement pour Gemini. Cependant, nous avons fait une architecture de DB permettant d'avoir plusieurs modèles.
        # On devrait donc fetch le modèle depuis la DB pour obtenir ses informations (comme son ID, les configs, etc.)
        # Cependant pour simplicité puisqu'on utilise directement Gemini nous utilisons un ID statique pour l'instant.

        # TODO (DB) - Fetch the active rest pipeline in the DB and fetch its prompt_templates
        # TODO (DB) - Init un des PromptTemplate pour les prompts utilisés lors de la génération
        # Exemple:
        #       prompt_X = basic_prompt.BasicPipeline(...)
        #       prompts_dict = {1: prompt_1.prompt, 2: prompt_2.prompt, 3: prompt_3.prompt}
        # TODO (Refactoring) - Initialise le pipeline avec ces prompts
        # Exemple:
        #      rest_pipeline = pipelines.rest_pipeline.RestAssuredPipeline(llm, prompts_dict)
        # TODO (Refactoring) - Run the pipeline (generate_test) pour générer le test complet

        # TODO (Refactoring) - Supprimer la logique de la génération du test dans ce endpoint une fois le pipeline fonctionnel
        # Étape 1: Analyser l'API
        logger.info("Step 1: Analyzing API code")
        # TODO (DB) Utiliser le prompt de la DB selon le ID du step 1
        current_prompt = rest_pipeline.RestAssuredPrompts.get_api_analysis_prompt().prompt
        api_info = rest_pipeline.analyze_api_code(llm, api_code, current_prompt)
        if not api_info:
            logger.error("API analysis failed!")
            raise Exception("API analysis failed")

        logger.info(f"API analysis successful")
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)[:500]}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        # TODO (DB) Utiliser le prompt de la DB selon le ID du step 2
        current_prompt = rest_pipeline.RestAssuredPrompts.get_basic_test_prompt().prompt
        basic_test = rest_pipeline.generate_basic_test(llm, api_code, api_info, current_prompt)
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)

        # Étape 3: Améliorer le test
        skipping_enhancement = True
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            # TODO (DB) Utiliser le prompt de la DB selon le ID du step 3
            current_prompt = rest_pipeline.RestAssuredPrompts.get_advanced_test_prompt().prompt
            enhanced_test = rest_pipeline.enhance_test(llm, api_code, basic_test, current_prompt)

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
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        basic_test = unit_pipeline.generate_basic_test(llm, api_code, api_info)
        if basic_test is None:
            logger.error("Basic test generation failed!")
            raise Exception("Basic test generation failed")
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)

        # Étape 3: Améliorer le test
        skipping_enhancement = False
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            enhanced_test = unit_pipeline.enhance_test(
                llm, api_code, api_info, basic_test
            )
            if enhanced_test is None:
                logger.error("Enhanced test generation failed!")
                raise EnhancedTestGenerationError("Enhanced test generation failed")
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
    except EnhancedTestGenerationError as etge:
        logger.error(f"Enhanced test generation error: {str(etge)}")
        return jsonify({"generated_test": basic_test})
    except Exception as e:
        logger.error(f"Error occurred while generating unit test pipeline: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500

# TODO (DB) - Rework les endpoints CRUD de la DB pour la nouvelles architecture des services
# Noter que le FE va surement aussi devoir être mis à jour pour envoyer les bonnes données
@app.route("/db/testcases", methods=["POST"])
def create_test_case():
    data = request.json

    # Vérifier si la requête contient des données JSON
    if not data:
        logger.warning("Request body is empty")
        return jsonify({"error": "Request body is required"}), 400

    # Vérifier la présence des champs requis
    required_fields = ["testType", "sourceCode", "testCase"]
    missing_fields = [
        field
        for field in required_fields
        if field not in data or data.get(field) is None
    ]

    if missing_fields:
        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        return (
            jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}),
            400,
        )

    # Validation des types de données
    if not isinstance(data.get("testType"), str):
        return jsonify({"error": "testType must be a string"}), 400

    if not isinstance(data.get("sourceCode"), str):
        return jsonify({"error": "sourceCode must be a string"}), 400

    if not isinstance(data.get("testCase"), str):
        return jsonify({"error": "testCase must be a string"}), 400

    try:
        # Deprecated, ne pas utiliser test_case comme objet
        # TODO (DB) - Utiliser le Services class pour orchestrer les appels aux différents services nécessaires
        # EX: 
        #   1. Créer un code_snippet, 
        #   2.fetch le id du modèle & pipeline utilisé 
        #   3. Créer test_génération avec les FK
        result = test_case_service.create_test_case(
            test_type=data.get("testType"),
            source_code=data.get("sourceCode"),
            test_case=data.get("testCase"),
        )

        return jsonify(
            {
                "id": str(result.id),
                "testType": result.test_type,
                "createdAt": result.created_at.isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({"error": f"Failed to create test case: {str(e)}"}), 500


# TODO (DB) - Rework les endpoints CRUD de la DB pour la nouvelles architecture des services et models
@app.route("/db/testcases", methods=["GET"])
def get_test_cases():
    try:
        # Récupération et validation des paramètres de requête
        test_type = request.args.get("testType")
        limit = request.args.get("limit")
        offset = request.args.get("offset")

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
                    return (
                        jsonify({"error": "offset must be a non-negative integer"}),
                        400,
                    )
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
            test_cases = test_cases[offset : offset + limit]
        elif limit:
            test_cases = test_cases[:limit]

        # Formatage de la réponse
        return jsonify(
            [
                {
                    "id": str(tc.id),
                    "testType": tc.test_type,
                    "sourceCode": tc.source_code,
                    "testCase": tc.test_case,
                    "createdAt": tc.created_at.isoformat(),
                }
                for tc in test_cases
            ]
        )
    except Exception as e:
        logger.error(f"Error retrieving test cases: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": f"Failed to retrieve test cases: {str(e)}"}), 500

# TODO (DB) - Rework les endpoints CRUD de la DB pour la nouvelles architecture des services et models
@app.route("/db/testcases/<id>", methods=["DELETE"])
def delete_test_case(id):
    try:
        success = test_case_service.delete_test_case(id)
        if success:
            return jsonify({"message": "Test case deleted"}), 200
        else:
            return jsonify({"error": "Test case not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting test case: {str(e)}")
        return jsonify({"error": f"Failed to delete test case: {str(e)}"}), 500
    
# TODO (DB) - Rework les endpoints CRUD de la DB pour la nouvelles architecture des services et models
@app.route("/db/testcases/<id>", methods=["PUT"])
def update_test_case(id):
    data = request.json

    # Verify request contains JSON data
    if not data:
        logger.warning("Request body is empty")
        return jsonify({"error": "Request body is required"}), 400

    # Check for fields to update and convert from camelCase to snake_case
    update_data = {}
    
    if "testType" in data:
        if not isinstance(data["testType"], str):
            return jsonify({"error": "testType must be a string"}), 400
        update_data["test_type"] = data["testType"]
        
    if "sourceCode" in data:
        if not isinstance(data["sourceCode"], str):
            return jsonify({"error": "sourceCode must be a string"}), 400
        update_data["source_code"] = data["sourceCode"]
        
    if "testCase" in data:
        if not isinstance(data["testCase"], str):
            return jsonify({"error": "testCase must be a string"}), 400
        update_data["test_case"] = data["testCase"]
    
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        # Call service method
        result = test_case_service.update_test_case(id, update_data)
        
        if not result:
            return jsonify({"error": "Test case not found"}), 404
            
        return jsonify({
            "id": str(result.id),
            "testType": result.test_type,
            "sourceCode": result.source_code,
            "testCase": result.test_case,
            "createdAt": result.created_at.isoformat(),
            "updatedAt": result.updated_at.isoformat() if hasattr(result, "updated_at") else None
        })
    except Exception as e:
        logger.error(f"Error updating test case: {str(e)}")
        return jsonify({"error": f"Failed to update test case: {str(e)}"}), 500

executor = None # temporary global executor instance en attendant l'implémentation complète de la DB

# TODO (DB) - Ajouter l'enregistrement des exécutions de tests dans la DB.
# Noter qu'il va surement falloir envoyer plus de data du FE pour récupérer la pipeline, modèle, etc.
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
