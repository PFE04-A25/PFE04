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

@pytest.fixture(scope="function", autouse=True)
def cleanup_db():
    """Fixture to clean up test data before and after tests."""
    # Pre-test cleanup (optional)
    yield
    # Post-test cleanup
    try:
        from db.services.test_case import TestCaseService
        service = TestCaseService()
        
        # Find all test data (using a prefix convention)
        test_cases = service.get_test_cases({"testType": {"$regex": "^test_"}})
        
        # Delete all test data
        for case in test_cases:
            service.delete_test_case(case.id)
        
        print(f"Cleaned up {len(test_cases)} test records")
    except Exception as e:
        print(f"Error during test cleanup: {e}")
