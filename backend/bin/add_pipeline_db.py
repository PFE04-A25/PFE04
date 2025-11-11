import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db.services.pipeline import PipelineService
from db.services.prompt_template import PromptTemplateService
from prompts import (
    rest_prompt,
    unit_prompt,
)
from logger import setup_logger

logger = setup_logger("add_pipeline")
   
def add_rest_pipeline(pipeline_service: PipelineService, prompt_template_service: PromptTemplateService):
    """Add JAVA REST pipeline to the database"""
    logger.info("Adding Rest pipeline to database...")
    try:
        #
        # Example to create pipeline with the prompts as a list of FKs with order
        # [
        #   {
        #     "order": 1,
        #     "prompt_id": <id of the prompt template>,
        #   },
        #   ...
        # ]
        # REST
        # Rest prompt
        rest_api_analysis_prompt = (
            rest_prompt.RestAssuredPrompts.get_api_analysis_prompt()
        )
        rest_basic_test_prompt = rest_prompt.RestAssuredPrompts.get_basic_test_prompt()
        rest_advanced_test_prompt = (
            rest_prompt.RestAssuredPrompts.get_advanced_test_prompt()
        )
        rest_api_analysis_prompt_db = prompt_template_service.create_prompt_template(
            name="RestAssured API Analysis Prompt",
            description="Prompt for analyzing Spring Boot API code",
            template_text=rest_api_analysis_prompt._prompt.template,
            input_variables=rest_api_analysis_prompt._prompt.input_variables,
            partial_variables=rest_api_analysis_prompt._prompt.partial_variables,
            language="java",
        )
        rest_basic_test_prompt_db = prompt_template_service.create_prompt_template(
            name="RestAssured Basic Test Prompt",
            description="Prompt for generating basic RestAssured tests",
            template_text=rest_basic_test_prompt._prompt.template,
            input_variables=rest_basic_test_prompt._prompt.input_variables,
            partial_variables=rest_basic_test_prompt._prompt.partial_variables,
            language="java",
        )
        rest_advanced_test_prompt_db = prompt_template_service.create_prompt_template(
            name="RestAssured Advanced Test Prompt",
            description="Prompt for generating advanced RestAssured tests",
            template_text=rest_advanced_test_prompt._prompt.template,
            input_variables=rest_advanced_test_prompt._prompt.input_variables,
            partial_variables=rest_advanced_test_prompt._prompt.partial_variables,
            language="java",
        )
        # Create pipeline with the prompts
        # [
        #   {
        #     "order": 1,
        #     "prompt_id": <id of the prompt template>,
        #   },
        #   ...
        # ]
        pipeline = pipeline_service.create_pipeline(
            name="REST",
            description="Pipeline for generating REST API tests",
            version="1.0",
            prompts=[
                {"order": 1, "prompt_id": rest_api_analysis_prompt_db.id},
                {"order": 2, "prompt_id": rest_basic_test_prompt_db.id},
                {"order": 3, "prompt_id": rest_advanced_test_prompt_db.id},
            ],
            language="java",
            active=True,
        )

        logger.info(f"Successfully added Pipeline with ID: {pipeline.id}")
        logger.info(
            f"Pipeline details: name={pipeline.name}, description={pipeline.description}, version={pipeline.version}"
        )
    except Exception as e:
        logger.error(f"Error adding Gemini pipeline: {str(e)}")
        logger.exception("Full traceback:")
        pipeline = None
    if pipeline:
        print(f"✓ Pipeline added successfully with ID: {pipeline.id}")
    else:
        print("✗ Failed to add pipeline")
    return pipeline

def add_unit_pipeline(pipeline_service: PipelineService, prompt_template_service: PromptTemplateService):
    logger.info("Adding python Unit pipeline to database...")
    try:
        # We need to add the prompts then link them in the pipeline
        #
        # Example to create pipeline with the prompts as a list of FKs with order
        # [
        #   {
        #     "order": 1,
        #     "prompt_id": <id of the prompt template>,
        #   },
        #   ...
        # ]
        unit_prompt_one = unit_prompt.UnitPrompts.get_code_analysis_prompt()
        unit_prompt_two = unit_prompt.UnitPrompts.get_basic_test_prompt()
        unit_prompt_three = unit_prompt.UnitPrompts.get_advanced_test_prompt()
        
        unit_prompt_one_db = prompt_template_service.create_prompt_template(
            name="UNIT",
            description="Prompt for analyzing code",
            template_text=unit_prompt_one._prompt.template,
            input_variables=unit_prompt_one._prompt.input_variables,
            partial_variables=unit_prompt_one._prompt.partial_variables,
            language="python",
        )
        unit_prompt_two_db = prompt_template_service.create_prompt_template(
            name="UNIT",
            description="Prompt for generating basic tests",
            template_text=unit_prompt_two._prompt.template,
            input_variables=unit_prompt_two._prompt.input_variables,
            partial_variables=unit_prompt_two._prompt.partial_variables,
            language="python",
        )
        unit_prompt_three_db = prompt_template_service.create_prompt_template(
            name="UNIT",
            description="Prompt for generating advanced tests",
            template_text=unit_prompt_three._prompt.template,
            input_variables=unit_prompt_three._prompt.input_variables,
            partial_variables=unit_prompt_three._prompt.partial_variables,
            language="python",
        )
        # Create pipeline with the prompts
        # [
        #   {
        #     "order": 1,
        #     "prompt_id": <id of the prompt template>,
        #   },
        #   ...
        # ]
        pipeline = pipeline_service.create_pipeline(
            name="UNIT",
            description="Pipeline for generating unit tests",
            version="1.0",
            prompts=[
                {"order": 1, "prompt_id": unit_prompt_one_db.id},
                {"order": 2, "prompt_id": unit_prompt_two_db.id},
                {"order": 3, "prompt_id": unit_prompt_three_db.id},
            ],
            language="python",
            active=True,
        )

        logger.info(f"Successfully added Pipeline with ID: {pipeline.id}")
        logger.info(
            f"Pipeline details: name={pipeline.name}, description={pipeline.description}, version={pipeline.version}"
        )
    except Exception as e:
        logger.error(f"Error adding Gemini pipeline: {str(e)}")
        logger.exception("Full traceback:")
        pipeline = None
    if pipeline:
        print(f"✓ Pipeline added successfully with ID: {pipeline.id}")
    else:
        print("✗ Failed to add pipeline")
    return pipeline


def init_pipelines_db():
    logger.info("Starting to add pipelines to the database...")
    pipeline_service = PipelineService()
    prompt_template_service = PromptTemplateService()
    rest_pipeline = add_rest_pipeline(pipeline_service, prompt_template_service)
    unit_pipeline = add_unit_pipeline(pipeline_service, prompt_template_service)

    if rest_pipeline is not None and unit_pipeline is not None:
        logger.info("Finished adding pipelines to the database.")
    else:
        logger.error("Failed to add one or more pipelines to the database.") 


if __name__ == "__main__":

    init_pipelines_db()
