from db.models.base_model import BaseModel

class TestCase(BaseModel):
    collection_name = "testcases"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_type = kwargs.get('test_type')
        self.source_code = kwargs.get('source_code')
        self.test_case = kwargs.get('test_case')