from db.repositories.test_execution_repository import TestExecutionRepository
from db.models.test_execution import TestExecution
from logger import get_logger
from typing import List, Optional, Dict

logger = setup_logger()
logger = get_logger("test_execution_service")


class TestExecutionService:
    def __init__(self):
        self.repository = TestExecutionRepository()

    def create_test_execution(
        self,
        test_generation_id: str,
        build_success: bool,
        tests_run: int,
        error_count: int,
        failure_count: int,
        skipped_count: int,
        success_rate: float,
        execution_time: float,
        line_coverage: float,
        timestamp: float,
        logs: str,
    ) -> TestExecution:
        """Create a new test execution entry"""
        test_execution_obj = TestExecution(
            test_generation_id=test_generation_id,
            build_success=build_success,
            tests_run=tests_run,
            error_count=error_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            success_rate=success_rate,
            execution_time=execution_time,
            line_coverage=line_coverage,
            timestamp=timestamp,
            logs=logs,
        )
        logger.info("Creating new test execution entry")
        return self.repository.create(test_execution_obj)
    
    def get_test_execution(self, id: str) -> Optional[TestExecution]:
        """Get test execution by ID"""
        return self.repository.find_by_id(id)
    
    def get_executions_by_generation_id(self, generation_id: str) -> List[TestExecution]:
        """Get test executions by test generation ID"""
        logger.info(f"Retrieving test executions for generation ID {generation_id}")
        return self.repository.find_by_test_generation_id(generation_id)
