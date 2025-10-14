from db.models.base_model import BaseModel

class PromptTemplate(BaseModel):
    collection_name = "prompt_templates"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.template_text = kwargs.get('template_text')  
