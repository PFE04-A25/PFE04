from logging import Logger
import uuid
import threading
import time
import tempfile
import subprocess
import os

import execute.spring_boot as spring_boot
import execute.maven as maven

import code_manipulation.java as java_utils

class JavaTestExecutor:

    def __init__(self, logger: Logger,test_code: str, api_code: str):
        self.logger = logger
        self.id = str(uuid.uuid4())
        self.test_executions = {}
        if test_code is None:
            raise ValueError("test_code cannot be None")
        if api_code is None:
            raise ValueError("api_code cannot be None")
        self.test_code = test_code
        self.api_code = api_code

    def __run_java_tests_async(self, execution_id, test_code, api_code=""):
        """Exécute les tests Java en arrière-plan et stocke les résultats"""
        try:
            self.logger.info(f"Starting test execution {execution_id}")
            self.test_executions[execution_id] = {
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
                pom_content = spring_boot.POM_CONTENT_TEMPLATE
                
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
                    user_code_wrapped = java_utils.wrap_user_code_in_controller(api_code)
                    app_content = spring_boot.get_app_content_encapsulated(user_code_wrapped)
                else:
                    # Application Spring Boot minimale par défaut
                    app_content = spring_boot.get_app_content_default()
                
                app_file = os.path.join(src_main_java, "TestApplication.java")
                with open(app_file, 'w', encoding='utf-8') as f:
                    f.write(app_content)
                
                # Déplacer le fichier de test avec le bon nom
                import shutil
                shutil.move(test_file, os.path.join(src_test_java, f"{class_name}.java"))
                
                # Exécuter les tests avec Maven + JaCoCo pour la couverture
                mvn_path = maven.get_maven_path()
                result = subprocess.run(
                    [mvn_path, 'clean', 'test', 'jacoco:report'],  # Inclure JaCoCo
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                execution_time = time.time() - self.test_executions[execution_id]['start_time']
                
                # Parser les résultats
                output = result.stdout + result.stderr
                self.test_executions[execution_id]['logs'] = output

                # Extraire les métriques des logs Maven
                metrics = maven.parse_maven_test_results(output)
                
                # Ajouter les métriques de couverture JaCoCo
                coverage_metrics = maven.parse_jacoco_coverage_report(temp_dir)
                metrics.update(coverage_metrics)
                
                # Compter les endpoints dans le code API
                endpoints_count = java_utils.count_endpoints_in_api(api_code)
                metrics['endpoints_count'] = endpoints_count
                
                # Calculer le ratio tests/endpoints
                if endpoints_count > 0:
                    metrics['tests_per_endpoint'] = metrics['tests_run'] / endpoints_count
                else:
                    metrics['tests_per_endpoint'] = 0.0
                
                # Métriques d'exécution
                metrics['execution_time'] = execution_time
                metrics['return_code'] = result.returncode
                
                self.test_executions[execution_id].update({
                    'status': 'completed' if result.returncode == 0 else 'failed',
                    'metrics': metrics,
                    'end_time': time.time()
                })
                
                self.logger.info(f"Test execution {execution_id} completed with status: {self.test_executions[execution_id]['status']}")
                
        except subprocess.TimeoutExpired:
            self.test_executions[execution_id].update({
                'status': 'timeout',
                'logs': 'Test execution timed out after 5 minutes',
                'metrics': {'error': 'timeout'}
            })
            self.logger.error(f"Test execution {execution_id} timed out")
            
        except Exception as e:
            self.test_executions[execution_id].update({
                'status': 'error',
                'logs': f'Error during test execution: {str(e)}',
                'metrics': {'error': str(e)}
            })
            self.logger.error(f"Test execution {execution_id} failed: {str(e)}")


    def get_thread(self)->threading.Thread:
        """Retourne un thread pour exécuter les tests Java en arrière-plan"""
        thread = threading.Thread(
            target=self.__run_java_tests_async,
            args=(self.id, self.test_code, self.api_code)
        )
        thread.daemon = True
        return thread