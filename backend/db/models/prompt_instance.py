from db.models.base_model import BaseModel

class PromptInstance(BaseModel):
    collection_name = "prompt_instances"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template_id = kwargs.get('template_id')      # Référence au PromptTemplate
        self.variables = kwargs.get('variables', {})      # Dictionnaire {clé: valeur}
        self.final_prompt = kwargs.get('final_prompt')    # Prompt envoyé réellement au modèle
