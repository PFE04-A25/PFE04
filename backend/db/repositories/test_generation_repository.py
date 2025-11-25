from db.repositories.base_repository import BaseRepository
from db.models.test_generation import TestGeneration


class TestGenerationRepository(BaseRepository[TestGeneration]):
    """
    Repository pour interagir avec la collection 'test_generations'.
    Cette collection relie un code source, un prompt et un modèle IA à un test généré.
    """

    def __init__(self, mongo_uri: str = None):
        super().__init__(TestGeneration, mongo_uri)
        self.model_class = TestGeneration

    def find_by_test_type(self, test_type: str):
        """Find test cases by test type"""
        return self.find_all({"test_type": test_type})
    
    def find_by_model_id(self, model_id: str):
        """Find test generations by model ID"""
        return self.find_all({"model_id": model_id})

    def find_by_pipeline_id(self, pipeline_id: str):
        """Find test generations by pipeline ID"""
        return self.find_all({"pipeline_id": pipeline_id})

    def update_executed_flag(self, generation_id: str, executed: bool) -> TestGeneration:
        """Update the executed flag of a test generation"""
        update_data = {"executed": executed}
        return self.update({"_id": generation_id}, update_data)
