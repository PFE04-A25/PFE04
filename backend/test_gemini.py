import pytest
import prompts.rest_prompt
from gemini import app, setup_llm, analyze_api_code, generate_basic_test
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

"""List des pytests pour tester le fichier gemini.py et ses fonctions:

   1. setup_llm()
   2. analyze_api_code()
   3. generate_basic_test()
   4. generate_restassured_test()
   5. execute_tests()
   6. get_execution_status()
   7. get_detailed_metrics()"""

class FakeExecutor:
        def __init__(self,executions):
            self.test_executions = executions

class FakeResponse:
    content = '```json\n{"controller_name": "TestController", "endpoints": []}\n```' #Fake valid JSON response from LLM
    usage_metadata = {'input_tokens': 100, 'output_tokens': 200} #Simulate input token usage
    response_metadata = {'finish_reason': 'stop'} #Simulate finish reason

class FakeEmptyResponse:
    content = '' #Empty JSON response from LLM

class FakeLLM(Runnable):
    max_output_tokens = 8192
    
    def __init__(self, response_type='success'):
        # Allow the mock to be initialized to return different responses
        if response_type == 'empty':
            self.response = FakeEmptyResponse()
        else:
            self.response = FakeResponse()

    def invoke(self, input, config=None):
        """Matches the LangChain Runnable protocol."""
        return self.response

class Prompt: #Mocks the pipe operator, returning the next element (usually the LLM)
        def __or__(self, other):
            return other 
    
class FakePrompt: #Return an object holding the prompt chain  
    prompt = Prompt()           

@pytest.fixture
def client(): #Create an object client for Flask tests
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_setup_llm_missing_api(monkeypatch):
    """Cherche qu'une erreur est levée si la clé API est manquante."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False) #Create a test environment without the API key

    with pytest.raises(ValueError, match="Clé API Google Gemini non fournie"): #Check for a raised ValueError
        setup_llm()

def test_setup_llm_with_api(monkeypatch):
    """Vérifie que le LLM est configuré correctement avec une clé API."""

    FAKE_API_KEY = "fake_api_key"
    monkeypatch.setenv("GEMINI_API_KEY", FAKE_API_KEY) #Create a test environment with a fake API key
    llm = setup_llm()

    assert isinstance(llm, ChatGoogleGenerativeAI) #Check that the LLM is properly set up

def test_analyze_api_code_success():
    """Test si le LLM retourne une réponse JSON valide et que la fonction parse correctement le JSON."""
            
    #Initialize test parameters
    fake_llm = FakeLLM
    api_code = "public class TestController {}" 
    result = analyze_api_code(fake_llm, api_code)

    assert result is not None
    assert result['controller_name'] == "TestController"
    assert isinstance(result['endpoints'], list)

def test_analyze_api_code_failure():  
    """Test si une erreur est levée pour une réponse sans JSON/vide."""
    
    #Initialize test parameters     
    fake_llm = FakeEmptyResponse
    api_code = "public class TestController {}"
    result = analyze_api_code(fake_llm, api_code)

    assert result is None

def test_generate_basic_test_success(monkeypatch):
        
    #Implement dependencies without effecting the test  
    monkeypatch.setattr("code_manipulation.java.clean_java_code", lambda code: code.replace("Test", "TestCleaned"))
    monkeypatch.setattr("code_manipulation.java.fix_spring_boot_test_annotation", lambda code: code + "//fixed")
    monkeypatch.setattr(prompts.rest_prompt.RestAssuredPrompts, "get_basic_test_prompt", lambda: FakePrompt())

    #Initialize test parameters
    llm = FakeLLM()
    api_code = "public class TestController {}"
    api_info = {"controller_name": "TestController", "endpoints": []} 
    
    result = generate_basic_test(llm, api_code, api_info)
    
    assert "TestCleaned" in result
    assert "//fixed" in result

def test_generate_restassured_test_api_key(client, monkeypatch):
    """Testez le point de terminaison /rest-assured-test/gemini avec une fausse clé API et un LLM simulé"""

    #Implement dependencies without effecting the test  
    monkeypatch.setenv("GEMINI_API_KEY", "fake_api_key")
    monkeypatch.setattr("code_manipulation.java.clean_java_code", lambda code: code.replace("Test", "TestCleaned"))
    monkeypatch.setattr("code_manipulation.java.fix_spring_boot_test_annotation", lambda code: code + "//fixed")
    monkeypatch.setattr(prompts.rest_prompt.RestAssuredPrompts, "get_basic_test_prompt", lambda: FakePrompt())
    monkeypatch.setattr("gemini.setup_llm", lambda api_key=None: FakeLLM())
    monkeypatch.setattr("gemini.analyze_api_code", lambda llm, api_code: {"controller_name": "TestController", "endpoints": []})

    # Simulate post request to the endpoint
    response = client.post(
        "/rest-assured-test/gemini",
        json={"api_code": "public class TestController {}"}
    )
    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert "generated_test" in data
    assert "TestCleaned" in data["generated_test"]
    assert "//fixed" in data["generated_test"]

def test_execute_tests_missing_test_code(client):
    """"Test si le fonction retourne une erreur s'il manque un parameter `test_code`."""
    response = client.post("/execute-tests", json={"test_cde": "", "api_code": "test api code"})  #Implement response without test_code block   
    assert response.status_code == 400 #Check for 400 Error
    assert "Test code is required" in response.get_json()["error"]

