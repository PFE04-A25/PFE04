from db.repositories.test_case import TestCaseRepository
from db.models.test_case import TestCase
from logger import setup_logger

logger = setup_logger()

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
        logger.info(f"Creating new test case of type {test_type}")
        return self.repository.create(test_case_obj)
    
    def get_test_cases(self, filter_dict=None):
        """Get all test cases"""
        return self.repository.find_all(filter_dict)
    
    def get_test_case(self, id: str):
        """Get test case by ID"""
        return self.repository.find_by_id(id)
    
    def delete_test_case(self, id: str) -> bool:
        """Delete a test case by ID"""
        return self.repository.delete(id)
    
    def update_test_case(self, id: str, update_data: dict) -> TestCase:
        """
        Update a test case by ID
        
        Args:
            id: The ID of the test case to update
            update_data: Dictionary containing the fields to update
            
        Returns:
            Updated TestCase object or None if not found
        """
        try:
            return self.repository.update(id, update_data)
        except Exception as e:
            logger.error(f"Error updating test case: {str(e)}")
            raise