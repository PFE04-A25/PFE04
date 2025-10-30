from db.repositories.base_repository import BaseRepository
from db.models.test_execution import TestExecution


class TestExecutionRepository(BaseRepository[TestExecution]):
    def __init__(self, mongo_uri: str = None):
        super().__init__(TestExecution, mongo_uri)

    def find_by_test_generation_id(self, test_generation_id: str):
        """Find test executions by test generation ID"""
        return self.find_all({"test_generation_id": test_generation_id})
    
    def find_by_chrono(self, limit: int = 10):
        """Find test executions ordered by timestamp descending"""
        return self.find_all(sort=[("timestamp", -1)], limit=limit)
