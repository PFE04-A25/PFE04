from add_model_db import init_model_db
from add_pipeline_db import init_pipelines_db


from db.services.model import ModelService
from db.services.pipeline import PipelineService
from db.services.prompt_template import PromptTemplateService

from logger import setup_logger

logger = setup_logger("init_project_db")

def init_project_db():
    """Initialize the project database by adding models and pipelines."""
    logger.info("Initializing project database...")
    init_model_db()
    init_pipelines_db()
    logger.info("Project database initialization complete.")

def clean_up_project_db():
    """Clean up the project database by removing all models and pipelines."""
    logger.info("Cleaning up project database...")
    model_service = ModelService()
    pipeline_service = PipelineService()
    prompt_template_service = PromptTemplateService()
    model_service.purge_models()
    pipeline_service.purge_pipelines()
    prompt_template_service.purge_prompt_templates()
    logger.info("Project database cleanup complete.")

if __name__ == "__main__":
    clean_up_project_db()
    init_project_db()