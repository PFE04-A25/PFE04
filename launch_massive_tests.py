#!/usr/bin/env python3
"""
Lanceur rapide pour tests massifs du pipeline IA
"""

import sys
import subprocess
import time

def main():
    print("*** LANCEUR DE TESTS MASSIFS - PIPELINE IA ***")
    print("=" * 50)
    print()
    
    print("Choisissez le type de test:")
    print("1. Mode rapide (30 tests, ~3 minutes)")
    print("2. Mode standard (100 tests, ~15 minutes)")
    print("3. Mode intensif (300 tests, ~45 minutes)")
    print("4. Mode extrême (500 tests, ~75 minutes)")
    print("5. Mode standard (non-massif)")
    print("0. Annuler")
    print()
    
    choice = input("Votre choix (0-5): ").strip()
    
    if choice == "0":
        print("Annulé.")
        return
    
    # Modifier la configuration selon le choix
    if choice == "1":
        tests_per_llm = 10
        print(f"*** Lancement mode rapide: {tests_per_llm * 3} tests ***")
    elif choice == "2":
        tests_per_llm = 100
        print(f"*** Lancement mode standard: {tests_per_llm * 3} tests ***")
    elif choice == "3":
        tests_per_llm = 100
        print(f"*** Lancement mode intensif: {tests_per_llm * 3} tests ***")
    elif choice == "4":
        tests_per_llm = 167  # ~500 tests au total
        print(f"*** Lancement mode extreme: {tests_per_llm * 3} tests ***")
    elif choice == "5":
        print("*** Lancement mode standard (non-massif) ***")
        subprocess.run([sys.executable, "comprehensive_test_suite.py"])
        return
    else:
        print("Choix invalide.")
        return
    
    # Modifier temporairement la configuration dans le fichier
    if choice in ["1", "2", "3", "4"]:
        print(f"*** Duree estimee: {(tests_per_llm * 3 * 30) // 60} a {(tests_per_llm * 3 * 45) // 60} minutes ***")
        print("⚠️ Assurez-vous que vos services sont démarrés!")
        print()
        
        confirm = input("Confirmer le lancement? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Annulé.")
            return
        
        # Modifier la configuration
        config_content = f'''
# Configuration temporaire pour tests massifs
MASSIVE_TEST_CONFIG = {{
    "tests_per_llm": {tests_per_llm},
    "batch_size": 10,
    "delay_between_batches": 2,
    "max_concurrent": 5,
    "timeout_per_test": 30
}}
'''
        
        # Lancer les tests massifs
        start_time = time.time()
        try:
            print("🔄 Lancement des tests massifs...")
            result = subprocess.run([sys.executable, "comprehensive_test_suite.py", "--massive"], 
                                  check=False, capture_output=False)
            
            elapsed = time.time() - start_time
            print(f"\n*** Tests termines en {elapsed//60:.0f}m {elapsed%60:.0f}s ***")
            
            if result.returncode == 0:
                print("✅ Tests réussis! Consultez les résultats:")
                print("   • pipeline_evaluation_results.json")
                print("   • pipeline_tracking.csv")
                print("   • test_results.log")
            else:
                print("❌ Erreur lors des tests")
                
        except KeyboardInterrupt:
            print("\n⏹️ Tests interrompus par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    main()