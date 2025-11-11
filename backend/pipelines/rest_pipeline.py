import json
import re
from logger import get_logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate

from prompts.rest_prompt import (
    RestAssuredPrompts,
)
from pipelines.base_pipeline import BasePipeline

from code_manipulation import java as java_utils

logger = get_logger()

# TODO (Refactoring) - Implémenter cette classe dans le serveur Gemini pour faciliter la génération (à tester avant)
class RestPipeline(BasePipeline):
    """
    Pipeline pour analyser le code API Spring Boot et générer des tests RestAssured.
    """

    def create_pipeline_chain(self, skip_enhancement: bool = False):
        """
        Create a unified LangChain pipeline for REST test generation.
    
        Pipeline flow:
        1. API Analysis: Extract structured information from API code
        2. Basic Test Generation: Generate initial RestAssured test
        3. Enhancement (optional): Add advanced test scenarios
        
        Args:
            llm: The language model instance
            skip_enhancement: Whether to skip the enhancement step
        
        Returns:
            A runnable pipeline that takes api_code and returns generated test
        """
        # Note - On pourrait rajouter un log dans chaque étape
        # Step 1: API Analysis Chain
        analysis_chain = (
            self.prompts.get(1)
            | self.llm
            | RunnableLambda(lambda x: self.extract_json_from_response(x.content))
            # | RunnableLambda(lambda x: self._log_step("Analysis", x))
        )
    
        # Step 2: Basic Test Generation Chain
        basic_test_chain = (
            self.prompts.get(2)
            | self.llm
            | RunnableLambda(lambda x: self.extract_java_code(x.content))
        )
        if skip_enhancement:
            # Simple 2-step pipeline: Analysis -> Basic Test
            pipeline = (
                {
                    "api_code": RunnablePassthrough(),
                    "api_info": analysis_chain
                }
                | RunnableLambda(lambda x: {
                    "api_code": x["api_code"],
                    "api_info": json.dumps(x["api_info"], indent=2)
                })
                | basic_test_chain
            )
        else:
            # Full 3-step pipeline: Analysis -> Basic Test -> Enhancement
            enhancement_chain = (
                self.prompts.get(3)
                | self.llm
                | RunnableLambda(lambda x: self.extract_java_code(x.content))
            )
            
            pipeline = (
                {
                    "api_code": RunnablePassthrough(),
                    "api_info": analysis_chain
                }
                | RunnableLambda(lambda x: {
                    "api_code": x["api_code"],
                    "api_info": json.dumps(x["api_info"], indent=2)
                })
                | RunnableLambda(lambda x: {
                    "api_code": x["api_code"],
                    "basic_test": basic_test_chain.invoke(x)
                })
                | enhancement_chain
            )
        
        return pipeline
    
    def generate(self, code_snippet: str, skip_enhancement: bool = False) -> str:
        """
        Exécute le pipeline complet pour générer un test RestAssured.

        Arguments:
            code_snippet: Code Java Spring Boot de l'API à tester
        Retourne:
            Code Java du test RestAssured généré
        """
        logger.info("Starting RestAssured test generation pipeline")
        logger.debug(f"API code snippet length: {len(code_snippet)} characters")
        
        pipeline = self.create_pipeline_chain(skip_enhancement=skip_enhancement)
        generated_test = pipeline.invoke({"api_code": code_snippet})
        return generated_test

def analyze_api_code(llm, api_code, api_analysis_prompt: PromptTemplate):
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
        if isinstance(api_analysis_prompt, str):
            api_analysis_prompt = PromptTemplate.from_template(api_analysis_prompt)

        # Utiliser l'API du model avec LangChain
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


def generate_basic_test(llm: ChatGoogleGenerativeAI, api_code, api_info, basic_test_prompt: PromptTemplate):
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
    chain = basic_test_prompt | llm
    logger.debug("Prompt chain for basic test created.")
    response = chain.invoke({"api_code": api_code, "api_info": api_info_str})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Output tokens: {response.usage_metadata['output_tokens']}, "
        f"Finish reason: {response.response_metadata['finish_reason']}, "
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


def enhance_test(llm: ChatGoogleGenerativeAI, api_code, basic_test, advanced_test_prompt: PromptTemplate):
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
    chain = advanced_test_prompt | llm
    logger.debug("Invoking LLM for test enhancement")
    response = chain.invoke({"api_code": api_code, "basic_test": basic_test})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Output tokens: {response.usage_metadata['output_tokens']}, "
        f"Finish reason: {response.response_metadata['finish_reason']}, "
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