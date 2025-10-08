from db.models.base_model import BaseModel

class TestGeneration(BaseModel):
    collection_name = "test_generations"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_id = kwargs.get('model_id')          
        self.prompt_instance_id = kwargs.get('prompt_instance_id')
        self.code_snippet_id = kwargs.get('code_snippet_id')
        self.generated_test = kwargs.get('generated_test')
        self.token_usage = kwargs.get('token_usage', {})
        self.generation_time = kwargs.get('generation_time')
