from db.repositories.prompt_template_repository import PromptTemplateRepository
from db.models.prompt_template import PromptTemplate
from logger import get_logger
from typing import List, Optional, Dict

logger = get_logger("prompt_template_service")

class PromptTemplateService:
    def __init__(self):
        self.repository = PromptTemplateRepository()

    def create_prompt_template(self, name: str, description: str, template_text: str, language: str, input_variables: list, partial_variables: dict) -> PromptTemplate:
        """Create a new prompt template"""
        prompt_template_obj = PromptTemplate(
            name=name,
            description=description,
            template_text=template_text,
            language=language,
            input_variables=input_variables,
            partial_variables=partial_variables,
        )
        logger.info(f"Creating new prompt template: {name}")
        return self.repository.create(prompt_template_obj)
    
    def get_prompt_templates(self, filter_dict=None) -> List[PromptTemplate]:
        """Get all prompt templates"""
        return self.repository.find_all(filter_dict)
    
    def get_prompt_template(self, id: str) -> Optional[PromptTemplate]:
        """Get prompt template by ID"""
        return self.repository.find_by_id(id)
    
    def find_templates_by_name(self, name: str) -> List[PromptTemplate]:
        """Find prompt templates by name"""
        return self.repository.find_by_name(name)
    
    def search_templates_by_keyword(self, keyword: str) -> List[PromptTemplate]:
        """Search prompt templates by keyword in template text"""
        return self.repository.search_by_keyword(keyword)
    
    def find_templates_by_language(self, language: str) -> List[PromptTemplate]:
        """Find prompt templates by programming language"""
        return self.repository.find_by_language(language)
    
    def purge_prompt_templates(self) -> bool:
        """Delete all prompt templates from the database"""
        logger.info("Purging all prompt templates from the database")
        all_templates = self.get_prompt_templates()
        deleted_count = 0
        for template in all_templates:
            if self.repository.delete(template.id):
                deleted_count += 1
        logger.info(f"Purged {deleted_count} prompt templates from the database")
        return deleted_count == len(all_templates)