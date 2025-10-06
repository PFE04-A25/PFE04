import pytest
from bson import ObjectId

from db.services.test_case import TestCaseService

def test_db_connection(test_case_service=TestCaseService()):
    """Test that we can connect to the database."""
    # If this doesn't raise an exception, connection works
    test_cases = test_case_service.get_test_cases()
    assert isinstance(test_cases, list)

def test_db_crud(test_case_service=TestCaseService()):
    """Test that we can insert data into the database."""
    # Get all test cases before insertion
    before_insert = test_case_service.get_test_cases()
    before_count = len(before_insert)

    # Create a test case
    result = test_case_service.create_test_case(
        test_type="test_db",
        source_code="public class Test {}",
        test_case="@Test public void test() {}"
    )
    
    # Verify the result has an ID
    assert result.id is not None
    assert isinstance(result.id, ObjectId)
    
    # Verify we can retrieve it
    test_cases = test_case_service.get_test_cases()
    assert len(test_cases) == before_count + 1
    assert test_cases[-1].test_type == "test_db"

    test_case_service.repository.delete(result.id)  # Clean up

    # Verify it was deleted
    after_delete = test_case_service.get_test_cases()
    assert len(after_delete) == before_count
    
    # Try to find it by ID - should return None
    deleted_test = test_case_service.get_test_case(result.id)
    assert deleted_test is None