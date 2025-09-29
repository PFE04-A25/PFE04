from tempfile import template
from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from config_class import EndpointInfo, ApiAnalysis
from prompts.basic_prompt import BasePrompt, api_parser

# ====================================
# CONFIGURATION DES PROMPTS
# ====================================


class RestAssuredPrompts:
    """Collection of prompts for generating RestAssured tests"""

    @staticmethod
    def get_api_analysis_prompt() -> BasePrompt:
        """Prompt for analyzing Spring Boot API code"""
        template = """Tu es un expert en analyse de code Java Spring Boot. Analyse minutieusement le code API suivant et extrait les informations structurées au format spécifié.

        Code API:
        ```java
        {api_code}
        ```

        {format_instructions}

        Fournir une analyse détaillée et précise."""
        return BasePrompt(
            template=template,
            input_variables=["api_code"],
            partial_variables={
                "format_instructions": api_parser.get_format_instructions()
            },
        )

    @staticmethod
    def get_basic_test_prompt() -> BasePrompt:
        """Prompt for generating basic RestAssured tests"""
        template = """En tant qu'ingénieur de test API expérimenté, génère un test RestAssured complet pour l'API Spring Boot suivante. Le test doit suivre les meilleures pratiques et inclure toutes les validations nécessaires.

        Informations API:
        {api_info}

        Code API:
        ```java
        {api_code}
        ```

        Génère uniquement le code Java du test, sans explications supplémentaires. Le test doit:
        1. Inclure toutes les importations nécessaires
        2. Utiliser @SpringBootTest avec RANDOM_PORT
        3. Configurer RestAssured correctement
        4. Tester chaque endpoint avec des assertions complètes
        5. Inclure des tests positifs et négatifs
        6. Utiliser @DisplayName et @Nested pour une meilleure organisation
        7. Inclure des assertions sur le code de statut, les headers et le corps de la réponse"""

        return BasePrompt(
            template=template,
            input_variables=["api_code", "basic_test"],
            temperature=0.2,
        )

    @staticmethod
    def get_advanced_test_prompt() -> BasePrompt:
        """Prompt for generating advanced RestAssured tests"""
        template = """En tant qu'expert en tests d'API, améliore le test RestAssured suivant en ajoutant des scénarios de test avancés et des techniques sophistiquées.

        Code API:
        ```java
        {api_code}
        ```

        Test de base:
        ```java
        {basic_test}
        ```

        Améliore ce test en ajoutant:
        1. Tests de limites et cas extrêmes
        2. Tests de performance avec timeouts
        3. Tests de validation de schéma JSON
        4. Mocks pour les dépendances si nécessaire
        5. Tests paramétrés avec @ParameterizedTest
        6. Vérifications de sécurité appropriées
        7. Tests d'erreur avancés avec différents scénarios d'exception
        8. Utilisation de fixtures/data builders pour les données de test
        9. Assertions plus sophistiquées

        Ne conserve que le code Java final amélioré, sans explications."""
        return BasePrompt(
            template=template,
            input_variables=["api_code", "basic_test"],
            temperature=0.2,
        )
