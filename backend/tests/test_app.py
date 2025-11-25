
import json
import pytest
from unittest.mock import patch, MagicMock

@patch('gemini.setup_llm')
@patch('gemini.analyze_api_code')
@patch('gemini.generate_basic_test')
def test_rest_assured_generation(mock_generate_basic, mock_analyze, mock_setup_llm, client):
    """Test the RestAssured test generation endpoint."""
    # Mock the LLM and response functions
    mock_llm = MagicMock()
    mock_setup_llm.return_value = mock_llm
    
    mock_api_info = {
        "controller_name": "TestController",
        "base_path": "/api",
        "endpoints": [{"method": "GET", "path": "/test"}]
    }
    mock_analyze.return_value = mock_api_info
    
    mock_generate_basic.return_value = "public class ApiTest { @Test void testApi() {} }"
    
    # Send request to generate RestAssured test
    response = client.post(
        "/rest-assured-test/gemini",
        data=json.dumps({"api_code": "public class Api {}"}),
        content_type="application/json"
    )
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "generated_test" in data
    assert "public class ApiTest" in data["generated_test"]
    
    # Verify our mocks were called correctly
    mock_setup_llm.assert_called_once()
    mock_analyze.assert_called_once()
    mock_generate_basic.assert_called_once()