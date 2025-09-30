import os
from typing import Dict, List, Optional
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
import traceback
from flask import jsonify, Flask, request
from dotenv import load_dotenv
import logging
from datetime import datetime
import sys


# Configure logger
def setup_logger():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Get current date for log filename
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Configure logger
    logger = logging.getLogger('gemini_api')
    logger.setLevel(logging.DEBUG)
    
    # Log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(f'logs/gemini_api_{current_date}.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
logger.info("Flask app initialized.")

# ====================================
# MODÈLES DE DONNÉES
# ====================================

class EndpointInfo(BaseModel):
    """
    Modèle pour stocker les informations sur un endpoint API.

    Attributs:
        path: Chemin de l'endpoint (ex: "/users/{id}")
        method: Méthode HTTP (GET, POST, etc.)
        parameters: Liste des paramètres avec nom et type
        return_type: Type de retour de l'endpoint
        description: Description de la fonction de l'endpoint
    """
    path: str = Field(description="Chemin de l'endpoint")
    method: str = Field(description="Méthode HTTP (GET, POST, etc.)")
    parameters: List[Dict[str, str]] = Field(description="Paramètres de l'endpoint", default_factory=list)
    return_type: str = Field(description="Type de retour de l'endpoint")
    description: str = Field(description="Description de l'endpoint")


class ApiAnalysis(BaseModel):
    """
    Modèle pour stocker l'analyse complète d'un contrôleur API.

    Attributs:
        controller_name: Nom du contrôleur analysé
        base_path: Chemin de base pour tous les endpoints
        endpoints: Liste des endpoints détectés
        model_classes: Classes de modèle utilisées dans l'API
        dependencies: Dépendances Java détectées
        authentication_type: Type d'authentification si détecté
    """
    controller_name: str = Field(description="Nom du contrôleur API")
    base_path: str = Field(description="Chemin de base du contrôleur")
    endpoints: List[EndpointInfo] = Field(description="Liste des endpoints détectés")
    model_classes: List[str] = Field(description="Classes de modèle utilisées", default_factory=list)
    dependencies: List[str] = Field(description="Dépendances Java détectées", default_factory=list)
    authentication_type: Optional[str] = Field(description="Type d'authentification si détecté", default=None)


# ====================================
# CONFIGURATION DES PROMPTS
# ====================================

# Initialisation du parseur pour la sortie structurée
api_parser = PydanticOutputParser(pydantic_object=ApiAnalysis)

# Prompt pour analyser le code API et extraire des informations structurées
api_analysis_prompt = PromptTemplate(
    template="""Tu es un expert en analyse de code Java Spring Boot. Analyse minutieusement le code API suivant et extrait les informations structurées au format spécifié.

Code API:
```java
{api_code}
```

{format_instructions}

Fournir une analyse détaillée et précise.""",
    input_variables=["api_code"],
    partial_variables={"format_instructions": api_parser.get_format_instructions()}
)

# Prompt pour générer des tests RestAssured de base
basic_test_prompt = PromptTemplate(
    template="""En tant qu'ingénieur de test API expérimenté, génère un test RestAssured complet pour l'API Spring Boot suivante. Le test doit suivre les meilleures pratiques et inclure toutes les validations nécessaires.

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
7. Inclure des assertions sur le code de statut, les headers et le corps de la réponse""",
    input_variables=["api_code", "api_info"]
)

# Prompt pour améliorer les tests avec des scénarios avancés
advanced_test_prompt = PromptTemplate(
    template="""En tant qu'expert en tests d'API, améliore le test RestAssured suivant en ajoutant des scénarios de test avancés et des techniques sophistiquées.

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

Ne conserve que le code Java final amélioré, sans explications.""",
    input_variables=["api_code", "basic_test"]
)


# ====================================
# FONCTIONS PRINCIPALES
# ====================================

def setup_llm(api_key=None):
    """
    Configure et retourne l'instance du modèle LLM.

    Arguments:
        api_key: Clé API Google Gemini (facultative, sinon utilise la variable d'environnement)

    Retourne:
        Une instance du modèle Gemini configurée

    Lève:
        ValueError: Si aucune clé API n'est trouvée
    """
    # Utiliser la clé fournie ou rechercher dans les variables d'environnement
    api_key = api_key or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        logger.error("Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement")
        raise ValueError("Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement")

    model = "gemini-2.5-flash"
    logger.info(f"Using Gemini model: {model}")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,  # Valeur basse pour des résultats cohérents
        top_p=0.95,  # Légèrement créatif tout en restant focalisé
        max_tokens=4096  # Longueur maximale pour les réponses complètes
    )


def analyze_api_code(llm, api_code):
    """
    Analyse le code API pour extraire des informations structurées.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java Spring Boot à analyser

    Retourne:
        Dictionnaire contenant les informations structurées sur l'API ou None en cas d'erreur
    """
    try:
        logger.info("Starting API code analysis...")
        # Utiliser l'API du model avec LangChain
        chain = api_analysis_prompt | llm
        logger.info("Prompt chain created.")
        response = chain.invoke({"api_code": api_code})

        # Extraire le JSON de la réponse (peut être encapsulé dans des blocs de code)
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.content)
        if json_match:
            logger.debug("JSON block found in response.")
            json_str = json_match.group(1) # Si un bloc JSON est trouvé, on l'extrait
        else:
            logger.debug("No JSON block found, using full response content.")
            json_str = response.content # Sinon, on prend tout le texte brute

        # Nettoyer et parser le JSON
        api_info = json.loads(json_str)
        logger.info(f"API analysis completed successfully: {api_info['controller_name']} with {len(api_info['endpoints'])} endpoints")
        return api_info
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        logger.debug(f"Response received: {response.content if 'response' in locals() else 'N/A'}")
        logger.exception("Full traceback:")
        return None


