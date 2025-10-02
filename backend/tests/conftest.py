import pytest
from flask import Flask
import mongomock
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini import app as flask_app
from db.repositories.test_case import TestCaseRepository
from db.services.test_case import TestCaseService


@pytest.fixture
def app():
    """Create a Flask test application."""
    # Configure app for testing
    flask_app.config.update({
        "TESTING": True,
    })
    return flask_app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_mongo(monkeypatch):
    """Create a mock MongoDB client."""
    mock_client = mongomock.MongoClient()
    
    # Patch the MongoDB client in TestCaseRepository
    def mock_init(self, mongo_uri=None):
        self.client = mock_client
        self.db = mock_client.test_generator
        self.collection = self.db.test_cases
    
    monkeypatch.setattr(TestCaseRepository, "__init__", mock_init)
    return mock_client

@pytest.fixture
def test_case_service(mock_mongo):
    """Create a test case service with mock MongoDB."""
    return TestCaseService()


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