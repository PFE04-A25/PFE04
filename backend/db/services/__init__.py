from logger import get_logger

logger = get_logger("db_services")

from db.services.code_snippet import CodeSnippetService
from db.services.pipeline import PipelineService
from db.services.prompt_template import PromptTemplateService
from db.services.model import ModelService
from db.services.test_generation import TestGenerationService
from db.services.test_execution import TestExecutionService

class Services:

    def __init__(self):
        logger.info("Initializing all database services")
        self.pipeline_service = PipelineService()
        self.prompt_template_service = PromptTemplateService()
        self.model_service = ModelService()
        self.test_generation_service = TestGenerationService()
        self.code_snippet_service = CodeSnippetService()
        self.test_execution_service = TestExecutionService()
        logger.info("All database services initialized successfully")
    # TODO - Implémenter des fonctions pour orchestrer des opérations entre plusieurs services si nécessaire