from db.repositories.base_repository import BaseRepository
from db.models.test_case import TestCase

class TestCaseRepository(BaseRepository[TestCase]):
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017"):
        super().__init__(TestCase, mongo_uri)
    
    def find_by_test_type(self, test_type: str):
        """Find test cases by test type"""
        return self.find_all({"test_type": test_type})