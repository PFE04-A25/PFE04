
import re
from logging import Logger
import os

logger = Logger(__name__)

def __get_maven_path(self,):
        """
        Détecte automatiquement le chemin vers Maven sur le système.
        
        Retourne:
            str: Le chemin vers l'exécutable Maven
            
        Lève:
            RuntimeError: Si Maven n'est pas trouvé
        """
        # Vérifier d'abord si un chemin personnalisé est défini dans .env
        custom_maven_path = os.environ.get("MAVEN_PATH")
        if custom_maven_path:
            if os.path.isfile(custom_maven_path) and os.access(custom_maven_path, os.X_OK):
                self.logger.info(f"Maven personnalisé trouvé: {custom_maven_path}")
                return custom_maven_path
            else:
                self.logger.warning(f"Chemin Maven personnalisé invalide: {custom_maven_path}")

        # Liste des emplacements possibles pour Maven
        possible_paths = []
        
        if platform.system() == "Windows":
            # Chemins Windows
            user_home = os.path.expanduser("~")
            possible_paths.extend([
                # Maven dans VS Code Extension
                os.path.join(user_home, "AppData", "Roaming", "Code", "User", "globalStorage", "pleiades.java-extension-pack-jdk", "maven", "latest", "bin", "mvn.cmd"),
                # Maven installation standard Windows
                "C:\\Program Files\\Apache\\maven\\bin\\mvn.cmd",
                "C:\\Program Files (x86)\\Apache\\maven\\bin\\mvn.cmd",
                # Maven dans le PATH
                "mvn.cmd",
                "mvn"
            ])
        else:
            # Chemins Unix/Linux/macOS
            possible_paths.extend([
                "/usr/bin/mvn",
                "/usr/local/bin/mvn",
                "/opt/maven/bin/mvn",
                "mvn"  # Maven dans le PATH
            ])
        
        # Vérifier chaque chemin possible
        for path in possible_paths:
            try:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    self.logger.info(f"Maven trouvé à: {path}")
                    return path
                elif shutil.which(path):  # Vérifie dans le PATH
                    maven_path = shutil.which(path)
                    self.logger.info(f"Maven trouvé dans le PATH: {maven_path}")
                    return maven_path
            except Exception:
                continue
        
        # Si aucun Maven n'est trouvé, lever une erreur avec des instructions
        error_msg = (
            "Maven n'a pas été trouvé sur ce système. Veuillez installer Maven ou l'ajouter au PATH.\n"
            "Installation:\n"
            "- Windows: Téléchargez depuis https://maven.apache.org/download.cgi\n"
            "- Ubuntu/Debian: sudo apt-get install maven\n"
            "- macOS: brew install maven\n"
            "Ou configurez la variable d'environnement MAVEN_HOME"
        )
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)

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

