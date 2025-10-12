from db.models.base_model import BaseModel


class ModelInfo(BaseModel):
    collection_name = "models"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.provider = kwargs.get('provider')          
        self.name = kwargs.get('name')                   
        self.version = kwargs.get('version')             
        self.temperature = kwargs.get('temperature')    
        self.top_p = kwargs.get('top_p')                 
        self.max_output_tokens = kwargs.get('max_output_tokens')
