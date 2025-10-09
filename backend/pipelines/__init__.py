import re
from logger import get_logger

logger = get_logger()

def cleanup_raw_code_output(output: str, language: str = None) -> tuple[bool, str]:
    """
    This function checks if the output from an LLM is raw code or contains
    additional text or markdown formatting. If it contains extra formatting,
    it will be removed.

    Args:
        output (str): The raw output string from the LLM.
        language (str, optional): The programming language of the code block to clean.
                                  If None, it will attempt to clean any code block.
                                  Defaults to None.
    Returns:
        tuple (bool, str): A tuple where the first element indicates if the cleaned output
                           is valid raw code (True) or not (False), and the second
                           element is the cleaned output string.
    """
    # Check for code block markers
    contains_code_markers = "```" in output
    
    # Clean the output if needed
    if contains_code_markers:
        logger.debug("Code block markers detected, cleaning output.")
        # Extract code from between markers
        if language is not None and language.strip() != "":
            language = language.strip().lower()
            # Handle both newline and space after language spec
            code_pattern = re.compile(r'```(?:{})?[\s\n](.*?)```'.format(language), re.DOTALL)
            matches = code_pattern.findall(output)
            if matches:
                cleaned_output = matches[0]
            else:
                # Remove language tags first
                cleaned_output = re.sub(r'```{}[\s\n]?'.format(language), '', output)
                # Then remove any remaining backticks
                cleaned_output = cleaned_output.replace("```", "")
        else:
            # Try to extract from any language code block
            code_pattern = re.compile(r'```(?:[a-zA-Z]*)?[\s\n](.*?)```', re.DOTALL)
            matches = code_pattern.findall(output)
            if matches:
                cleaned_output = matches[0]
            else:
                # Remove any language tags first
                cleaned_output = re.sub(r'```[a-zA-Z]*[\s\n]?', '', output)
                # Then remove any remaining backticks
                cleaned_output = cleaned_output.replace("```", "")
    else:
        cleaned_output = output

    return (not contains_code_markers, cleaned_output.strip())