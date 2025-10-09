
import json
import re
from logger import setup_logger
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.rest_prompt import (
    RestAssuredPrompts,
)

logger = setup_logger()

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
