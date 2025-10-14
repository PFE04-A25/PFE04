from db.models.base_model import BaseModel

class CodeSnippet(BaseModel):
    collection_name = "code_snippets"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language = kwargs.get('language')          
        self.source_code = kwargs.get('source_code')
        self.hash = kwargs.get('hash')                   
