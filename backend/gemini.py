import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import threading
import time
import uuid
from db.services import Services
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import json
from flask import jsonify, Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from pipelines import(
    unit_pipeline,
    rest_pipeline,
)
from logger import setup_logger
from execute import JavaTestExecutor


class EnhancedTestGenerationError(Exception):
    """Custom exception for errors during enhanced test generation."""
    pass

# Initialize logger
logger = setup_logger("gemini_app")

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
CORS(
    app, origins=["http://localhost:3000", "http://localhost:3001"]
)  # Enable CORS for Next.js frontend
logger.info("Flask app initialized with CORS.")
logger.info("Flask app initialized.")

logger.info("Initializing database services...")
db_services = Services()
logger.info("Database services initialized.")

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
    if "api_code" not in data:
        return jsonify({"error": "Missing api_code parameter"}), 400

    api_code = data["api_code"]
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"error": "Missing GEMINI_API_KEY in environment variables"}), 400

    try:
        llm = setup_llm(api_key)
        logger.info("LLM setup complete.")

        model_service = db_services.model_service
        pipeline_service = db_services.pipeline_service
        prompt_service = db_services.prompt_template_service
        snippet_service = db_services.code_snippet_service
        generation_service = db_services.test_generation_service

        model = model_service.get_models_by_name("Gemini")
        if not model:
            raise ValueError("Model 'Gemini' not found in DB")
        model = model[0]

        pipeline_list = pipeline_service.get_pipeline_active_by_name("REST")
        if not pipeline_list:
            raise ValueError("No active pipeline found for 'REST'")
        pipeline = pipeline_list[0]

        prompts_dict = {}
        for prompt_conf in pipeline.prompts:
            prompt_obj = prompt_service.get_prompt_template(str(prompt_conf["prompt_id"]))
            if prompt_obj:
                prompts_dict.update(
                    {prompt_conf["order"]: PromptTemplate(
                        template=prompt_obj.template_text,
                        input_variables=prompt_obj.input_variables,
                        partial_variables=prompt_obj.partial_variables,
                    )}
                )

        # prompts_dict = {p_idx + 1: prompts[p_idx].template_text for p_idx in range(len(prompts))}
        logger.info(f"Loaded {len(prompts_dict)} prompts for REST pipeline.")

        logger.info("Step 1: Analyzing API code")
        if 1 not in prompts_dict.keys():
            raise Exception("Missing prompt for API analysis step")
        api_info = rest_pipeline.analyze_api_code(llm, api_code, prompts_dict[1])
        if not api_info:
            raise Exception("API analysis failed")

        logger.info("Step 2: Generating basic test")
        if 2 not in prompts_dict.keys():
            raise Exception("Missing prompt for basic test generation step")
        basic_test = rest_pipeline.generate_basic_test(llm, api_code, api_info, prompts_dict[2])
        logger.info("Basic test generation successful")

        enhanced_test = None
        skipping_enhancement = True
        if not skipping_enhancement and 3 in prompts_dict.keys():
            logger.info("Step 3: Enhancing test")
            enhanced_test = rest_pipeline.enhance_test(llm, api_code, basic_test, prompts_dict[3])
        elif not skipping_enhancement and 3 not in prompts_dict.keys():
            raise Exception("Missing prompt for enhanced test generation step")
        else:
            enhanced_test = basic_test

        snippet = snippet_service.create_code_snippet(
            source_code=api_code,
            language="java",
            description="Spring Boot API analyzed for RestAssured test generation"
        )

        generation = generation_service.create_test_generation(
            model_id=str(model.id),
            pipeline_id=str(pipeline.id),
            code_snippet_id=str(snippet.id),
            generated_analysis=str(api_info),
            generated_test=enhanced_test,
            token_usage={"prompt_tokens": 0, "completion_tokens": 0},  # placeholder
            executed=False
        )

        logger.info(f"Test generation saved in DB (ID: {generation.id})")

        return jsonify({
            "generated_test": enhanced_test,
            "generation_id": str(generation.id)
        })

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
            if enhanced_test is None or enhanced_test.strip() == "":
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


