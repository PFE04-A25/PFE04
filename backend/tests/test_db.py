import pytest
from bson import ObjectId

from db.services.test_case import TestCaseService

def test_db_connection(test_case_service=TestCaseService()):
    """Test that we can connect to the database."""
    # If this doesn't raise an exception, connection works
    test_cases = test_case_service.get_test_cases()
    assert isinstance(test_cases, list)

def test_db_insert(test_case_service=TestCaseService()):
    """Test that we can insert data into the database."""
    # Create a test case
    result = test_case_service.create_test_case(
        test_type="test",
        source_code="public class Test {}",
        test_case="@Test public void test() {}"
    )
    
    # Verify the result has an ID
    assert result.id is not None
    assert isinstance(result.id, ObjectId)
    
    # Verify we can retrieve it
    test_cases = test_case_service.get_test_cases()
    assert test_cases[-1].test_type == "test"