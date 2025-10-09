import json
import re
from logger import get_logger
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.unit_prompt import (
    UnitPrompts,
)
from pipelines import cleanup_raw_code_output

logger = get_logger()


def analyze_code(llm, api_code) -> dict:
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
        api_analysis_prompt = UnitPrompts.get_code_analysis_prompt().prompt
        chain = api_analysis_prompt | llm
        logger.info("Prompt chain created.")
        response = chain.invoke({"source_code": api_code})
        # Extraire le JSON de la réponse (peut être encapsulé dans des blocs de code)
        logger.info("API analysis completed, extracting JSON...")
        contains_code_marker, json_str = cleanup_raw_code_output(
            response.content, language="json"
        )

        if contains_code_marker:
            logger.warning("Response contained code block markers that were removed.")
        if json_str.strip() == "":
            logger.error("Extracted JSON string is empty.")
            return None

        # Nettoyer et parser le JSON
        api_info = json.loads(json_str)
        logger.info(f"API analysis completed successfully")
        return api_info
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        logger.debug(
            f"Response received: {response.content if 'response' in locals() else 'N/A'}"
        )
        logger.exception("Full traceback:")
        return None


def generate_basic_test(
    llm: ChatGoogleGenerativeAI, api_code, api_info, language="python"
) -> str:
    """
    Génère un test RestAssured de base pour l'API.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java de l'API
        api_info: Informations structurées sur l'API

    Retourne:
        Raw code du unit test généré
    """
    try:
        logger.info("Generating basic RestAssured test...")
        # Convertir api_info en chaîne formatée pour le prompt
        api_info_str = json.dumps(api_info, indent=2)
        # Génération du test
        basic_test_prompt = UnitPrompts.get_basic_test_prompt().prompt
        chain = basic_test_prompt | llm
        logger.debug("Prompt chain for basic test created.")
        response = chain.invoke(
            {"raw_source_code": api_code, "analysis_json": api_info_str}
        )
        logger.info(
            f"Input tokens: {response.usage_metadata['input_tokens']}, "
            f"Output tokens: {response.usage_metadata['output_tokens']}, "
            f"Finish reason: {response.response_metadata['finish_reason']}, "
            f"Max tokens allowed: {llm.max_output_tokens}"
        )
    
        contains_code_marker, cleaned_raw_code = cleanup_raw_code_output(
            response.content, language=language
        )
        is_empty = cleaned_raw_code.strip() == ""

        if contains_code_marker:
            logger.warning("Response contained code block markers that were removed.")
        if is_empty:
            logger.error("Cleaned code output is empty.")
            return None
        return cleaned_raw_code
    except Exception as e:
        logger.error(f"Erreur lors de la génération du test: {str(e)}")
        logger.exception("Full traceback:")
        return None


def enhance_test(llm: ChatGoogleGenerativeAI, api_code, api_info, basic_test) -> str:
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
    advanced_test_prompt = UnitPrompts.get_advanced_test_prompt().prompt
    chain = advanced_test_prompt | llm
    logger.debug("Invoking LLM for test enhancement")
    response = chain.invoke(
        {
            "raw_source_code": api_code,
            "analysis_json": api_info,
            "basic_unit_tests": basic_test,
        }
    )
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Output tokens: {response.usage_metadata['output_tokens']}, "
        f"Finish reason: {response.response_metadata['finish_reason']}, "
        f"Max tokens allowed: {llm.max_output_tokens}"
    )

    contains_code_marker, cleaned_raw_code = cleanup_raw_code_output(
        response.content, language="python"
    )
    is_empty = cleaned_raw_code.strip() == ""

    if contains_code_marker:
        logger.warning(
            "code block found in enhanced test response, returning Cleaned raw content"
        )

    if is_empty:
        logger.error("Cleaned code output is empty.")
        return None

    return cleaned_raw_code
