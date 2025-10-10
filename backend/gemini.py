import os
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
from flask import jsonify, Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

from logger import setup_logger
from config_class import EndpointInfo, ApiAnalysis
from prompts.rest_prompt import (
    RestAssuredPrompts,
)
import subprocess
import tempfile
import threading
import time
import uuid


# Initialize logger
logger = setup_logger()

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)  # Create Flask application instance
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])  # Enable CORS for Next.js frontend
logger.info("Flask app initialized with CORS.")


def clean_java_code(code):
    """
    Nettoie le code Java des marqueurs markdown et autres artefacts indésirables
    """
    # Supprimer les marqueurs de code markdown qui peuvent apparaître dans le contenu
    code = re.sub(r'^```(?:java)?\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)
    
    # Supprimer les lignes qui ne contiennent que des backticks
    code = re.sub(r'^\s*`+\s*$', '', code, flags=re.MULTILINE)
    
    # Supprimer les espaces en début/fin
    code = code.strip()
    
    # Supprimer les lignes vides multiples
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    
    return code


def fix_spring_boot_test_annotation(code):
    """
    Modifie les annotations @SpringBootTest pour spécifier la classe d'application de test
    """
    # Remplacer @SpringBootTest par @SpringBootTest(classes = TestApplication.class)
    code = re.sub(
        r'@SpringBootTest\s*(\([^)]*\))?',
        '@SpringBootTest(classes = com.test.TestApplication.class, webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)',
        code
    )
    
    return code


def wrap_user_code_in_controller(user_code):
    """
    Analyse le code utilisateur et l'encapsule dans une classe contrôleur si nécessaire
    """
    user_code = user_code.strip()
    
    if not user_code:
        return ""
    
    # Vérifier si c'est déjà une classe complète (contient 'class' et des accolades)
    if 'class ' in user_code and '{' in user_code and '}' in user_code:
        return user_code
    
    # Vérifier si c'est une ou plusieurs méthodes (contient @GetMapping, @PostMapping, etc.)
    if any(annotation in user_code for annotation in ['@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping', '@RequestMapping']):
        # C'est une ou plusieurs méthodes - les encapsuler dans un contrôleur
        # Utiliser une classe package-private (pas public) pour éviter les erreurs de compilation
        controller_code = f"""
@RestController
class ApiController {{
    {user_code}
}}"""
        return controller_code
    
    # Si ce n'est ni une classe ni des méthodes d'API, retourner tel quel
    return user_code


def setup_llm(api_key=None)-> ChatGoogleGenerativeAI:
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
        logger.error(
            "Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement"
        )
        raise ValueError(
            "Clé API Google Gemini non fournie et non trouvée dans les variables d'environnement"
        )

    model = "gemini-2.5-flash"
    logger.info(f"Using Gemini model: {model}")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,  # Valeur basse pour des résultats cohérents
        top_p=0.95,  # Légèrement créatif tout en restant focalisé
        max_tokens=4096,  # Longueur maximale pour les réponses complètes
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
        api_analysis_prompt = RestAssuredPrompts.get_api_analysis_prompt().prompt
        chain = api_analysis_prompt | llm
        logger.info("Prompt chain created.")
        response = chain.invoke({"api_code": api_code})

        # Extraire le JSON de la réponse (peut être encapsulé dans des blocs de code)
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content)
        if json_match:
            logger.debug("JSON block found in response.")
            json_str = json_match.group(1)  # Si un bloc JSON est trouvé, on l'extrait
        else:
            logger.debug("No JSON block found, using full response content.")
            json_str = response.content  # Sinon, on prend tout le texte brute

        # Nettoyer et parser le JSON
        api_info = json.loads(json_str)
        logger.info(
            f"API analysis completed successfully: {api_info['controller_name']} with {len(api_info['endpoints'])} endpoints"
        )
        return api_info
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        logger.debug(
            f"Response received: {response.content if 'response' in locals() else 'N/A'}"
        )
        logger.exception("Full traceback:")
        return None


