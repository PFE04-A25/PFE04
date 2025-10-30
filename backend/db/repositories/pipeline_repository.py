from db.repositories.base_repository import BaseRepository
from db.models.pipeline import Pipeline


class PipelineRepository(BaseRepository[Pipeline]):
    def __init__(self, mongo_uri: str = None):
        super().__init__(Pipeline, mongo_uri)

    def find_by_name(self, name: str):
        return self.find_all({"name": name})
    
    def find_by_language(self, language: str):
        return self.find_all({"language": language})
