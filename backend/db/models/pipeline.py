from db.models.base_model import BaseModel

class Pipeline(BaseModel):
    collection_name = "pipelines"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get('name')
        self.version = kwargs.get('version')
        self.description = kwargs.get('description')
        self.language = kwargs.get('language')  

        # Storing a list of prompt template configurations
        self.prompts = kwargs.get('prompts')
        # Structure: [
        #   {
        #     "step_name": "<name of the step>",
        #     "template": "<template prompt text>",
        #     "order": 1,
        #     "input_variables": [<list of input variable names>],
        #   },
        #   ...
        # ]
        
