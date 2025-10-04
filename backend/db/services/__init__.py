from db.repositories.test_case import TestCaseRepository
from db.models.test_case import TestCase

class TestCaseService:
    def __init__(self):
        self.repository = TestCaseRepository()
    
    def create_test_case(self, test_type: str, source_code: str, test_case: str) -> TestCase:
        """Create a new test case"""
        test_case_obj = TestCase(
            test_type=test_type,
            source_code=source_code,
            test_case=test_case
        )
        return self.repository.create(test_case_obj)
    
    def get_test_cases(self, filter_dict=None):
        """Get all test cases"""
        return self.repository.find_all(filter_dict)
    
    def get_test_case(self, id: str):
        """Get test case by ID"""
        return self.repository.find_by_id(id)