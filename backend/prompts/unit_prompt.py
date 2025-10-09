from prompts.basic_prompt import BasePrompt, api_parser

# ====================================
# CONFIGURATION DES PROMPTS
# ====================================


class UnitPrompts:
    """Collection of prompts for generating unit tests"""

    @staticmethod
    def get_code_analysis_prompt() -> BasePrompt:
        """
        This prompt will analyze the source code to:
                - Identify public methods and their signatures
                - Determine input/output types and constraints
                - Detect dependencies and potential mocking needs
                - Identify edge cases and boundary conditions
                - Extract any existing annotations or documentation
        """
        template = """
        You are an expert static code analyzer. Your task is to analyze the following source_code written in Python and extract the critical components necessary for writing comprehensive unit tests.

        ## Analyze the code for the following criteria:
        1. Public Interface: Identify all public methods/functions and their full signatures (name, parameters, return type).
        2. Logic & Constraints: Determine the input constraints (e.g., non-null, size limits) and the expected output behavior (including error handling/exceptions) for each method.
        3. Dependencies & Mocks: List all external or complex internal dependencies (other classes, external services, static calls, etc.) that would require mocking for isolated unit testing.
        4. Edge Cases & Boundaries: Based on the logic, suggest specific edge case categories and boundary conditions to test (e.g., zero, null, max value, empty lists, division by zero).
        5. Existing Documentation: Extract any relevant inline documentation or annotations (e.g., type hints, docstrings) that explain method intent or constraints.

        ## Output format:
        **RESPOND ONLY WITH A SINGLE, VALID CODE JSON OBJECT** DO NOT use markdown code fences (```json) around the object. Adhere to the following structure. Do not include any introductory or concluding text
        {
            "language": "Python",
            "dependencies_to_mock": [ "...", "..." ],
            "methods": [
                {
                "name": "method_name",
                "signature": "full_method_signature",
                "return_type": "...",
                "input_constraints": [ "..." ],
                "expected_exceptions": [ "..." ],
                "suggested_test_categories": [ "Happy Path", "Null Input", "division by zero","Boundary Condition X" ],
                "extracted_docs": "..."
                }
                // ... other methods
            ]
        }

        ## Provided Input:
        - Source Code (in Python):
        ```python
        {source_code}
        ```
        """
        prompt = BasePrompt(
            template=template,
            input_variables=["source_code"],
            partial_variables={
                "format_instructions": api_parser.get_format_instructions()
            },
        )
        return prompt

    @staticmethod
    def get_basic_test_prompt() -> BasePrompt:
        """
        This prompt will create fundamental unit tests:
            - Generate test class structure with proper imports
            - Create test methods for each main function/method
            - Implement basic assertions for expected behavior
            - Include setup and teardown methods if needed
            - Generate simple test data and mocks
        """
        template = """
        You are an expert Python unit test developer. Your task is to generate a basic, runnable unit test class for the provided raw source code, using the provided analysis_data.

        ## Instructions:
        1. Framework: Use the standard testing framework for Python (pytest with pytest-mock).
        2. Structure: Create the full test class structure, including necessary imports (e.g., for assertions, mocks).
        3. Test Methods: Generate at least one passing test for the primary happy path functionality of EACH method listed in the JSON analysis.
        4. Mocks & Setup: Implement basic mocks for all identified dependencies and use **@pytest.fixture** or the `setUp`/`tearDown` methods of `unittest.TestCase` if they simplify test initialization.
        5. Assertions: Include clear and explicit assertions to verify the expected return values and/or state changes (e.g., **assert <condition>** or `self.assertEqual`).
        6. Simplicity: Keep the test data and logic simple. Complex edge cases are reserved for the final enhancement step.
        
        ## Output format:
        **RESPOND ONLY WITH THE RAW UNIT TEST CODE BLOCK**. Ensure the code is complete, correct, and directly runnable.
        
        ## Provided Inputs:
        - Raw Source Code (in Python):
        ```python
        {raw_source_code}
        ```
        - Analysis JSON:
        ```json
        {analysis_json}
        ```
        """
        prompt = BasePrompt(
            template=template,
            input_variables=["raw_source_code", "analysis_json"],
        )
        return prompt

    @staticmethod
    def get_advanced_test_prompt() -> BasePrompt:
        """
        This prompt will enhance the basic tests with:
            - Edge case testing
            - Parameterized tests for comprehensive coverage
            - Advanced mocking techniques
            - Performance considerations
            - Security testing where applicable
            - Test organization improvements (nested tests, display names)
            - More sophisticated assertions
        """

        template = """
        You are a senior-level Quality Assurance Engineer. Your task is to take the provided basic_unit_tests and enhance them significantly based on the analysis_json and the raw_source_code.

        ## Enhancement Requirements:
        1. Edge Case Coverage: Add new test methods or modify existing ones to explicitly test all suggested edge cases and boundary conditions identified in the Analysis JSON (e.g., null inputs, empty collections, max/min values, error paths).
        2. Parameterized/Data-Driven Tests: Convert test cases with repetitive logic into parameterized tests (e.g., **@pytest.mark.parametrize** with clear data lists) where appropriate to ensure comprehensive data coverage.
        3. Implement advanced mocking techniques such as **`MagicMock` configuration, patching internal methods, or verification of specific interaction counts/arguments (e.g., `mock.call_count`, `mock.assert_called_once`).**
        4. Ensure robust testing of expected exceptions and error flows, using constructs like **`pytest.raises`**.
        5. Code Quality: Improve test organization by using features like test display names or nested test classes to group related tests logically.
        
        ## Output Format:
        **RESPOND ONLY WITH THE FINAL, COMPLETE, AND ENHANCED RAW UNIT TEST CODE BLOCK.** Do not include any introductory or concluding text.

        ## Provided Inputs:
        - Raw Source Code (in Python):
        ```python
        {raw_source_code}
        ```
        - Analysis JSON:
        ```json
        {analysis_json}
        ```
        - Basic Unit Tests:
        ```python
        {basic_unit_tests}
        ```
        """
        prompt = BasePrompt(
            template=template,
            input_variables=["raw_source_code", "analysis_json", "basic_unit_tests"],
        )
        return prompt