@app.route("/db/testcases", methods=["GET"])
def get_test_cases():
    """
    Retourne la liste des tests générés depuis la nouvelle structure MongoDB.
    Combine test_generations + code_snippets + pipeline.
    """
    try:
        test_type = request.args.get("testType")
        limit = request.args.get("limit")
        offset = request.args.get("offset")

        try:
            limit = int(limit) if limit else None
            offset = int(offset) if offset else 0
        except ValueError:
            return jsonify({"error": "limit and offset must be integers"}), 400

        generation_service = db_services.test_generation_service
        pipeline_service = db_services.pipeline_service
        snippet_service = db_services.code_snippet_service

        generations = generation_service.repository.find_all()

        if test_type:
            pipelines = pipeline_service.get_pipelines_by_name(test_type.upper())
            pipeline_ids = {str(p.id) for p in pipelines}
            generations = [g for g in generations if str(g.pipeline_id) in pipeline_ids]

        if limit:
            generations = generations[offset:offset + limit]

        snippets_by_id = {str(s.id): s for s in snippet_service.repository.find_all()}

        response = []
        for gen in generations:
            snippet = snippets_by_id.get(str(gen.code_snippet_id))
            response.append({
                "id": str(gen.id),
                "testType": test_type or "UNKNOWN",
                "sourceCode": snippet.source_code if snippet else None,
                "generatedTest": gen.generated_test,
                "executed": gen.executed,
                "createdAt": gen.created_at.isoformat() if hasattr(gen, "created_at") else None,
            })

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error retrieving test generations: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500
    
@app.route("/db/testcases/<id>", methods=["DELETE"])
def delete_test_case(id):
    """
    Supprime un test généré (test_generation) et son code source associé (code_snippet)
    selon la nouvelle architecture MongoDB.
    """
    try:
        generation_service = db_services.test_generation_service
        snippet_service = db_services.code_snippet_service

        generation = generation_service.get_generation(id)
        if not generation:
            logger.warning(f"TestGeneration with ID {id} not found.")
            return jsonify({"error": "Test generation not found"}), 404

        snippet_id = getattr(generation, "code_snippet_id", None)

        deleted_gen = generation_service.repository.delete(id)
        if not deleted_gen:
            logger.warning(f"Failed to delete TestGeneration with ID {id}.")
            return jsonify({"error": "Failed to delete test generation"}), 500

        if snippet_id:
            snippet_service.repository.delete(snippet_id)
            logger.info(f"Deleted CodeSnippet with ID {snippet_id}")

        logger.info(f"Successfully deleted TestGeneration {id} and associated CodeSnippet.")
        return jsonify({"message": f"Test generation {id} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting test generation: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to delete test generation: {str(e)}"}), 500
    
@app.route("/db/testcases/<id>", methods=["PUT"])
def update_test_case(id):
    """
    Met à jour un test généré (test_generation) ou son code source (code_snippet)
    selon la nouvelle structure MongoDB.
    """
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        generation_service = db_services.test_generation_service
        snippet_service = db_services.code_snippet_service

        generation = generation_service.get_generation(id)
        if not generation:
            return jsonify({"error": f"Test generation with ID {id} not found"}), 404

        generation_updates = {}
        snippet_updates = {}

        if "testCase" in data:
            if not isinstance(data["testCase"], str):
                return jsonify({"error": "testCase must be a string"}), 400
            generation_updates["generated_test"] = data["testCase"]

        if "sourceCode" in data:
            if not isinstance(data["sourceCode"], str):
                return jsonify({"error": "sourceCode must be a string"}), 400
            snippet_updates["source_code"] = data["sourceCode"]

        if not generation_updates and not snippet_updates:
            return jsonify({"error": "No valid fields to update"}), 400

        updated_gen = None
        updated_snippet = None

        if generation_updates:
            updated_gen = generation_service.repository.update(id, generation_updates)

        if snippet_updates and hasattr(generation, "code_snippet_id"):
            updated_snippet = snippet_service.repository.update(
                generation.code_snippet_id, snippet_updates
            )

        response = {
            "id": str(id),
            "testType": getattr(generation, "test_type", "N/A"),
            "sourceCode": getattr(updated_snippet or {}, "source_code", None),
            "generatedTest": getattr(updated_gen or generation, "generated_test", None),
            "executed": getattr(generation, "executed", False),
            "updatedAt": getattr(updated_gen or generation, "updated_at", None),
        }

        logger.info(f"Updated test generation {id}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error updating test generation: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to update test generation: {str(e)}"}), 500
    
