#!/usr/bin/env python3
"""
Installation rapide des dépendances pour l'évaluation du pipeline
"""

import subprocess
import sys

def install_dependencies():
    """Installe les dépendances minimales nécessaires"""
    dependencies = [
        "aiohttp>=3.8.0",
        "requests>=2.28.0"
    ]
    
    print("*** Installation des dependances minimales... ***")
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"*** {dep} installe ***")
        except subprocess.CalledProcessError:
            print(f"❌ Erreur installation {dep}")
    
    print("*** Installation terminee! ***")
    print()
    print("*** Utilisation: ***")
    print("1. python comprehensive_test_suite.py")
    print("2. python analyze_pipeline_trends.py")
    print("3. python check_services.py")

if __name__ == "__main__":
    install_dependencies()