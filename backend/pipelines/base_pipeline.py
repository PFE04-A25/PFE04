from logger import get_logger
from code_manipulation import java as java_utils
import re
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

logger = get_logger("base_pipeline")

class BasePipeline:
    """
    Base class for all pipelines.
    Provides common utilities for pipeline implementations.
    """
    def __init__(self, llm: ChatGoogleGenerativeAI, prompts: dict[int, PromptTemplate]):
        self.llm = llm
        self.prompts = prompts

    @staticmethod
    def _log_step(self, step_name: str, data):
        """Helper method to log pipeline step results"""
        logger.info(f"Pipeline Step: {step_name}")
        if isinstance(data, str):
            logger.debug(f"{step_name} - Output length: {len(data)} characters")
            logger.debug(f"{step_name} - Preview: {data[:200]}...")
        elif isinstance(data, dict):
            logger.debug(f"{step_name} - Output keys: {list(data.keys())}")
            for key, value in data.items():
                if isinstance(value, str):
                    logger.debug(f"{step_name} - {key} length: {len(value)} characters")
        return data
    
    def extract_json_from_response(self,response: str) -> str:
        """
        Extrait le JSON d'une réponse textuelle, en nettoyant les marqueurs markdown.
        """
        # Extraire le JSON de la réponse (peut être encapsulé dans des blocs de code)
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
        if json_match:
            logger.debug("JSON block found in response.")
            json_str = json_match.group(1)  # Si un bloc JSON est trouvé, on l'extrait
        else:
            logger.debug("No JSON block found, using full response content.")
            json_str = response  # Sinon, on prend tout le texte brute
        # Nettoyer et parser le JSON
        api_info = json.loads(json_str)
        return api_info

    @staticmethod
    def extract_java_code(response:str)->str:
        """
        Extrait le code Java d'une réponse textuelle, en nettoyant les marqueurs markdown.

        Arguments:
            response: Réponse textuelle contenant potentiellement du code Java
        Retourne:
            Code Java nettoyé
        """
        # Extraire le code Java de la réponse
        java_match = re.search(r"```(?:java)?\s*([\s\S]*?)\s*```", response)
        if java_match:
            logger.debug("Java code block found in response.")
            test_code = java_match.group(1).strip()
        else:
            logger.warning("No Java code block found in response, returning raw content")
            test_code = response.strip()

        # Nettoyer le code des marqueurs markdown résiduels
        test_code = java_utils.clean_java_code(test_code)

        # Corriger les annotations Spring Boot pour spécifier la classe d'application
        test_code = java_utils.fix_spring_boot_test_annotation(test_code)
        return test_code
    
    def create_pipeline_chain(self, **kwargs):
        """Method to create the pipeline chain. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement create_pipeline_chain method.")
    
    def generate(self, **kwargs):
        """Method to run the pipeline. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate method.")