@app.route("/execute-tests", methods=["POST"])
def execute_tests():
    """Lance l'exécution des tests et enregistre les résultats dans MongoDB"""
    try:
        data = request.get_json()
        test_code = data.get("test_code", "")
        api_code = data.get("api_code", "")
        # TODO: FE should send test generation ID to link execution
        test_generation_id = data.get("test_generation_id")
        if not test_code.strip():
            return jsonify({"error": "Test code is required"}), 400

        exec_service = db_services.test_execution_service
        # execution_id = str(uuid.uuid4())

        execution = exec_service.create_test_execution(
            test_generation_id=test_generation_id,
            build_success=False,
            tests_run=0,
            error_count=0,
            failure_count=0,
            skipped_count=0,
            success_rate=0.0,
            execution_time=0.0,
            line_coverage=0.0,
            timestamp=time.time(),
            logs="Execution started...",
        )

        executor = JavaTestExecutor(logger=logger, test_code=test_code, api_code=api_code)

        def run_and_save_to_db(exec_id: str, executor: JavaTestExecutor):
            try:
                result = executor.run_java_tests_async(exec_id)
                metrics = result.get("metrics", {})
                logs = result.get("logs", "")

                exec_service.repository.update(
                    str(execution.id),
                    {
                        "build_success": metrics.get("return_code", 1) == 0,
                        "tests_run": metrics.get("tests_run", 0),
                        "error_count": metrics.get("errors", 0),
                        "failure_count": metrics.get("failures", 0),
                        "skipped_count": metrics.get("skipped", 0),
                        "success_rate": metrics.get("success_rate", 0.0),
                        "execution_time": metrics.get("execution_time", 0.0),
                        "line_coverage": metrics.get("line_coverage", 0.0),
                        "logs": logs,
                        "timestamp": time.time(),
                    },
                )
                logger.info(f"Test execution {exec_id} completed and saved to MongoDB")

            except Exception as e:
                logger.error(f"Error during execution {exec_id}: {str(e)}", exc_info=True)
                exec_service.repository.update(
                    str(execution.id),
                    {"logs": f"Execution failed: {str(e)}", "build_success": False},
                )

        thread = threading.Thread(target=run_and_save_to_db, args=(str(execution.id), executor))
        thread.daemon = True
        thread.start()

        return jsonify({
            "execution_id": str(execution.id),
            "status": "started",
            "message": "Test execution started"
        }), 200

    except Exception as e:
        logger.error(f"Error starting test execution: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500



@app.route("/execution-status/<execution_id>", methods=["GET"])
def get_execution_status(execution_id):
    """Retourne le statut et les métriques d'une exécution depuis MongoDB"""
    try:
        exec_service = db_services.test_execution_service
        execution = exec_service.get_test_execution(execution_id)

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        if not execution.build_success and execution.logs == "Execution started...":
            status = "running"
        elif execution.build_success:
            status = "completed"
        elif "failed" in (execution.logs or "").lower():
            status = "failed"
        else:
            status = "unknown"

        response = {
            "execution_id": execution_id,
            "status": status,
            "logs": execution.logs or "",
            "metrics": {
                "tests_run": execution.tests_run or 0,
                "failures": execution.failure_count or 0,
                "errors": execution.error_count or 0,
                "skipped": execution.skipped_count or 0,
                "success_rate": execution.success_rate or 0.0,
                "build_success": execution.build_success or False,
                "line_coverage": execution.line_coverage or 0.0,
                "execution_time": execution.execution_time or 0.0,
            },
            "start_time": execution.timestamp or time.time(),
            "end_time": None if status == "running" else time.time(),
        }

        logger.info(f"Status fetched for execution {execution_id}: {status}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error retrieving execution status: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/execution-metrics/<execution_id>", methods=["GET"])
def get_detailed_metrics(execution_id):
    """Récupère les métriques détaillées avec analyse de couverture depuis MongoDB"""
    try:
        exec_service = db_services.test_execution_service
        execution = exec_service.get_test_execution(execution_id)

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        metrics = {
            "tests_run": execution.tests_run or 0,
            "failures": execution.failure_count or 0,
            "errors": execution.error_count or 0,
            "skipped": execution.skipped_count or 0,
            "success_rate": execution.success_rate or 0.0,
            "build_success": execution.build_success or False,
            "line_coverage": execution.line_coverage or 0.0,
            "branch_coverage": getattr(execution, "branch_coverage", 0.0),
            "instruction_coverage": getattr(execution, "instruction_coverage", 0.0),
            "lines_covered": getattr(execution, "lines_covered", 0),
            "lines_total": getattr(execution, "lines_total", 0),
            "branches_covered": getattr(execution, "branches_covered", 0),
            "branches_total": getattr(execution, "branches_total", 0),
            "instructions_covered": getattr(execution, "instructions_covered", 0),
            "instructions_total": getattr(execution, "instructions_total", 0),
            "endpoints_count": getattr(execution, "endpoints_count", 0),
            "tests_per_endpoint": getattr(execution, "tests_per_endpoint", 0.0),
            "execution_time": execution.execution_time or 0.0,
            "return_code": getattr(execution, "return_code", 0),
        }

        quality_analysis = {
            "coverage_quality": "poor",
            "test_completeness": "insufficient",
            "overall_score": 0.0,
        }

        line_coverage = metrics.get("line_coverage", 0)
        branch_coverage = metrics.get("branch_coverage", 0)
        instruction_coverage = metrics.get("instruction_coverage", 0)
        tests_per_endpoint = metrics.get("tests_per_endpoint", 0)
        endpoints_count = metrics.get("endpoints_count", 0)

        if line_coverage >= 90 and branch_coverage >= 85:
            quality_analysis["coverage_quality"] = "excellent"
        elif line_coverage >= 80 and branch_coverage >= 70:
            quality_analysis["coverage_quality"] = "good"
        elif line_coverage >= 60 and branch_coverage >= 50:
            quality_analysis["coverage_quality"] = "fair"
        else:
            quality_analysis["coverage_quality"] = "poor"

        if tests_per_endpoint >= 3:
            quality_analysis["test_completeness"] = "comprehensive"
        elif tests_per_endpoint >= 2:
            quality_analysis["test_completeness"] = "adequate"
        elif tests_per_endpoint >= 1:
            quality_analysis["test_completeness"] = "minimal"
        else:
            quality_analysis["test_completeness"] = "insufficient"

        coverage_score = (
            line_coverage * 0.4
            + branch_coverage * 0.4
            + instruction_coverage * 0.2
        )
        test_score = min(100, tests_per_endpoint * 25)
        quality_analysis["overall_score"] = coverage_score * 0.7 + test_score * 0.3

        recommendations = []
        if line_coverage < 70:
            recommendations.append("Augmenter la couverture de lignes (cible: 80%+)")
        if branch_coverage < 60:
            recommendations.append("Améliorer la couverture des branches - tester tous les cas if/else/switch")
        if tests_per_endpoint < 2:
            recommendations.append("Ajouter plus de tests par endpoint (recommandé: 2-3 tests minimum)")
        if endpoints_count > 0 and metrics.get("tests_run", 0) == 0:
            recommendations.append("Aucun test détecté - implémenter des tests pour tous les endpoints")
        if not recommendations:
            recommendations.append("Excellente couverture de tests ! Continuer les bonnes pratiques.")

        return jsonify({
            "execution_id": execution_id,
            "metrics": metrics,
            "quality_analysis": quality_analysis,
            "recommendations": recommendations,
            "coverage_summary": {
                "line_coverage": f"{line_coverage:.1f}%",
                "branch_coverage": f"{branch_coverage:.1f}%",
                "instruction_coverage": f"{instruction_coverage:.1f}%",
                "tests_per_endpoint": f"{tests_per_endpoint:.1f}",
                "total_endpoints": endpoints_count,
                "total_tests": metrics["tests_run"],
            },
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving detailed metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not os.environ.get("WERKZEUG_RUN_MAIN"):
        logger.info("Starting Gemini Flask server on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)