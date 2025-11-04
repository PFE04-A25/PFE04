from db.repositories.pipeline_repository import PipelineRepository
from db.models.pipeline import Pipeline
from logger import setup_logger
from typing import List, Optional, Dict

logger = setup_logger()


class PipelineService:
    def __init__(self):
        self.repository = PipelineRepository()

    def create_pipeline(
        self,
        name: str,
        description: str,
        version: str,
        prompts: List[str],
        language: str
    ) -> Pipeline:
        """Create a new pipeline"""
        pipeline_obj = Pipeline(
            name=name,
            description=description,
            version=version,  
            prompts=prompts,
            language=language
        )
        logger.info(f"Creating new pipeline: {name}")
        return self.repository.create(pipeline_obj)

    def get_pipeline(self, id: str) -> Optional[Pipeline]:
        """Get pipeline by ID"""
        return self.repository.find_by_id(id)

    def get_all_pipelines(self) -> List[Pipeline]:
        """Get all pipelines"""
        logger.info("Retrieving all pipelines")
        return self.repository.find_all()

    def get_pipelines_by_name(self, name: str) -> List[Pipeline]:
        """Get pipelines by name"""
        logger.info(f"Retrieving pipelines with name {name}")
        return self.repository.find_by_name(name)
    
    def get_pipeline_active_by_name(self, name: str) -> List[Pipeline]:
        """Get active pipelines by name"""
        logger.info(f"Retrieving active pipelines with name {name}")
        return self.repository.find_active_by_name(name)
    
    def get_pipeline_version(self,name: str, version: str) -> Optional[Pipeline]:
        """Get pipeline by name and version"""
        logger.info(f"Retrieving pipeline with name {name} and version {version}")
        results = self.repository.find_all({"name": name, "version": version})
        return results[0] if results else None
    
    def get_pipelines_by_language(self, language: str) -> List[Pipeline]:
        """Get pipelines by language"""
        logger.info(f"Retrieving pipelines with language {language}")
        return self.repository.find_by_language(language)