from db.models.base_model import BaseModel

class TestExecution(BaseModel):
    collection_name = "test_executions"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_generation_id = kwargs.get('test_generation_id')
        self.build_success = kwargs.get('build_success', False)
        self.tests_run = kwargs.get('tests_run', 0)
        self.error_count = kwargs.get('error_count', 0)
        self.failure_count = kwargs.get('failure_count', 0)
        self.skipped_count = kwargs.get('skipped_count', 0)
        self.success_rate = kwargs.get('success_rate', 0.0)
        self.execution_time = kwargs.get('execution_time', 0.0)
        self.line_coverage = kwargs.get('line_coverage', 0.0)
        self.timestamp = kwargs.get('timestamp', 0.0)
        self.logs = kwargs.get('logs', "")
