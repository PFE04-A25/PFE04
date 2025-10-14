from db.repositories.base_repository import BaseRepository
from db.models.prompt_template import PromptTemplate


class PromptTemplateRepository(BaseRepository[PromptTemplate]):
    def __init__(self, mongo_uri: str = None):
        super().__init__(PromptTemplate, mongo_uri)

    def find_by_name(self, name: str):
        return self.find_all({"name": name})

    def search_by_keyword(self, keyword: str):
        regex_filter = {"template_text": {"$regex": keyword, "$options": "i"}}
        return self.find_all(regex_filter)
