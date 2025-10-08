from db.models.base_model import BaseModel

class TestExecution(BaseModel):
    collection_name = "test_executions"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_generation_id = kwargs.get('test_generation_id')
        self.success_count = kwargs.get('success_count', 0)
        self.failure_count = kwargs.get('failure_count', 0)
        self.execution_time = kwargs.get('execution_time')    
        self.coverage = kwargs.get('coverage')               
        self.logs = kwargs.get('logs', "")
