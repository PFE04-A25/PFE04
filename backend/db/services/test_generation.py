from db.repositories.test_generation_repository import TestGenerationRepository
from db.models.test_generation import TestGeneration
from logger import get_logger
from typing import Optional, List, Dict

logger = get_logger("test_generation_service")


class TestGenerationService:
    def __init__(self):
        self.repository = TestGenerationRepository()

    def create_test_generation(
        self,
        model_id: str,
        pipeline_id: str,
        code_snippet_id: str,
        generated_analysis: str,
        generated_test: str,
        token_usage: dict = None,
        generation_time: float = None,
        executed: bool = False,
    ) -> TestGeneration:
        """Create a new test generation"""
        test_generation_obj = TestGeneration(
            model_id=model_id,
            pipeline_id=pipeline_id,
            code_snippet_id=code_snippet_id,
            generated_analysis=generated_analysis,
            generated_test=generated_test,
            token_usage=token_usage,
            generation_time=generation_time,
            executed=executed,
        )

        logger.info(f"Creating new test generation with ID {test_generation_obj.id}")
        return self.repository.create(test_generation_obj)

    def get_generation(self, generation_id: str) -> Optional[TestGeneration]:
        """Get a test generation by ID"""
        logger.info(f"Retrieving test generation with ID {generation_id}")
        return self.repository.find_by_id(generation_id)

    def get_generations_by_type(self, test_type: str) -> List[TestGeneration]:
        """Get all test generations of a specific test type"""
        return self.repository.find_by_test_type(test_type)

    def get_generations_by_model(self, model_id: str) -> List[TestGeneration]:
        """Get all test generations using a specific model"""
        return self.repository.find_by_model_id(model_id)

    def get_generations_by_pipeline(
        self, pipeline_id: str
    ) -> List[TestGeneration]:
        """Get all test generations using a specific pipeline"""
        return self.repository.find_by_pipeline_id(pipeline_id)

    def update_generation_executed(
        self, generation_id: str, executed: bool
    ) -> Optional[TestGeneration]:
        """Update the executed flag of a test generation"""
        logger.info(
            f"Updating executed flag for generation ID {generation_id} to {executed}"
        )
        return self.repository.update_executed_flag(generation_id, executed)