def generate_basic_test(llm: ChatGoogleGenerativeAI, api_code, api_info):
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
    basic_test_prompt = RestAssuredPrompts.get_basic_test_prompt().prompt
    chain = basic_test_prompt | llm
    logger.debug("Prompt chain for basic test created.")
    response = chain.invoke({"api_code": api_code, "api_info": api_info_str})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Max tokens allowed: {llm.max_output_tokens}"
    )

    # Extraire le code Java de la réponse
    java_match = re.search(r"```(?:java)?\s*([\s\S]*?)\s*```", response.content)
    if java_match:
        logger.debug("Java code block found in response.")
        test_code = java_match.group(1).strip()
    else:
        logger.warning("No Java code block found in response, returning raw content")
        test_code = response.content.strip()
    
    # Nettoyer le code des marqueurs markdown résiduels
    test_code = clean_java_code(test_code)
    
    # Corriger les annotations Spring Boot pour spécifier la classe d'application
    test_code = fix_spring_boot_test_annotation(test_code)
    
    logger.info(f"Basic test generated successfully: {len(test_code)} characters")
    return test_code


def enhance_test(llm: ChatGoogleGenerativeAI, api_code, basic_test):
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
    advanced_test_prompt = RestAssuredPrompts.get_advanced_test_prompt().prompt
    chain = advanced_test_prompt | llm
    logger.debug("Invoking LLM for test enhancement")
    response = chain.invoke({"api_code": api_code, "basic_test": basic_test})
    logger.info(
        f"Input tokens: {response.usage_metadata['input_tokens']}, "
        f"Max tokens allowed: {llm.max_output_tokens}"
    )

    filled_prompt = advanced_test_prompt.format_prompt(
        api_code=api_code, basic_test=basic_test
    ).text
    logger.debug(f"Enhancement prompt length: {len(filled_prompt)} characters")
    logger.debug(f"Final enhancement prompt:\n{filled_prompt}")

    # Extraire le code Java de la réponse
    java_match = re.search(r"```(?:java)?\s*([\s\S]*?)\s*```", response.content)
    if java_match:
        logger.debug("Java code block found in enhanced test response")
        enhanced_code = java_match.group(1).strip()
    else:
        logger.warning("No Java code block found in enhanced test response, returning raw content")
        enhanced_code = response.content.strip()
    
    # Nettoyer le code des marqueurs markdown résiduels
    enhanced_code = clean_java_code(enhanced_code)
    
    # Corriger les annotations Spring Boot pour spécifier la classe d'application
    enhanced_code = fix_spring_boot_test_annotation(enhanced_code)
    
    logger.info(f"Test enhanced successfully: {len(enhanced_code)} characters")
    return enhanced_code


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
        return (
            jsonify({"error": "Missing GEMINI_API_KEY in environment variables"}),
            400,
        )

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
            raise Exception("API analysis failed")

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
            logger.debug(
                "Enhanced test preview: "
                + (
                    enhanced_test[:500] + "..."
                    if len(enhanced_test) > 500
                    else enhanced_test
                )
            )

            logger.info("Test generation completed successfully")
            return jsonify({"generated_test": enhanced_test})
        else:
            return jsonify({"generated_test": basic_test})

    except Exception as e:
        logger.error(f"Error occurred while generating test: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500


# Storage pour les exécutions de test
test_executions = {}

def run_java_tests_async(execution_id, test_code, api_code=""):
    """Exécute les tests Java en arrière-plan et stocke les résultats"""
    try:
        logger.info(f"Starting test execution {execution_id}")
        test_executions[execution_id] = {
            'status': 'running',
            'start_time': time.time(),
            'logs': '',
            'metrics': {}
        }
        
        # Créer un répertoire temporaire pour les tests
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extraire le nom de la classe publique du code généré
            import re
            class_match = re.search(r'class\s+(\w+)', test_code)
            class_name = class_match.group(1) if class_match else "GeneratedTest"
            
            # S'assurer que le nom de la classe se termine par "Test" pour Maven
            if not class_name.endswith('Test'):
                class_name = class_name + 'Test'
            
            # Écrire le code de test dans un fichier avec le bon nom
            test_file = os.path.join(temp_dir, f"{class_name}.java")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            # Créer un pom.xml complet avec toutes les dépendances Spring Boot Test
            pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.test</groupId>
    <artifactId>generated-test</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <spring.boot.version>3.3.5</spring.boot.version>
    </properties>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring.boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <dependencies>
        <!-- Spring Boot Web Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <!-- Spring Boot Test Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- RestAssured for API testing -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>5.4.0</version>
            <scope>test</scope>
        </dependency>
        
        <!-- JaCoCo for code coverage -->
        <dependency>
            <groupId>org.jacoco</groupId>
            <artifactId>jacoco-maven-plugin</artifactId>
            <version>0.8.10</version>
            <scope>test</scope>
        </dependency>
        
        <!-- Exclude conflicting logging -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-logging</artifactId>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <version>${spring.boot.version}</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
                <configuration>
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/*Tests.java</include>
                    </includes>
                    <systemPropertyVariables>
                        <java.awt.headless>true</java.awt.headless>
                    </systemPropertyVariables>
                    <!-- Arguments JVM pour JaCoCo -->
                    <argLine>${jacoco.agent.argLine}</argLine>
                </configuration>
            </plugin>
            
            <!-- Plugin JaCoCo pour la couverture de code -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.10</version>
                <executions>
                    <!-- Préparer l'agent JaCoCo -->
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                        <configuration>
                            <propertyName>jacoco.agent.argLine</propertyName>
                        </configuration>
                    </execution>
                    
                    <!-- Générer le rapport de couverture -->
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                        <configuration>
                            <formats>
                                <format>XML</format>
                                <format>HTML</format>
                            </formats>
                        </configuration>
                    </execution>
                    
                    <!-- Vérifier les seuils de couverture -->
                    <execution>
                        <id>check</id>
                        <goals>
                            <goal>check</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <rule>
                                    <element>BUNDLE</element>
                                    <limits>
                                        <limit>
                                            <counter>LINE</counter>
                                            <value>COVEREDRATIO</value>
                                            <minimum>0.50</minimum>
                                        </limit>
                                        <limit>
                                            <counter>BRANCH</counter>
                                            <value>COVEREDRATIO</value>
                                            <minimum>0.50</minimum>
                                        </limit>
                                    </limits>
                                </rule>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>"""
            
            pom_file = os.path.join(temp_dir, "pom.xml")
            with open(pom_file, 'w', encoding='utf-8') as f:
                f.write(pom_content)
            
            # Créer la structure de répertoires Maven
            src_main_java = os.path.join(temp_dir, "src", "main", "java")
            src_test_java = os.path.join(temp_dir, "src", "test", "java")
            os.makedirs(src_main_java, exist_ok=True)
            os.makedirs(src_test_java, exist_ok=True)
            
            # Créer une application Spring Boot qui inclut le code utilisateur
            if api_code.strip():
                # Analyser et encapsuler correctement le code utilisateur
                user_code_wrapped = wrap_user_code_in_controller(api_code)
                app_content = f"""package com.test;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class TestApplication {{
    public static void main(String[] args) {{
        SpringApplication.run(TestApplication.class, args);
    }}
}}

{user_code_wrapped}
"""
            else:
                # Application Spring Boot minimale par défaut
                app_content = """package com.test;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class TestApplication {
    public static void main(String[] args) {
        SpringApplication.run(TestApplication.class, args);
    }
}

@RestController
class HelloController {
    @GetMapping("/api/hello") 
    public String hello() {
        return "Hello, world!";
    }
}
"""
            
            app_file = os.path.join(src_main_java, "TestApplication.java")
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(app_content)
            
            # Déplacer le fichier de test avec le bon nom
            import shutil
            shutil.move(test_file, os.path.join(src_test_java, f"{class_name}.java"))
            
            # Exécuter les tests avec Maven + JaCoCo pour la couverture
            mvn_path = r'C:\Users\samsd\AppData\Roaming\Code\User\globalStorage\pleiades.java-extension-pack-jdk\maven\latest\bin\mvn.cmd'
            result = subprocess.run(
                [mvn_path, 'clean', 'test', 'jacoco:report'],  # Inclure JaCoCo
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            execution_time = time.time() - test_executions[execution_id]['start_time']
            
            # Parser les résultats
            output = result.stdout + result.stderr
            test_executions[execution_id]['logs'] = output
            
            # Extraire les métriques des logs Maven
            metrics = parse_maven_test_results(output)
            
            # Ajouter les métriques de couverture JaCoCo
            coverage_metrics = parse_jacoco_coverage_report(temp_dir)
            metrics.update(coverage_metrics)
            
            # Compter les endpoints dans le code API
            endpoints_count = count_endpoints_in_api(api_code)
            metrics['endpoints_count'] = endpoints_count
            
            # Calculer le ratio tests/endpoints
            if endpoints_count > 0:
                metrics['tests_per_endpoint'] = metrics['tests_run'] / endpoints_count
            else:
                metrics['tests_per_endpoint'] = 0.0
            
            # Métriques d'exécution
            metrics['execution_time'] = execution_time
            metrics['return_code'] = result.returncode
            
            test_executions[execution_id].update({
                'status': 'completed' if result.returncode == 0 else 'failed',
                'metrics': metrics,
                'end_time': time.time()
            })
            
            logger.info(f"Test execution {execution_id} completed with status: {test_executions[execution_id]['status']}")
            
    except subprocess.TimeoutExpired:
        test_executions[execution_id].update({
            'status': 'timeout',
            'logs': 'Test execution timed out after 5 minutes',
            'metrics': {'error': 'timeout'}
        })
        logger.error(f"Test execution {execution_id} timed out")
        
    except Exception as e:
        test_executions[execution_id].update({
            'status': 'error',
            'logs': f'Error during test execution: {str(e)}',
            'metrics': {'error': str(e)}
        })
        logger.error(f"Test execution {execution_id} failed: {str(e)}")


def count_endpoints_in_api(api_code):
    """
    Analyse le code API pour compter le nombre d'endpoints définis
    """
    if not api_code:
        return 0
    
    # Patterns pour détecter les annotations Spring Web
    endpoint_patterns = [
        r'@GetMapping',
        r'@PostMapping', 
        r'@PutMapping',
        r'@DeleteMapping',
        r'@PatchMapping',
        r'@RequestMapping'
    ]
    
    endpoint_count = 0
    for pattern in endpoint_patterns:
        matches = re.findall(pattern, api_code, re.IGNORECASE)
        endpoint_count += len(matches)
    
    return endpoint_count


def parse_jacoco_coverage_report(temp_dir):
    """
    Parse le rapport de couverture JaCoCo pour extraire les métriques
    """
    coverage_metrics = {
        'line_coverage': 0.0,
        'instruction_coverage': 0.0,
        'branch_coverage': 0.0,
        'lines_covered': 0,
        'lines_total': 0,
        'branches_covered': 0,
        'branches_total': 0,
        'instructions_covered': 0,
        'instructions_total': 0
    }
    
    try:
        # Chemin vers le rapport XML JaCoCo
        jacoco_xml_path = os.path.join(temp_dir, 'target', 'site', 'jacoco', 'jacoco.xml')
        
        if os.path.exists(jacoco_xml_path):
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(jacoco_xml_path)
            root = tree.getroot()
            
            # Parcourir les counters dans le rapport
            for counter in root.findall('.//counter'):
                counter_type = counter.get('type')
                covered = int(counter.get('covered', 0))
                missed = int(counter.get('missed', 0))
                total = covered + missed
                
                if counter_type == 'LINE':
                    coverage_metrics['lines_covered'] = covered
                    coverage_metrics['lines_total'] = total
                    coverage_metrics['line_coverage'] = (covered / total * 100) if total > 0 else 0.0
                    
                elif counter_type == 'BRANCH':
                    coverage_metrics['branches_covered'] = covered
                    coverage_metrics['branches_total'] = total
                    coverage_metrics['branch_coverage'] = (covered / total * 100) if total > 0 else 0.0
                    
                elif counter_type == 'INSTRUCTION':
                    coverage_metrics['instructions_covered'] = covered
                    coverage_metrics['instructions_total'] = total
                    coverage_metrics['instruction_coverage'] = (covered / total * 100) if total > 0 else 0.0
            
            logger.info(f"Coverage report parsed successfully: Line={coverage_metrics['line_coverage']:.1f}%, Branch={coverage_metrics['branch_coverage']:.1f}%")
        
        else:
            logger.warning(f"JaCoCo report not found at {jacoco_xml_path}")
    
    except Exception as e:
        logger.error(f"Error parsing JaCoCo coverage report: {str(e)}")
    
    return coverage_metrics


def parse_maven_test_results(output):
    """Parse Maven test output to extract metrics"""
    metrics = {
        'tests_run': 0,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
        'success_rate': 0.0,
        'build_success': False,
        # Nouvelles métriques de couverture
        'line_coverage': 0.0,
        'instruction_coverage': 0.0,
        'branch_coverage': 0.0,
        'lines_covered': 0,
        'lines_total': 0,
        'branches_covered': 0,
        'branches_total': 0,
        'instructions_covered': 0,
        'instructions_total': 0,
        'endpoints_count': 0,
        'tests_per_endpoint': 0.0
    }
    
    try:
        # Chercher les résultats des tests dans la sortie Maven
        import re
        
        # Pattern pour "Tests run: X, Failures: Y, Errors: Z, Skipped: W"
        test_pattern = r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)'
        matches = re.findall(test_pattern, output)
        
        if matches:
            # Prendre le dernier match (résumé final)
            last_match = matches[-1]
            metrics['tests_run'] = int(last_match[0])
            metrics['failures'] = int(last_match[1])
            metrics['errors'] = int(last_match[2])
            metrics['skipped'] = int(last_match[3])
            
            # Calculer le taux de succès
            if metrics['tests_run'] > 0:
                successful_tests = metrics['tests_run'] - metrics['failures'] - metrics['errors']
                metrics['success_rate'] = (successful_tests / metrics['tests_run']) * 100
        
        # Vérifier si le build a réussi
        metrics['build_success'] = 'BUILD SUCCESS' in output
        
        # Extraire les métriques JaCoCo depuis les logs si disponibles
        try:
            # Pattern pour JaCoCo dans les logs Maven
            jacoco_patterns = {
                'instruction': r'Instructions\s*:\s*(\d+(?:\.\d+)?)%\s*\(\s*(\d+)/(\d+)\s*\)',
                'branch': r'Branches\s*:\s*(\d+(?:\.\d+)?)%\s*\(\s*(\d+)/(\d+)\s*\)',
                'line': r'Lines\s*:\s*(\d+(?:\.\d+)?)%\s*\(\s*(\d+)/(\d+)\s*\)'
            }
            
            for coverage_type, pattern in jacoco_patterns.items():
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    percentage = float(match.group(1))
                    covered = int(match.group(2))
                    total = int(match.group(3))
                    
                    if coverage_type == 'instruction':
                        metrics['instruction_coverage'] = percentage
                        metrics['instructions_covered'] = covered
                        metrics['instructions_total'] = total
                    elif coverage_type == 'branch':
                        metrics['branch_coverage'] = percentage
                        metrics['branches_covered'] = covered
                        metrics['branches_total'] = total
                    elif coverage_type == 'line':
                        metrics['line_coverage'] = percentage
                        metrics['lines_covered'] = covered
                        metrics['lines_total'] = total
        
        except Exception as coverage_error:
            logger.warning(f"Could not parse JaCoCo metrics from logs: {coverage_error}")
        
        # Extraire les erreurs de compilation si présentes
        if 'COMPILATION ERROR' in output:
            metrics['compilation_error'] = True
            
    except Exception as e:
        logger.error(f"Error parsing Maven results: {str(e)}")
        metrics['parse_error'] = str(e)
    
    return metrics


@app.route('/execute-tests', methods=['POST'])
def execute_tests():
    """Endpoint pour exécuter les tests Java et retourner un ID d'exécution"""
    try:
        data = request.get_json()
        test_code = data.get('test_code', '')
        api_code = data.get('api_code', '')
        
        if not test_code.strip():
            return jsonify({'error': 'Test code is required'}), 400
        
        # Générer un ID unique pour cette exécution
        execution_id = str(uuid.uuid4())
        
        # Lancer l'exécution en arrière-plan
        thread = threading.Thread(
            target=run_java_tests_async,
            args=(execution_id, test_code, api_code)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started test execution with ID: {execution_id}")
        return jsonify({
            'execution_id': execution_id,
            'status': 'started',
            'message': 'Test execution started'
        })
        
    except Exception as e:
        logger.error(f"Error starting test execution: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/execution-status/<execution_id>', methods=['GET'])
def get_execution_status(execution_id):
    """Endpoint pour récupérer le statut et les résultats d'une exécution"""
    try:
        if execution_id not in test_executions:
            return jsonify({'error': 'Execution ID not found'}), 404
        
        execution_data = test_executions[execution_id]
        
        return jsonify({
            'execution_id': execution_id,
            'status': execution_data['status'],
            'logs': execution_data['logs'],
            'metrics': execution_data['metrics'],
            'start_time': execution_data.get('start_time'),
            'end_time': execution_data.get('end_time')
        })
        
    except Exception as e:
        logger.error(f"Error retrieving execution status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/execution-metrics/<execution_id>', methods=['GET'])
def get_detailed_metrics(execution_id):
    """Endpoint pour récupérer les métriques détaillées avec analyse de couverture"""
    try:
        if execution_id not in test_executions:
            return jsonify({'error': 'Execution ID not found'}), 404
        
        execution_data = test_executions[execution_id]
        metrics = execution_data.get('metrics', {})
        
        # Analyser les métriques de qualité
        quality_analysis = {
            'coverage_quality': 'poor',  # poor, fair, good, excellent
            'test_completeness': 'insufficient',  # insufficient, minimal, adequate, comprehensive
            'overall_score': 0.0  # 0-100
        }
        
        # Évaluer la qualité de la couverture
        line_coverage = metrics.get('line_coverage', 0)
        branch_coverage = metrics.get('branch_coverage', 0)
        
        if line_coverage >= 90 and branch_coverage >= 85:
            quality_analysis['coverage_quality'] = 'excellent'
        elif line_coverage >= 80 and branch_coverage >= 70:
            quality_analysis['coverage_quality'] = 'good'
        elif line_coverage >= 60 and branch_coverage >= 50:
            quality_analysis['coverage_quality'] = 'fair'
        else:
            quality_analysis['coverage_quality'] = 'poor'
        
        # Évaluer la complétude des tests
        tests_per_endpoint = metrics.get('tests_per_endpoint', 0)
        endpoints_count = metrics.get('endpoints_count', 0)
        
        if tests_per_endpoint >= 3:
            quality_analysis['test_completeness'] = 'comprehensive'
        elif tests_per_endpoint >= 2:
            quality_analysis['test_completeness'] = 'adequate'
        elif tests_per_endpoint >= 1:
            quality_analysis['test_completeness'] = 'minimal'
        else:
            quality_analysis['test_completeness'] = 'insufficient'
        
        # Score global (pondéré)
        coverage_score = (line_coverage * 0.4 + branch_coverage * 0.4 + metrics.get('instruction_coverage', 0) * 0.2)
        test_score = min(100, tests_per_endpoint * 25)  # 25 points par test par endpoint, max 100
        
        quality_analysis['overall_score'] = (coverage_score * 0.7 + test_score * 0.3)
        
        # Recommandations
        recommendations = []
        
        if line_coverage < 70:
            recommendations.append("Augmenter la couverture de lignes (cible: 80%+)")
        if branch_coverage < 60:
            recommendations.append("Améliorer la couverture des branches - tester tous les cas if/else/switch")
        if tests_per_endpoint < 2:
            recommendations.append("Ajouter plus de tests par endpoint (recommandé: 2-3 tests minimum)")
        if endpoints_count > 0 and metrics.get('tests_run', 0) == 0:
            recommendations.append("Aucun test détecté - implémenter des tests pour tous les endpoints")
        
        if not recommendations:
            recommendations.append("Excellente couverture de tests ! Continuer les bonnes pratiques.")
        
        return jsonify({
            'execution_id': execution_id,
            'metrics': metrics,
            'quality_analysis': quality_analysis,
            'recommendations': recommendations,
            'coverage_summary': {
                'line_coverage': f"{line_coverage:.1f}%",
                'branch_coverage': f"{branch_coverage:.1f}%",
                'instruction_coverage': f"{metrics.get('instruction_coverage', 0):.1f}%",
                'tests_per_endpoint': f"{tests_per_endpoint:.1f}",
                'total_endpoints': endpoints_count,
                'total_tests': metrics.get('tests_run', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving detailed metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
