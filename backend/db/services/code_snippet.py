from db.repositories.code_snippet_repository import CodeSnippetRepository
from db.models.code_snippet import CodeSnippet
from logger import get_logger
from typing import List, Optional, Dict

logger = get_logger("code_snippet_service")

class CodeSnippetService:
    def __init__(self):
        self.repository = CodeSnippetRepository()

    def create_code_snippet(
        self,
        source_code: str,
        language: str,
        description: str
    ) -> CodeSnippet:
        """Create a new code snippet"""
        code_snippet_obj = CodeSnippet(
            source_code=source_code,
            language=language,
            description=description
        )
        logger.info(f"Creating new code snippet")
        return self.repository.create(code_snippet_obj)
