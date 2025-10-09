from db.repositories.base_repository import BaseRepository
from db.models.model_info import ModelInfo

class ModelRepository(BaseRepository[ModelInfo]):
    print("✅ model_repository module loaded successfully")
    def __init__(self, mongo_uri: str = None):
        super().__init__(ModelInfo, mongo_uri)
        self.model_class = ModelInfo

