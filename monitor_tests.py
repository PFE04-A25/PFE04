#!/usr/bin/env python3
"""
Monitor en temps réel pour les tests massifs
"""

import time
import json
import csv
import os
from datetime import datetime
from pathlib import Path

def monitor_tests():
    """Surveille les tests en cours et affiche les statistiques"""
    
    print("*** MONITORING TESTS MASSIFS EN TEMPS REEL ***")
    print("=" * 50)
    print("Appuyez sur Ctrl+C pour arrêter le monitoring")
    print()
    
    log_file = Path("test_results.log")
    csv_file = Path("pipeline_tracking.csv")
    json_file = Path("pipeline_evaluation_results.json")
    
    last_log_size = 0
    start_time = time.time()
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - start_time
            
            # Vérifier les logs
            if log_file.exists():
                current_size = log_file.stat().st_size
                if current_size != last_log_size:
                    # Nouveaux logs détectés
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        recent_lines = lines[-10:]  # 10 dernières lignes
                        
                        print(f"\r*** [{current_time}] Activite detectee - Logs recents: ***", end="")
                        for line in recent_lines[-3:]:  # 3 dernières lignes
                            if "Progrès:" in line or "Batch" in line or "terminé" in line:
                                clean_line = line.strip().split(" - ")[-1] if " - " in line else line.strip()
                                print(f"\n   📝 {clean_line[:80]}{'...' if len(clean_line) > 80 else ''}")
                    
                    last_log_size = current_size
            
            # Vérifier les résultats JSON pour stats en temps réel
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        
                    total_tests = data.get('total_tests', 0)
                    success_rate = data.get('success_rate', 0)
                    
                    print(f"\n*** Stats actuelles: {total_tests} tests | {success_rate:.1f}% succes | {elapsed//60:.0f}m{elapsed%60:02.0f}s ***")
                    
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Afficher progrès estimé
            print(f"\r🕐 [{current_time}] Monitoring actif - Durée: {elapsed//60:.0f}m{elapsed%60:02.0f}s", end="", flush=True)
            
            time.sleep(5)  # Rafraîchir toutes les 5 secondes
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Monitoring arrêté après {elapsed//60:.0f}m{elapsed%60:02.0f}s")
        
        # Afficher résumé final si disponible
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    final_data = json.load(f)
                
                print("\n📋 RÉSUMÉ FINAL:")
                print(f"   • Tests exécutés: {final_data.get('total_tests', 'N/A')}")
                print(f"   • Taux de succès: {final_data.get('success_rate', 0):.1f}%")
                print(f"   • Score qualité moyen: {final_data.get('avg_quality_score', 0):.1f}/100")
                
                # Top LLM
                llm_scores = final_data.get('llm_scores', {})
                if llm_scores:
                    best_llm = max(llm_scores, key=llm_scores.get)
                    print(f"   • Meilleur LLM: {best_llm} ({llm_scores[best_llm]:.1f}/100)")
                    
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                print("   (Résultats finaux non disponibles)")

def tail_logs():
    """Affiche les logs en temps réel (style tail -f)"""
    
    log_file = Path("test_results.log")
    
    if not log_file.exists():
        print("❌ Fichier de log non trouvé. Démarrez d'abord les tests.")
        return
    
    print("📝 LOGS EN TEMPS RÉEL")
    print("=" * 30)
    print("Appuyez sur Ctrl+C pour arrêter")
    print()
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Aller à la fin du fichier
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    # Filtrer et formatter les lignes importantes
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    if any(keyword in line for keyword in ["Progrès:", "Batch", "terminé", "ERROR", "SUCCESS"]):
                        clean_line = line.strip()
                        print(f"[{timestamp}] {clean_line}")
                else:
                    time.sleep(0.5)
                    
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt du suivi des logs")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--logs":
        tail_logs()
    else:
        monitor_tests()

if __name__ == "__main__":
    main()