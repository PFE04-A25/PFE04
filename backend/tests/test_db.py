import pytest
from bson import ObjectId

def test_db_connection(test_case_service):
    """Test that we can connect to the database."""
    # If this doesn't raise an exception, connection works
    test_cases = test_case_service.get_test_cases()
    assert isinstance(test_cases, list)

def test_db_insert(test_case_service):
    """Test that we can insert data into the database."""
    # Create a test case
    result = test_case_service.create_test_case(
        test_type="unit",
        source_code="public class Test {}",
        test_case="@Test public void test() {}"
    )
    
    # Verify the result has an ID
    assert result.id is not None
    assert isinstance(result.id, ObjectId)
    
    # Verify we can retrieve it
    test_cases = test_case_service.get_test_cases()
    assert len(test_cases) == 1
    assert test_cases[0].test_type == "unit"