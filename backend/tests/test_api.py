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
    assert "testType" in data[-1]
    assert data[-1]["testType"] == "test_restassured"

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

def test_delete_test_case_endpoint(client, cleanup_db):
    """Test the delete test case endpoint."""
    # Create a test case first
    test_data = {
        "testType": "test_delete",
        "sourceCode": "public class DeleteTest {}",
        "testCase": "public class TestToDelete {}"
    }
    
    # Create the test case
    response = client.post(
        "/db/testcases",
        data=json.dumps(test_data),
        content_type="application/json"
    )
    
    # Get the ID of the created test case
    data = json.loads(response.data)
    test_id = data["id"]
    
    # Delete the test case
    delete_response = client.delete(f"/db/testcases/{test_id}")
    
    # Check response
    assert delete_response.status_code == 200
    delete_data = json.loads(delete_response.data)
    assert "message" in delete_data
    assert delete_data["message"] == "Test case deleted"
    
    # Verify it's deleted by trying to get it from the GET endpoint
    get_response = client.get("/db/testcases")
    get_data = json.loads(get_response.data)
    
    # Ensure it doesn't exist in the returned data
    test_ids = [item["id"] for item in get_data]
    assert test_id not in test_ids

def test_update_test_case_endpoint(client, cleanup_db):
    """Test the update test case endpoint."""
    # Create a test case first
    test_data = {
        "testType": "test_update_original",
        "sourceCode": "public class OriginalTest {}",
        "testCase": "public class TestOriginal {}"
    }
    
    # Create the test case
    response = client.post(
        "/db/testcases",
        data=json.dumps(test_data),
        content_type="application/json"
    )
    
    # Get the ID of the created test case
    data = json.loads(response.data)
    test_id = data["id"]
    
    # Update data
    update_data = {
        "testType": "test_update_modified",
        "sourceCode": "public class ModifiedTest {}",
        "testCase": "public class TestModified {}"
    }
    
    # Update the test case
    update_response = client.put(
        f"/db/testcases/{test_id}",
        data=json.dumps(update_data),
        content_type="application/json"
    )
    
    # Check response
    assert update_response.status_code == 200
    update_result = json.loads(update_response.data)
    assert update_result["id"] == test_id
    assert update_result["testType"] == "test_update_modified"
    assert update_result["sourceCode"] == "public class ModifiedTest {}"
    assert update_result["testCase"] == "public class TestModified {}"
    
    # Verify update by getting the test case
    get_response = client.get("/db/testcases")
    get_data = json.loads(get_response.data)
    
    # Find our updated test case in the list
    updated_test = next((item for item in get_data if item["id"] == test_id), None)
    assert updated_test is not None
    assert updated_test["testType"] == "test_update_modified"
    assert updated_test["sourceCode"] == "public class ModifiedTest {}"
    assert updated_test["testCase"] == "public class TestModified {}"