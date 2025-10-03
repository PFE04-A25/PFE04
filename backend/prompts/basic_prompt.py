from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from config_class import EndpointInfo, ApiAnalysis

# ====================================
# CONFIGURATION DES PROMPTS
# ====================================

# Initialisation du parseur pour la sortie structurée
api_parser = PydanticOutputParser(pydantic_object=ApiAnalysis)


class BasePrompt:
    """Base class for all prompts with common functionality"""

    def __init__(
        self,
        template: str,
        input_variables: List[str],
        partial_variables: dict = None,
        temperature: float = 0.2,
    ):
        self.template = template
        self.input_variables = input_variables
        self.partial_variables = partial_variables or {}
        self.temperature = temperature
        self._prompt = PromptTemplate(
            template=self.template, input_variables=self.input_variables, partial_variables=self.partial_variables
        )

    @property
    def prompt(self) -> PromptTemplate:
        """Return the LangChain PromptTemplate object"""
        return self._prompt
    
    def format(self, **kwargs):
        """Format the prompt template with the given variables"""
        # Use LangChain's formatting which already handles partial_variables
        return self._prompt.format(**kwargs)

    def get_chain(self, llm):
        """Create a prompt chain with the given LLM"""
        return self._prompt | llm

    def format_prompt(self, **kwargs) -> str:
        """Format the prompt with the given variables"""
        return self._prompt.format_prompt(**kwargs).text

    def estimate_tokens(self, **kwargs) -> int:
        """Estimate the number of tokens in the formatted prompt"""
        formatted = self.format_prompt(**kwargs)
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(formatted) // 4
