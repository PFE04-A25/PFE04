"""
Module utilitaire pour la manipulation de code Java sous forme de chaînes de caractères.
"""
import re

def clean_java_code(code: str) -> str:
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

def fix_spring_boot_test_annotation(code: str) -> str:
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

def wrap_user_code_in_controller(user_code: str) -> str:
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


def count_endpoints_in_api(api_code: str) -> int:
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