def test_execute_tests_success(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une test_code et id."""
    class FakeExecutor:
        id = "fake id"
        def get_thread(self): 
            class thread:
                def start(self): pass
            return thread()

    #Implement dependencies without effecting the test   
    monkeypatch.setattr("gemini.JavaTestExecutor", lambda **kwargs: FakeExecutor())

    response = client.post("/execute-tests", json={"test_code": "test code", "api_code": "test api code"}) #Implement response with valid test_code and api_code
    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["execution_id"] == "fake id" 
    assert data["status"] == "started"

def test_get_execution_status_no_id(client):
    """Test si le fonction retourne le propre erreur si il manque une id."""
    response = client.get("/execution-status/<execution_id>")    
    assert response.status_code == 404 #Check for 404 Error if execution_id is missing

def test_get_execution_status_invalid_id(client):    
    """Test si le fonction retourne le propre erreur si il y a une id invalide."""
    response = client.get("/execution-status/invalid_id")
    assert response.status_code == 404 #Check for 404 Error if execution_id is invalid
    data = response.get_json()
    assert data is not None
    assert "error" in data

def test_get_execution_status_success(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide."""

    test_executions = { #Simulate a valid execution ID with status details
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {},
            "start_time": "now",
            "end_time": "later"
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor(executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)
    
    response = client.get("/execution-status/valid_id")
    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["execution_id"] == "valid_id"
    assert data["status"] == "completed"
    assert data["logs"] == "All tests passed"
    assert data["metrics"] == {}
    assert data["start_time"] == "now"
    assert data["end_time"] == "later"   

def test_get_detailed_metrics_missing_id(client):
    """"Test si le fonction retourne le propre erreur si il manque une id pour les métriques détaillées."""
    response = client.get("/execution-metrics/<execution_id>")
    assert response.status_code == 404 #Check for 404 Error if execution_id is missing

def test_get_detailed_metrics_invalid_id(client):
    """Test si le fonction retourne le propre erreur si il y a une id invalide pour les métriques détaillées."""
    response = client.get("/execution-metrics/invalid_id")
    assert response.status_code == 404 #Check for 404 Error if execution_id is invalid
    data = response.get_json()
    assert data is not None
    assert "error" in data    

def test_get_detailed_metrics_success(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées"""

    test_executions = {
        "valid_id": { #Create fake metris for simulation 
            "status": "completed",
            "logs": "All tests passed",
            "metrics": { 
                "line_coverage": 85.0,
                "branch_coverage": 75.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor(executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get("/execution-metrics/valid_id")
    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["execution_id"] == "valid_id" #Check if it returns the correct mock data
    assert data["metrics"]["line_coverage"] == 85.0
    assert data["metrics"]["branch_coverage"] == 75.0
    assert data["metrics"]["instruction_coverage"] == 80.0
    assert data["metrics"]["tests_per_endpoint"] == 2.0
    assert data["metrics"]["endpoints_count"] == 5
    assert data["metrics"]["tests_run"] == 10

def test_get_detailed_metrics_coverage_quality_poor(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une qualité couverture pauvre"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 50.0, 
                "branch_coverage": 40.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["coverage_quality"] == "poor" #Check for poor coverage quality

def test_get_detailed_metrics_coverage_quality_fair(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une qualité couverture fair"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 60.0, 
                "branch_coverage": 50.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["coverage_quality"] == "fair" #Check for fair coverage quality    

def test_get_detailed_metrics_coverage_quality_good(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une qualité couverture bonne"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 80.0, 
                "branch_coverage": 70.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["coverage_quality"] == "good" #Check for good coverage quality

def test_get_detailed_metrics_coverage_quality_excellent(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une qualité couverture excellent"""
    # class FakeExecutor:
    #     def __init__(self,executions):
    #         self.test_executions = executions
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 90.0, 
                "branch_coverage": 85.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["coverage_quality"] == "excellent" #Check for excellent coverage quality

def test_get_detailed_metrics_test_completeness_insufficient(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une complétude des tests insuffisantes"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 85.0, 
                "branch_coverage": 75.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 0.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["test_completeness"] == "insufficient" #Check for insufficient test completeness

def test_get_detailed_metrics_test_completeness_minimal(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une complétude des tests minimale"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 85.0, 
                "branch_coverage": 75.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 1.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["test_completeness"] == "minimal" #Check for minimal test completeness 

def test_get_detailed_metrics_test_completeness_adequate(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une complétude des tests adéquate"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 85.0, 
                "branch_coverage": 75.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 2.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["test_completeness"] == "adequate" #Check for adequate test completeness   

def test_get_detailed_metrics_test_completeness_comprehensive(client, monkeypatch):
    """Test si le fonction retourne le propre réponse si il y a une id valide pour les métriques détaillées avec une complétude des tests compréhensive"""
            
    execution_id = "valid_id"
    test_executions = {
        "valid_id": {
            "status": "completed",
            "logs": "All tests passed",
            "metrics": {  #Create fake metris for simulation 
                "line_coverage": 85.0, 
                "branch_coverage": 75.0,
                "instruction_coverage": 80.0,
                "tests_per_endpoint": 3.0,
                "endpoints_count": 5,
                "tests_run": 10
            }
        }
    }

    #Implement dependencies without effecting the test 
    monkeypatch.setattr("gemini.executor", FakeExecutor( executions=test_executions))
    monkeypatch.setattr("gemini.JavaTestExecutor", FakeExecutor)

    response = client.get(f"/execution-metrics/{execution_id}")

    assert response.status_code == 200 #Check for successful response
    data = response.get_json()
    assert data["quality_analysis"]["test_completeness"] == "comprehensive" #Check for comprehensive test completeness