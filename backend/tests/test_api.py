import json
import pytest

def test_create_test_case_endpoint(client, cleanup_db):
    """Test the create test case endpoint."""
    # Prepare test data
    test_data = {
        "testType": "test_restassured",
        "sourceCode": "public class ExampleApi {}",
        "testCase": "public class ExampleTest {}"
    }
    
    # Send POST request
    response = client.post(
        "/db/testcases",
        data=json.dumps(test_data),
        content_type="application/json"
    )
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "id" in data
    assert data["testType"] == "test_restassured"

def test_get_test_cases_endpoint(client, cleanup_db):
    """Test the get test cases endpoint."""
    # Create a test case first
    test_data = {
        "testType": "test_restassured",
        "sourceCode": "public class ExampleApi {}",
        "testCase": "public class ExampleTest {}"
    }
    client.post(
        "/db/testcases",
        data=json.dumps(test_data),
        content_type="application/json"
    )
    
    # Send GET request
    response = client.get("/db/testcases")
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "testType" in data[0]
    assert data[0]["testType"] == "test_restassured"

def test_filter_test_cases_endpoint(client, cleanup_db):
    """Test filtering test cases by test type."""
    # Create test cases with different types
    client.post(
        "/db/testcases",
        data=json.dumps({
            "testType": "test_restassured",
            "sourceCode": "public class RestApi {}",
            "testCase": "public class RestTest {}"
        }),
        content_type="application/json"
    )
    
    client.post(
        "/db/testcases",
        data=json.dumps({
            "testType": "test_unit",
            "sourceCode": "public class UnitApi {}",
            "testCase": "public class UnitTest {}"
        }),
        content_type="application/json"
    )
    
    # Filter by testType
    response = client.get("/db/testcases?testType=test_unit")
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert all(tc["testType"] == "test_unit" for tc in data)