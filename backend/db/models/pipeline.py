from db.models.base_model import BaseModel

class Pipeline(BaseModel):
    collection_name = "pipelines"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get('name')
        self.version = kwargs.get('version')
        self.description = kwargs.get('description')
        self.language = kwargs.get('language') 
        self.active = kwargs.get('active', False) 

        # Storing a list of prompt template configurations
        self.prompts = kwargs.get('prompts')
        # Structure: [
        #   {
        #     "order": 1,
        #     "prompt_id": <id of the prompt template>,
        #   },
        #   ...
        # ]

        
        
