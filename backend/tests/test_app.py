
import json
import pytest
from unittest.mock import patch, MagicMock

class TestRestAssuredGeneration:
    ##############
    # RestAssured Test Generation Endpoint Tests
    ##############

    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    @patch('pipelines.rest_pipeline.analyze_api_code')
    @patch('pipelines.rest_pipeline.generate_basic_test')
    def test_rest_assured_generation_success(self,mock_generate_basic, mock_analyze, mock_setup_llm, mock_db_services, client, monkeypatch):
        """Test successful RestAssured test generation endpoint."""
        monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
        
        # Mock LLM
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        # Mock database services
        mock_model = MagicMock()
        mock_model.id = "model_123"
        mock_db_services.model_service.get_models_by_name.return_value = [mock_model]
        
        mock_pipeline = MagicMock()
        mock_pipeline.id = "pipeline_123"
        mock_pipeline.prompts = [
            {"prompt_id": "prompt_1", "order": 1},
            {"prompt_id": "prompt_2", "order": 2}
        ]
        mock_db_services.pipeline_service.get_pipeline_active_by_name.return_value = [mock_pipeline]
        
        mock_prompt_1 = MagicMock()
        mock_prompt_1.template_text = "Analyze this API: {api_code}"
        mock_prompt_1.input_variables = ["api_code"]
        mock_prompt_1.partial_variables = {}
        
        mock_prompt_2 = MagicMock()
        mock_prompt_2.template_text = "Generate test for: {api_code}"
        mock_prompt_2.input_variables = ["api_code"]
        mock_prompt_2.partial_variables = {}
        
        mock_db_services.prompt_template_service.get_prompt_template.side_effect = [mock_prompt_1, mock_prompt_2]
        
        mock_snippet = MagicMock()
        mock_snippet.id = "snippet_123"
        mock_db_services.code_snippet_service.create_code_snippet.return_value = mock_snippet
        
        mock_generation = MagicMock()
        mock_generation.id = "generation_123"
        mock_db_services.test_generation_service.create_test_generation.return_value = mock_generation
        
        # Mock pipeline functions
        mock_api_info = {
            "controller_name": "TestController",
            "base_path": "/api",
            "endpoints": [{"method": "GET", "path": "/test"}]
        }
        mock_analyze.return_value = mock_api_info
        mock_generate_basic.return_value = "public class ApiTest { @Test void testApi() {} }"
        
        # Send request
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({"api_code": "public class Api {}"}),
            content_type="application/json"
        )
        
        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "generated_test" in data
        assert "generation_id" in data
        assert "public class ApiTest" in data["generated_test"]
        assert data["generation_id"] == "generation_123"
        
        # Verify mocks were called
        mock_setup_llm.assert_called_once()
        mock_analyze.assert_called_once()
        mock_generate_basic.assert_called_once()
        mock_db_services.code_snippet_service.create_code_snippet.assert_called_once()
        mock_db_services.test_generation_service.create_test_generation.assert_called_once()

    def test_rest_assured_generation_missing_api_code(self,client):
        """Test RestAssured generation when api_code parameter is missing."""
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({}),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing api_code parameter" in data["error"]

    def test_rest_assured_generation_missing_api_key(self,client, monkeypatch):
        """Test RestAssured generation when GEMINI_API_KEY is missing."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({"api_code": "public class Api {}"}),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "GEMINI_API_KEY" in data["error"]

    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    def test_rest_assured_generation_model_not_found(self,mock_setup_llm, mock_db_services, client):
        """Test RestAssured generation when model is not found in database."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        # Model not found
        mock_db_services.model_service.get_models_by_name.return_value = []
        
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({"api_code": "public class Api {}"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Model 'Gemini' not found" in data["error"]

    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    def test_rest_assured_generation_no_active_pipeline(self,mock_setup_llm, mock_db_services, client):
        """Test RestAssured generation when no active pipeline is found."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        mock_model = MagicMock()
        mock_model.id = "model_123"
        mock_db_services.model_service.get_models_by_name.return_value = [mock_model]
        
        # No active pipeline
        mock_db_services.pipeline_service.get_pipeline_active_by_name.return_value = []
        
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({"api_code": "public class Api {}"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "No active pipeline found for 'REST'" in data["error"]


    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    @patch('pipelines.rest_pipeline.analyze_api_code')
    def test_rest_assured_generation_analysis_fails(self,mock_analyze, mock_setup_llm, mock_db_services, client):
        """Test RestAssured generation when API analysis fails."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        # Setup database mocks
        mock_model = MagicMock()
        mock_model.id = "model_123"
        mock_db_services.model_service.get_models_by_name.return_value = [mock_model]
        
        mock_pipeline = MagicMock()
        mock_pipeline.id = "pipeline_123"
        mock_pipeline.prompts = [{"prompt_id": "prompt_1", "order": 1}]
        mock_db_services.pipeline_service.get_pipeline_active_by_name.return_value = [mock_pipeline]
        
        mock_prompt = MagicMock()
        mock_prompt.template_text = "Analyze: {api_code}"
        mock_prompt.input_variables = ["api_code"]
        mock_prompt.partial_variables = {}
        mock_db_services.prompt_template_service.get_prompt_template.return_value = mock_prompt
        
        # Analysis fails
        mock_analyze.return_value = None
        
        response = client.post(
            "/rest-assured-test/gemini",
            data=json.dumps({"api_code": "public class Api {}"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "API analysis failed" in data["error"]

    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    @patch('pipelines.rest_pipeline.analyze_api_code')
    @patch('pipelines.rest_pipeline.generate_basic_test')
    def test_rest_assured_generation_basic_test_fails(self,mock_generate_basic, mock_analyze, mock_setup_llm, mock_db_services, client):
        """Test RestAssured generation when basic test generation fails."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        # Setup database mocks
        mock_model = MagicMock()
        mock_model.id = "model_123"
        mock_db_services.model_service.get_models_by_name.return_value = [mock_model]
        
        mock_pipeline = MagicMock()
        mock_pipeline.id = "pipeline_123"
        mock_pipeline.prompts = [{"prompt_id": "prompt_1", "order": 1}, {"prompt_id": "prompt_2", "order": 2}]
        mock_db_services.pipeline_service.get_pipeline_active_by_name.return_value = [mock_pipeline]
        
        mock_prompt = MagicMock()
        mock_prompt.template_text = "Analyze: {api_code}"
        mock_prompt.input_variables = ["api_code"]
        mock_prompt.partial_variables = {}
        mock_db_services.prompt_template_service.get_prompt_template.return_value = mock_prompt
        
        # Mock analysis to return valid info
        mock_api_info = {"controller_name": "TestController"}
        mock_analyze.return_value = mock_api_info

        # Mock basic test generation to fail
        mock_generate_basic.return_value = None
        
        # Patch generate_basic_test to return None (failure)
        with patch('pipelines.rest_pipeline.generate_basic_test', return_value=None):
            response = client.post(
                "/rest-assured-test/gemini",
                data=json.dumps({"api_code": "public class Api {}"}),
                content_type="application/json"
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
            assert "Basic test generation failed" in data["error"]

    @patch('gemini.db_services')
    @patch('gemini.setup_llm')
    @patch('pipelines.rest_pipeline.analyze_api_code')
    def test_rest_assured_generation_missing_prompt(self,mock_analyze, mock_setup_llm, mock_db_services, client):
        """Test RestAssured generation when basic test generation fails."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        # Setup database mocks
        mock_model = MagicMock()
        mock_model.id = "model_123"
        mock_db_services.model_service.get_models_by_name.return_value = [mock_model]
        
        mock_pipeline = MagicMock()
        mock_pipeline.id = "pipeline_123"
        mock_pipeline.prompts = [{"prompt_id": "prompt_1", "order": 1}]
        mock_db_services.pipeline_service.get_pipeline_active_by_name.return_value = [mock_pipeline]
        
        mock_prompt = MagicMock()
        mock_prompt.template_text = "Analyze: {api_code}"
        mock_prompt.input_variables = ["api_code"]
        mock_prompt.partial_variables = {}
        mock_db_services.prompt_template_service.get_prompt_template.return_value = mock_prompt
        
        # Mock analysis to return valid info
        mock_api_info = {"controller_name": "TestController"}
        mock_analyze.return_value = mock_api_info
        
        # Patch generate_basic_test to return None (failure)
        with patch('pipelines.rest_pipeline.generate_basic_test', return_value=None):
            response = client.post(
                "/rest-assured-test/gemini",
                data=json.dumps({"api_code": "public class Api {}"}),
                content_type="application/json"
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
            assert "Missing prompt for basic test generation step" in data["error"]

class TestUnitTestGeneration:
    ##############
    # Unit Test Generation Endpoint Tests
        ##############
    @patch('gemini.setup_llm')
    @patch('pipelines.unit_pipeline.analyze_code')
    @patch('pipelines.unit_pipeline.generate_basic_test')
    @patch('pipelines.unit_pipeline.enhance_test')
    def test_unit_test_generation(self,mock_enhance, mock_generate_basic, mock_analyze, mock_setup_llm, client):
        """Test the unit test generation endpoint with enhancement enabled."""
        # Mock the LLM and response functions
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        mock_code_info = {
            "class_name": "Calculator",
            "methods": [{"name": "add", "params": ["a", "b"]}]
        }
        mock_analyze.return_value = mock_code_info
        
        mock_generate_basic.return_value = "def test_calculator(): pass"
        mock_enhance.return_value = "def test_calculator_enhanced(): assert True"
        
        # Send request to generate unit test
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({"api_code": "class Calculator: pass"}),
            content_type="application/json"
        )
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "generated_test" in data
        assert "test_calculator_enhanced" in data["generated_test"]
        
        # Verify our mocks were called correctly
        mock_setup_llm.assert_called_once()
        mock_analyze.assert_called_once()
        mock_generate_basic.assert_called_once()
        mock_enhance.assert_called_once()

    @patch('gemini.setup_llm')
    @patch('pipelines.unit_pipeline.analyze_code')
    @patch('pipelines.unit_pipeline.generate_basic_test')
    @patch('pipelines.unit_pipeline.enhance_test')
    def test_unit_test_generation_enhancement_fails(self,mock_enhance, mock_generate_basic, mock_analyze, mock_setup_llm, client):
        """Test unit test generation when enhancement fails, should return basic test."""
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        mock_code_info = {"class_name": "Calculator", "methods": []}
        mock_analyze.return_value = mock_code_info
        
        mock_generate_basic.return_value = "def test_basic(): pass"
        mock_enhance.return_value = ""  # Enhancement fails with empty string
        
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({"api_code": "class Calculator: pass"}),
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "generated_test" in data
        assert data["generated_test"] == "def test_basic(): pass"
        assert "error" in data
        assert "Enhanced test generation failed" in data["error"]

    @patch('gemini.get_gemini_key')
    def test_unit_test_generation_missing_api_key(self,mock_get_key, client):
        """Test unit test generation when GEMINI_API_KEY is missing."""
        mock_get_key.return_value = None
        
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({"api_code": "class Calculator: pass"}),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "GEMINI_API_KEY" in data["error"]

    def test_unit_test_generation_missing_api_code(self,client):
        """Test unit test generation when api_code parameter is missing."""
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({}),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing api_code parameter" in data["error"]

    @patch('gemini.setup_llm')
    @patch('pipelines.unit_pipeline.analyze_code')
    def test_unit_test_generation_analysis_fails(self,mock_analyze, mock_setup_llm, client):
        """Test unit test generation when code analysis fails."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        mock_analyze.return_value = None  # Analysis fails
        
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({"api_code": "class Calculator: pass"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "API analysis failed" in data["error"]

    @patch('gemini.setup_llm')
    @patch('pipelines.unit_pipeline.analyze_code')
    @patch('pipelines.unit_pipeline.generate_basic_test')
    def test_unit_test_generation_basic_test_fails(self,mock_generate_basic, mock_analyze, mock_setup_llm, client):
        """Test unit test generation when basic test generation fails."""
        
        mock_llm = MagicMock()
        mock_setup_llm.return_value = mock_llm
        
        mock_code_info = {"class_name": "Calculator"}
        mock_analyze.return_value = mock_code_info
        mock_generate_basic.return_value = None  # Basic test generation fails
        
        response = client.post(
            "/unit-test/gemini",
            data=json.dumps({"api_code": "class Calculator: pass"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Basic test generation failed" in data["error"]

class TestExecution:
    ##############
    # Execution of the test suite
    ##############
    
    @patch('gemini.db_services')
    @patch('gemini.JavaTestExecutor')
    @patch('gemini.threading.Thread')
    def test_execute_tests_success(self, mock_thread, mock_executor_class, mock_db_services, client):
        """Test successful test execution initiation."""
        # Mock database service
        mock_execution = MagicMock()
        mock_execution.id = "exec_123"
        mock_db_services.test_execution_service.create_test_execution.return_value = mock_execution
        
        # Mock executor
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance
        
        # Mock thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Send request
        response = client.post(
            "/execute-tests",
            data=json.dumps({
                "test_code": "public class Test { @Test void test() {} }",
                "api_code": "public class Api {}",
                "test_generation_id": "gen_123"
            }),
            content_type="application/json"
        )
        
        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "execution_id" in data
        assert data["execution_id"] == "exec_123"
        assert data["status"] == "started"
        assert data["message"] == "Test execution started"
        
        # Verify execution was created
        mock_db_services.test_execution_service.create_test_execution.assert_called_once()
        call_args = mock_db_services.test_execution_service.create_test_execution.call_args[1]
        assert call_args["test_generation_id"] == "gen_123"
        assert call_args["build_success"] == False
        assert call_args["tests_run"] == 0
        
        # Verify thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_execute_tests_missing_test_code(self, client):
        """Test execution fails when test_code is missing."""
        response = client.post(
            "/execute-tests",
            data=json.dumps({
                "api_code": "public class Api {}",
                "test_generation_id": "gen_123",
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Test code is required" in data["error"]

    def test_execute_tests_empty_test_code(self, client):
        """Test execution fails when test_code is empty."""
        response = client.post(
            "/execute-tests",
            data=json.dumps({
                "test_code": "   ",
                "api_code": "public class Api {}",
                "test_generation_id": "gen_123"
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Test code is required" in data["error"]

    @patch('gemini.db_services')
    def test_execute_tests_db_creation_fails(self, mock_db_services, client):
        """Test execution handles database creation failure."""
        # Mock database service to raise exception
        mock_db_services.test_execution_service.create_test_execution.side_effect = Exception("DB Error")
        
        response = client.post(
            "/execute-tests",
            data=json.dumps({
                "test_code": "public class Test {}",
                "api_code": "public class Api {}",
                "test_generation_id": "gen_123",
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "DB Error" in data["error"]

    @patch('gemini.db_services')
    @patch('gemini.JavaTestExecutor')
    @patch('gemini.threading.Thread')
    def test_execute_tests_without_generation_id(self, mock_thread, mock_executor_class, mock_db_services, client):
        """Test execution without test_generation_id."""
        mock_execution = MagicMock()
        mock_execution.id = "exec_789"
        mock_db_services.test_execution_service.create_test_execution.return_value = mock_execution
        
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        response = client.post(
            "/execute-tests",
            data=json.dumps({
                "test_code": "public class Test {}",
                "api_code": "public class Api {}",
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        assert "error" in json.loads(response.data)
        assert "test_generation_id is required" in json.loads(response.data)["error"]


class TestExecutionStatus:
    """Tests for the /execution-status/<execution_id> endpoint."""
    
    @patch('gemini.db_services')
    def test_get_execution_status_running(self, mock_db_services, client):
        """Test fetching status of a running execution."""
        mock_execution = MagicMock()
        mock_execution.build_success = False
        mock_execution.logs = "Execution started..."
        mock_execution.tests_run = 0
        mock_execution.failure_count = 0
        mock_execution.error_count = 0
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 0.0
        mock_execution.line_coverage = 0.0
        mock_execution.execution_time = 0.0
        mock_execution.timestamp = 1234567890.0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-status/exec_123")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["execution_id"] == "exec_123"
        assert data["status"] == "running"
        assert data["logs"] == "Execution started..."
        assert data["metrics"]["tests_run"] == 0
        assert data["end_time"] is None

    @patch('gemini.db_services')
    def test_get_execution_status_completed(self, mock_db_services, client):
        """Test fetching status of a completed execution."""
        mock_execution = MagicMock()
        mock_execution.build_success = True
        mock_execution.logs = "All tests passed"
        mock_execution.tests_run = 5
        mock_execution.failure_count = 0
        mock_execution.error_count = 0
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 100.0
        mock_execution.line_coverage = 85.5
        mock_execution.execution_time = 2.5
        mock_execution.timestamp = 1234567890.0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-status/exec_456")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "completed"
        assert data["metrics"]["tests_run"] == 5
        assert data["metrics"]["success_rate"] == 100.0
        assert data["metrics"]["line_coverage"] == 85.5
        assert data["end_time"] is not None

    @patch('gemini.db_services')
    def test_get_execution_status_failed(self, mock_db_services, client):
        """Test fetching status of a failed execution."""
        mock_execution = MagicMock()
        mock_execution.build_success = False
        mock_execution.logs = "Execution failed: Compilation error"
        mock_execution.tests_run = 0
        mock_execution.failure_count = 0
        mock_execution.error_count = 0
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 0.0
        mock_execution.line_coverage = 0.0
        mock_execution.execution_time = 0.0
        mock_execution.timestamp = 1234567890.0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-status/exec_789")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "failed"
        assert "failed" in data["logs"].lower()

    @patch('gemini.db_services')
    def test_get_execution_status_not_found(self, mock_db_services, client):
        """Test fetching status for non-existent execution."""
        mock_db_services.test_execution_service.get_test_execution.return_value = None
        
        response = client.get("/execution-status/nonexistent")
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "Execution not found" in data["error"]

    @patch('gemini.db_services')
    def test_get_execution_status_with_failures(self, mock_db_services, client):
        """Test fetching status with test failures."""
        mock_execution = MagicMock()
        mock_execution.build_success = True
        mock_execution.logs = "Tests completed with failures"
        mock_execution.tests_run = 10
        mock_execution.failure_count = 2
        mock_execution.error_count = 1
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 70.0
        mock_execution.line_coverage = 60.0
        mock_execution.execution_time = 3.2
        mock_execution.timestamp = 1234567890.0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-status/exec_test")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metrics"]["failures"] == 2
        assert data["metrics"]["errors"] == 1
        assert data["metrics"]["success_rate"] == 70.0


class TestExecutionMetrics:
    """Tests for the /execution-metrics/<execution_id> endpoint."""
    
    @patch('gemini.db_services')
    def test_get_detailed_metrics_excellent_coverage(self, mock_db_services, client):
        """Test metrics endpoint with excellent coverage."""
        mock_execution = MagicMock()
        mock_execution.tests_run = 15
        mock_execution.failure_count = 0
        mock_execution.error_count = 0
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 100.0
        mock_execution.build_success = True
        mock_execution.line_coverage = 92.0
        mock_execution.branch_coverage = 88.0
        mock_execution.instruction_coverage = 90.0
        mock_execution.lines_covered = 460
        mock_execution.lines_total = 500
        mock_execution.branches_covered = 88
        mock_execution.branches_total = 100
        mock_execution.instructions_covered = 900
        mock_execution.instructions_total = 1000
        mock_execution.endpoints_count = 5
        mock_execution.tests_per_endpoint = 3.0
        mock_execution.execution_time = 4.5
        mock_execution.return_code = 0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-metrics/exec_excellent")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["quality_analysis"]["coverage_quality"] == "excellent"
        assert data["quality_analysis"]["test_completeness"] == "comprehensive"
        assert data["quality_analysis"]["overall_score"] > 80.0
        assert len(data["recommendations"]) > 0

    @patch('gemini.db_services')
    def test_get_detailed_metrics_poor_coverage(self, mock_db_services, client):
        """Test metrics endpoint with poor coverage."""
        mock_execution = MagicMock()
        mock_execution.tests_run = 3
        mock_execution.failure_count = 0
        mock_execution.error_count = 0
        mock_execution.skipped_count = 0
        mock_execution.success_rate = 100.0
        mock_execution.build_success = True
        mock_execution.line_coverage = 45.0
        mock_execution.branch_coverage = 30.0
        mock_execution.instruction_coverage = 40.0
        mock_execution.lines_covered = 225
        mock_execution.lines_total = 500
        mock_execution.branches_covered = 30
        mock_execution.branches_total = 100
        mock_execution.instructions_covered = 400
        mock_execution.instructions_total = 1000
        mock_execution.endpoints_count = 5
        mock_execution.tests_per_endpoint = 0.6
        mock_execution.execution_time = 1.2
        mock_execution.return_code = 0
        
        mock_db_services.test_execution_service.get_test_execution.return_value = mock_execution
        
        response = client.get("/execution-metrics/exec_poor")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["quality_analysis"]["coverage_quality"] == "poor"
        assert data["quality_analysis"]["test_completeness"] == "insufficient"
        assert "Augmenter la couverture de lignes" in data["recommendations"][0]
        assert "Améliorer la couverture des branches" in data["recommendations"][1]

    @patch('gemini.db_services')
    def test_get_detailed_metrics_not_found(self, mock_db_services, client):
        """Test metrics endpoint for non-existent execution."""
        mock_db_services.test_execution_service.get_test_execution.return_value = None
        
        response = client.get("/execution-metrics/nonexistent")
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "Execution not found" in data["error"]