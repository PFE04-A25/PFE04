from db.repositories.model_repository import ModelRepository
from db.models.model_info import ModelInfo
from logger import setup_logger
from typing import List, Optional, Dict

logger = setup_logger()


class ModelService:
    def __init__(self):
        self.repository = ModelRepository()

    def create_model_info(
        self,
        provider: str,
        name: str,
        version: str,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
    ) -> ModelInfo:
        """Create a new model info entry"""
        model_info_obj = ModelInfo(
            provider=provider,
            name=name,
            version=version,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
        )

        logger.info(f"Creating new model info for model {name} by {provider}")
        return self.repository.create(model_info_obj)

    def get_model(self, id: str) -> Optional[ModelInfo]:
        """Get model info by ID"""
        return self.repository.find_by_id(id)

    def get_all_models(self) -> List[ModelInfo]:
        """Get all models"""
        logger.info("Retrieving all models")
        return self.repository.find_all()

    def get_models_by_name(self, name: str) -> List[ModelInfo]:
        """Get models by name"""
        logger.info(f"Retrieving models with name {name}")
        return self.repository.find_by_name(name)
    
    def purge_models(self) -> bool:
        """Delete all models from the database"""
        logger.info("Purging all models from the database")
        all_models = self.get_all_models()
        deleted_count = 0
        for model in all_models:
            if self.repository.delete(model.id):
                deleted_count += 1
        logger.info(f"Deleted {deleted_count} models from the database")
        return deleted_count == len(all_models)
