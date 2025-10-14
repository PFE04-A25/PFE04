from db.repositories.base_repository import BaseRepository
from db.models.prompt_instance import PromptInstance  # ⚠️ le nom du fichier doit être en minuscules

class PromptInstanceRepository(BaseRepository[PromptInstance]):
    def __init__(self, mongo_uri: str = None):
        super().__init__(PromptInstance, mongo_uri)

    def find_by_template(self, template_id: str):
        """Retourne toutes les instances d’un même template"""
        return self.find_all({"template_id": template_id})
