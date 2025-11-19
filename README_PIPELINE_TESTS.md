# Évaluation Pipeline IA - Tests RestAssured

Suite de tests pour évaluer vos modèles IA avec support pour **tests massifs (centaines de tests)**.

## Modes d'évaluation

**Installation:**

```bash
python install_deps.py
```

**Tests standards:**

```bash
python check_services.py                    # Vérification services
python comprehensive_test_suite.py          # Mode standard (~30 tests)
python comprehensive_test_suite.py --quick  # Mode rapide (~15 tests)
```

**Tests massifs (intensifs):**

```bash
python comprehensive_test_suite.py --massive  # 300 tests (45+ minutes)
python launch_massive_tests.py               # Interface guidée
python monitor_tests.py                      # Monitoring temps réel
```

## Analyse des tendances

```bash
python analyze_pipeline_trends.py
   ```

## Fichiers générés

- `pipeline_evaluation_results.json` - Résultats détaillés
- `pipeline_tracking.csv` - Historique des performances
- `test_results.log` - Logs d'exécution

## Métriques évaluées

- Qualité du code généré (/100)
- Temps de génération
- Consistance des modèles
- Comparaison Gemini vs DeepSeek vs Mistral

## Tests massifs - Performance LLM

**Configuration MASSIVE_TEST_CONFIG:**

- **Gemini**: 100 tests API variés
- **DeepSeek**: 100 tests avec différents formats
- **Mistral**: 100 tests de complexité variable
- **Total**: 300 tests (durée estimée: 45-75 minutes)

**Fonctionnalités avancées:**

- Traitement par lots (10 tests/batch)
- Contrôle de concurrence (semaphore)
- Monitoring temps réel
- Sauvegarde automatique des résultats
- Gestion d'erreurs et timeouts

**Interface interactive:**

`launch_massive_tests.py` propose 4 niveaux d'intensité:

- **Niveau 1**: 10 tests/LLM (~5 minutes)
- **Niveau 2**: 25 tests/LLM (~12 minutes)
- **Niveau 3**: 50 tests/LLM (~25 minutes)
- **Niveau 4**: 100 tests/LLM (~45-75 minutes)

## Configuration requise

Démarrez vos services (ports 3000, 5000, 8000) avant de lancer les tests.