def generate_basic_test(llm, api_code, api_info):
    """
    Génère un test RestAssured de base pour l'API.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java de l'API
        api_info: Informations structurées sur l'API

    Retourne:
        Code Java du test RestAssured généré
    """
    logger.info("Generating basic RestAssured test...")
    # Convertir api_info en chaîne formatée pour le prompt
    api_info_str = json.dumps(api_info, indent=2)

    # Génération du test
    chain = basic_test_prompt | llm
    logger.debug("Prompt chain for basic test created.")
    response = chain.invoke({"api_code": api_code, "api_info": api_info_str})
    logger.info(f"Input tokens: {response.usage_metadata['input_tokens']}, "
            f"Max tokens allowed: {llm.max_tokens}")

    # Extraire le code Java de la réponse
    java_match = re.search(r'```(?:java)?\s*([\s\S]*?)\s*```', response.content)
    if java_match:
        logger.debug("Java code block found in response.")
        test_code = java_match.group(1).strip()
        logger.info(f"Basic test generated successfully: {len(test_code)} characters")
        return test_code
    

    # Si pas de bloc de code, retourner tout le texte
    logger.warning("No Java code block found in response, returning raw content")
    logger.debug(f"Response: {response}")
    return response.content.strip()


def enhance_test(llm, api_code, basic_test):
    """
    Améliore le test de base avec des scénarios avancés et des techniques sophistiquées.

    Arguments:
        llm: Instance du modèle de langage
        api_code: Code Java de l'API
        basic_test: Code du test de base généré précédemment

    Retourne:
        Code Java du test RestAssured amélioré
    """
    logger.info("Enhancing test with advanced scenarios")
    
    # Générer le test amélioré
    chain = advanced_test_prompt | llm
    logger.debug("Invoking LLM for test enhancement")
    response = chain.invoke({"api_code": api_code, "basic_test": basic_test})
    logger.info(f"Input tokens: {response.usage_metadata['input_tokens']}, "
            f"Max tokens allowed: {llm.max_tokens}")

    filled_prompt = advanced_test_prompt.format_prompt(api_code=api_code, basic_test=basic_test).text
    logger.debug(f"Enhancement prompt length: {len(filled_prompt)} characters")
    logger.debug(f"Final enhancement prompt:\n{filled_prompt}")

    # Extraire le code Java de la réponse
    java_match = re.search(r'```(?:java)?\s*([\s\S]*?)\s*```', response.content)
    if java_match:
        logger.debug("Java code block found in enhanced test response")
        enhanced_code = java_match.group(1).strip()
        logger.info(f"Test enhanced successfully: {len(enhanced_code)} characters")
        return enhanced_code
    
    # Si pas de bloc de code, retourner tout le texte
    logger.warning("No Java code block found in enhanced test response, returning raw content")
    logger.debug(f"Response: {response}")
    logger.debug(f"Enhanced test preview: {response.content[:500]}{'...' if len(response.content) > 500 else ''}"   )
    return response.content.strip()


@app.route("/rest-assured-test/gemini", methods=["POST"])
def generate_restassured_test():
    """
    Fonction principale pour générer un test RestAssured complet à partir d'un code API Spring Boot.

    Cette fonction enchaîne toutes les étapes:
    1. Analyse du code API
    2. Génération d'un test de base
    3. Amélioration du test avec des scénarios avancés

    Retourne:
        Le code Java du test RestAssured amélioré ou None si une erreur survient
    """
    logger.info("REST API endpoint /rest-assured-test/gemini called")
    
    data = request.get_json()
    logger.debug(f"Request received with content type: {request.content_type}")

    if "api_code" not in data:
        logger.warning("Request missing api_code parameter")
        return jsonify({"error": "Missing api_code parameter"}), 400

    api_code = data["api_code"]
    logger.debug(f"Received API code of length: {len(api_code)} characters")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return jsonify({"error": "Missing GEMINI_API_KEY in environment variables"}), 400

    try:
        # Initialiser le modèle de langage
        logger.info("Setting up LLM...")
        llm = setup_llm(api_key)
        logger.info("LLM setup complete.")

        # Étape 1: Analyser l'API
        logger.info("Step 1: Analyzing API code")
        api_info = analyze_api_code(llm, api_code)
        if not api_info:
            logger.error("API analysis failed!")
            return jsonify({"error": "Failed to analyze API code"}), 500

        logger.info(f"API analysis successful")
        logger.debug(f"API analysis details: {json.dumps(api_info, indent=2)[:500]}")

        # Étape 2: Générer un test de base
        logger.info("Step 2: Generating basic test")
        basic_test = generate_basic_test(llm, api_code, api_info)
        logger.info("Basic test generation successful")
        logger.debug("Basic test:\n" + basic_test)
        
        # Étape 3: Améliorer le test
        skipping_enhancement = True
        # The enhanced test are always empty using basic_test for now
        if not skipping_enhancement:
            logger.info("Step 3: Enhancing test")
            enhanced_test = enhance_test(llm, api_code, basic_test)

            logger.info("Enhanced test generation successful")
            logger.debug("Enhanced test preview: " + (enhanced_test[:500] + "..." if len(enhanced_test) > 500 else enhanced_test))

            logger.info("Test generation completed successfully")
            return jsonify({"generated_test": enhanced_test}) 
        else:
            return jsonify({"generated_test": basic_test})

    except Exception as e:
        logger.error(f"Error occurred while generating test: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True)