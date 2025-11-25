import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db.services.model import ModelService
from logger import setup_logger

logger = setup_logger("add_model")

def add_gemini_model(model_service: ModelService):
    try:
        # Create model with the same parameters as in setup_llm()
        model = model_service.create_model_info(
            provider="Google",
            name="Gemini",
            version="gemini-2.5-flash",
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=8192
        )
        
        logger.info(f"Successfully added Gemini model with ID: {model.id}")
        logger.info(f"Model details: provider={model.provider}, name={model.name}, version={model.version}")
    except Exception as e:
        logger.error(f"Error adding Gemini model: {str(e)}")
        logger.exception("Full traceback:")
        model = None
    return model

def init_model_db():
    logger.info("Starting to add models to database...")
    model_service = ModelService()
    # We only use Gemini model for now
    model = add_gemini_model(model_service)
    if model is not None:
        print(f"✓ finished adding models")
    else:
        print("✗ Failed to add models")


if __name__ == "__main__":
    logger.info("Adding Gemini model to database...")
    try:
        model_service = ModelService()
        
        # Create model with the same parameters as in setup_llm()
        model = model_service.create_model_info(
            provider="Google",
            name="Gemini",
            version="gemini-2.5-flash",
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=8192
        )
        
        logger.info(f"Successfully added Gemini model with ID: {model.id}")
        logger.info(f"Model details: provider={model.provider}, name={model.name}, version={model.version}")
    except Exception as e:
        logger.error(f"Error adding Gemini model: {str(e)}")
        logger.exception("Full traceback:")
        model = None
    if model:
        print(f"✓ Model added successfully with ID: {model.id}")
    else:
        print("✗ Failed to add model")