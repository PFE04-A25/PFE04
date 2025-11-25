from db.models.base_model import BaseModel

class TestGeneration(BaseModel):
    collection_name = "test_generations"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Core relationships
        self.model_id = kwargs.get('model_id')          
        self.pipeline_id = kwargs.get('pipeline_id')
        self.code_snippet_id = kwargs.get('code_snippet_id')
        
        # Generation outputs
        self.generated_analysis = kwargs.get('generated_analysis')
        self.generated_test = kwargs.get('generated_test')
        
        # Generation metadata
        self.token_usage = kwargs.get('token_usage', {})
        self.generation_time = kwargs.get('generation_time')

        # Executed flag
        self.executed = kwargs.get('executed', False)
