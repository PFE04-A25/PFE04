from db.repositories.base_repository import BaseRepository
from db.models.model_info import ModelInfo

class ModelRepository(BaseRepository[ModelInfo]):
    
    def __init__(self, mongo_uri: str = None):
        super().__init__(ModelInfo, mongo_uri)
        self.model_class = ModelInfo

    def find_by_name(self, name: str):
        """Find model info by model name"""
        filter_dict = {"name": name}
        return self.find_all(filter_dict)
