#!/usr/bin/env python3
"""
Analyseur de tendances pour le pipeline de génération de tests IA
Ce script analyse l'évolution des performances de votre pipeline au fil du temps
"""

import json
import csv
from datetime import datetime
from pathlib import Path
import sys

class PipelineTrendAnalyzer:
    """Analyseur de tendances pour le suivi d'amélioration du pipeline"""
    
    def __init__(self):
        self.csv_file = Path("pipeline_tracking.csv")
        self.json_files = list(Path(".").glob("pipeline_evaluation_results*.json"))
        
    def analyze_trends(self):
        """Analyse les tendances d'amélioration"""
        if not self.csv_file.exists():
            print("*** Aucun fichier de suivi trouve. Lancez d'abord comprehensive_test_suite.py ***")
            return
        
        # Charger les données CSV manuellement
        data = []
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        if len(data) < 2:
            print("*** Pas assez de donnees pour analyser les tendances (minimum 2 executions) ***")
            return
        
        print("*** ANALYSE DES TENDANCES DU PIPELINE ***")
        print("=" * 50)
        
        # Analyser l'évolution globale
        self._analyze_overall_trends(data)
        
        # Analyser par LLM
        self._analyze_llm_trends(data)
        
        # Recommandations basées sur les tendances
        self._generate_trend_recommendations(data)
    
    def _analyze_overall_trends(self, data):
        """Analyse les tendances globales"""
        latest = data[-1]
        previous = data[-2] if len(data) > 1 else data[0]
        
        print(f"*** Evolution globale (derniere vs precedente): ***")
        
        # Calculs d'amélioration
        success_change = float(latest['Overall_Success_Rate']) - float(previous['Overall_Success_Rate'])
        quality_change = float(latest['Avg_Quality_Score']) - float(previous['Avg_Quality_Score'])
        speed_change = float(previous['Avg_Generation_Time']) - float(latest['Avg_Generation_Time'])  # Inversé car moins = mieux
        
        print(f"   • Taux de succès: {float(latest['Overall_Success_Rate']):.1f}% ({self._format_change(success_change)})")
        print(f"   • Score qualité: {float(latest['Avg_Quality_Score']):.1f}/100 ({self._format_change(quality_change)})")
        print(f"   • Vitesse génération: {float(latest['Avg_Generation_Time']):.3f}s ({self._format_change(speed_change, 's', inverse=True)})")
        
        # Tendance générale sur toutes les sessions
        if len(data) >= 3:
            first = data[0]
            total_quality_improvement = float(latest['Avg_Quality_Score']) - float(first['Avg_Quality_Score'])
            total_speed_improvement = float(first['Avg_Generation_Time']) - float(latest['Avg_Generation_Time'])
            
            print(f"\n*** Amelioration totale (depuis le debut): ***")
            print(f"   • Qualité: {self._format_change(total_quality_improvement)} points")
            print(f"   • Vitesse: {self._format_change(total_speed_improvement, 's', inverse=True)}")
        
        print()
    
    def _analyze_llm_trends(self, data):
        """Analyse les tendances par LLM"""
        print(f"🤖 Performance par modèle LLM (dernière session):")
        
        latest = data[-1]
        
        llms = [
            ("Gemini", float(latest.get('Gemini_Avg_Quality', 0))),
            ("DeepSeek", float(latest.get('DeepSeek_Avg_Quality', 0))),
            ("Mistral", float(latest.get('Mistral_Avg_Quality', 0)))
        ]
        
        # Trier par performance
        llms.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score) in enumerate(llms):
            rank_emoji = ["#1", "#2", "#3"][i] if i < 3 else "#"
            print(f"   {rank_emoji} {name}: {score:.1f}/100")
            
            # Analyser la tendance si on a des données précédentes
            if len(data) > 1:
                previous_score = float(data[-2].get(f'{name}_Avg_Quality', 0))
                change = score - previous_score
                trend = self._format_change(change)
                print(f"      Évolution: {trend}")
        
        print()
    
    def _generate_simple_summary(self, data):
        """Génère un résumé simple des tendances"""
        print(f"\n*** RESUME DES TENDANCES: ***")
        print("-" * 30)
        
        if len(data) >= 3:
            first = data[0]
            latest = data[-1]
            
            print(f"Session initiale: {first.get('Date', 'N/A')}")
            print(f"Session actuelle: {latest.get('Date', 'N/A')}")
            print(f"Nombre total de sessions: {len(data)}")
            
            # Évolution globale
            quality_evolution = float(latest.get('Avg_Quality_Score', 0)) - float(first.get('Avg_Quality_Score', 0))
            print(f"Évolution qualité globale: {quality_evolution:+.1f} points")
            
            # Meilleur LLM actuel
            llm_scores = {
                'Gemini': float(latest.get('Gemini_Avg_Quality', 0)),
                'DeepSeek': float(latest.get('DeepSeek_Avg_Quality', 0)),
                'Mistral': float(latest.get('Mistral_Avg_Quality', 0))
            }
            best_llm = max(llm_scores, key=llm_scores.get)
            print(f"Meilleur modèle actuel: {best_llm} ({llm_scores[best_llm]:.1f}/100)")
        else:
            print("Pas assez de données pour un résumé complet")
    
    def _generate_trend_recommendations(self, df):
        """Génère des recommandations basées sur les tendances"""
        print(f"*** RECOMMANDATIONS D'AMELIORATION: ***")
        print("-" * 40)
        
        if len(df) < 2:
            print("   • Continuez les tests pour établir des tendances")
            return
        
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        recommendations = []
        
        # Analyser les tendances de qualité
        quality_change = latest['Avg_Quality_Score'] - previous['Avg_Quality_Score']
        if quality_change < -2:
            recommendations.append("🔴 Qualité en baisse - revisitez vos derniers changements de prompts")
        elif quality_change < 1:
            recommendations.append("🟡 Qualité stable - explorez de nouvelles optimisations")
        else:
            recommendations.append("🟢 Qualité en amélioration - continuez sur cette voie")
        
        # Analyser les performances par LLM
        llm_scores = {
            'Gemini': latest['Gemini_Avg_Quality'],
            'DeepSeek': latest['DeepSeek_Avg_Quality'],
            'Mistral': latest['Mistral_Avg_Quality']
        }
        
        best_llm = max(llm_scores, key=llm_scores.get)
        worst_llm = min(llm_scores, key=llm_scores.get)
        
        if llm_scores[worst_llm] < 60:
            recommendations.append(f"🔧 Optimisez prioritairement {worst_llm} (score: {llm_scores[worst_llm]:.1f})")
        
        if llm_scores[best_llm] > 80:
            recommendations.append(f"✨ {best_llm} performe bien - utilisez-le comme référence")
        
        # Analyser la vitesse
        speed_change = previous['Avg_Generation_Time'] - latest['Avg_Generation_Time']
        if speed_change < -0.5:
            recommendations.append("*** Vitesse degradee - verifiez la charge systeme ***")
        
        # Afficher les recommandations
        for rec in recommendations:
            print(f"   • {rec}")
        
        print()
    
    def _format_change(self, change, unit='', inverse=False):
        """Formate l'affichage d'un changement avec couleur"""
        if inverse:
            change = -change  # Inverser pour les métriques où moins = mieux
        
        if abs(change) < 0.01:
            return "stable"
        elif change > 0:
            return f"+{change:.2f}{unit} ⬆️"
        else:
            return f"{change:.2f}{unit} ⬇️"
    
    def generate_progress_report(self):
        """Génère un rapport de progression détaillé"""
        if not self.csv_file.exists():
            print("*** Aucun historique trouve ***")
            return
        
        # Charger les données manuellement
        data = []
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        if len(data) == 0:
            print("*** Aucune donnee disponible ***")
            return
        
        print("*** RAPPORT DE PROGRESSION DU PIPELINE ***")
        print("=" * 50)
        
        # Statistiques globales
        print(f"*** Statistiques globales: ***")
        print(f"   • Nombre de sessions d'évaluation: {len(data)}")
        print(f"   • Période: {data[0]['Date']} → {data[-1]['Date']}")
        print(f"   • Score qualité actuel: {float(data[-1]['Avg_Quality_Score']):.1f}/100")
        print(f"   • Taux de succès actuel: {float(data[-1]['Overall_Success_Rate']):.1f}%")
        print()
        
        # Performance des LLM
        print(f"🤖 Classement des modèles LLM:")
        latest = data[-1]
        llms = [
            ("Gemini", latest['Gemini_Avg_Quality']),
            ("DeepSeek", latest['DeepSeek_Avg_Quality']),
            ("Mistral", latest['Mistral_Avg_Quality'])
        ]
        llms.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score) in enumerate(llms):
            print(f"   {i+1}. {name}: {score:.1f}/100")
        
        print()


def main():
    """Fonction principale"""
    analyzer = PipelineTrendAnalyzer()
    
    print("*** ANALYSEUR DE TENDANCES - PIPELINE DE GENERATION ***")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        analyzer.generate_progress_report()
    else:
        analyzer.analyze_trends()

if __name__ == "__main__":
    main()