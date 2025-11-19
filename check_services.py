#!/usr/bin/env python3
"""
Script de vérification des services pour l'évaluation du pipeline
Vérifie que tous les services nécessaires sont accessibles avant de lancer les tests
"""

import requests
import asyncio
import aiohttp
import sys
from datetime import datetime

class ServiceChecker:
    """Vérificateur de l'état des services"""
    
    def __init__(self):
        self.services = {
            "Frontend Next.js": "http://localhost:3000",
            "Backend Flask (Gemini)": "http://localhost:5000",
            "Backend Mistral": "http://127.0.0.1:8000",
            "DeepSeek API (Ollama)": "http://localhost:11434"
        }
        
        self.api_endpoints = {
            "Generation Gemini": "http://localhost:5000/generate-tests",
            "Generation Mistral": "http://127.0.0.1:8000/generate-test",
            "Execution Tests": "http://localhost:5000/execute-tests",
            "Metrics Retrieval": "http://localhost:5000/execution-metrics"
        }
    
    async def check_all_services(self):
        """Vérifie l'état de tous les services"""
        print("🔍 VÉRIFICATION DES SERVICES DU PIPELINE")
        print("=" * 50)
        print(f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        all_ok = True
        
        # Vérifier les services de base
        print("📡 Services de base:")
        for service_name, url in self.services.items():
            status = await self._check_service(url)
            print(f"   • {service_name:25} {status}")
            if "❌" in status:
                all_ok = False
        
        print()
        
        # Vérifier les endpoints API
        print("🔌 Endpoints API:")
        for endpoint_name, url in self.api_endpoints.items():
            status = await self._check_api_endpoint(url)
            print(f"   • {endpoint_name:25} {status}")
            if "❌" in status:
                all_ok = False
        
        print()
        
        # Vérifier les modèles IA
        print("🤖 Modèles IA:")
        await self._check_ai_models()
        
        print()
        
        # Résumé final
        if all_ok:
            print("*** TOUS LES SERVICES SONT OPERATIONNELS! ***")
            print("*** Vous pouvez lancer l'evaluation du pipeline ***")
            print()
            print("Commandes suggérées:")
            print("  python run_pipeline_evaluation.py --quick")
            print("  python comprehensive_test_suite.py --quick")
        else:
            print("*** CERTAINS SERVICES NE SONT PAS ACCESSIBLES ***")
            print("*** Actions suggerees: ***")
            print("  1. Vérifiez que tous vos services sont démarrés")
            print("  2. Consultez les logs d'erreur ci-dessus")
            print("  3. Redémarrez les services défaillants")
        
        return all_ok
    
    async def _check_service(self, url):
        """Vérifie si un service répond"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    if response.status < 500:
                        return "*** OK - Accessible ***"
                    else:
                        return f"*** ATTENTION - Erreur {response.status} ***"
        except aiohttp.ClientConnectorError:
            return "*** NON - Non accessible ***"
        except asyncio.TimeoutError:
            return "*** TIMEOUT - Timeout ***"
        except Exception as e:
            return f"*** ERREUR - Erreur: {str(e)[:30]} ***"
    
    async def _check_api_endpoint(self, url):
        """Vérifie un endpoint API spécifique"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Test avec un payload minimal
                test_payload = {"code": "test", "prompt": "test"}
                async with session.post(url, json=test_payload) as response:
                    if response.status == 200:
                        return "*** OK - Fonctionnel ***"
                    elif response.status in [400, 422]:  # Erreurs de validation attendues
                        return "*** OK - Accessible (validation OK) ***"
                    else:
                        return f"⚠️ Status {response.status}"
        except aiohttp.ClientConnectorError:
            return "*** NON - Non accessible ***"
        except asyncio.TimeoutError:
            return "*** TIMEOUT - Timeout ***"
        except Exception as e:
            return f"*** ERREUR - Erreur: {str(e)[:30]} ***"
    
    async def _check_ai_models(self):
        """Vérifie l'état des modèles IA"""
        models = [
            ("Gemini API", self._check_gemini),
            ("DeepSeek (Ollama)", self._check_deepseek),
            ("Mistral API", self._check_mistral)
        ]
        
        for model_name, check_func in models:
            status = await check_func()
            print(f"   • {model_name:25} {status}")
    
    async def _check_gemini(self):
        """Vérifie Gemini API"""
        try:
            # Test simple sur l'endpoint de génération
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                payload = {
                    "code": "public class Test {}",
                    "prompt": "Generate a simple test"
                }
                async with session.post("http://localhost:5000/generate-tests", json=payload) as response:
                    if response.status == 200:
                        return "✅ API fonctionnelle"
                    else:
                        return f"⚠️ Status {response.status}"
        except Exception as e:
            return f"❌ Non accessible: {str(e)[:30]}"
    
    async def _check_deepseek(self):
        """Vérifie DeepSeek via Ollama"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m.get('name', '') for m in data.get('models', [])]
                        if any('deepseek' in m.lower() for m in models):
                            return "*** OK - Modele disponible ***"
                        else:
                            return "*** ATTENTION - Modele deepseek non trouve ***"
                    else:
                        return f"⚠️ Ollama status {response.status}"
        except Exception as e:
            return f"❌ Ollama non accessible: {str(e)[:30]}"
    
    async def _check_mistral(self):
        """Vérifie Mistral API"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                payload = {"prompt": "test", "code": "test"}
                async with session.post("http://127.0.0.1:8000/generate-test", json=payload) as response:
                    if response.status == 200:
                        return "✅ API fonctionnelle"
                    else:
                        return f"⚠️ Status {response.status}"
        except Exception as e:
            return f"❌ Non accessible: {str(e)[:30]}"
    
    def check_dependencies(self):
        """Vérifie les dépendances Python"""
        print("📦 Vérification des dépendances Python:")
        
        required_packages = [
            'aiohttp', 'requests', 'pandas', 'matplotlib', 
            'seaborn', 'asyncio'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"   * {package:15} *** OK ***")
            except ImportError:
                print(f"   * {package:15} *** MANQUANT ***")
                missing.append(package)
        
        if missing:
            print(f"\n💡 Installez les dépendances manquantes:")
            print(f"   pip install {' '.join(missing)}")
            print(f"   Ou lancez: python setup_tests.py")
            return False
        
        print("   *** Toutes les dependances sont presentes ***")
        return True

async def main():
    """Fonction principale"""
    checker = ServiceChecker()
    
    print("🔧 DIAGNOSTIC DES SERVICES - PIPELINE DE GÉNÉRATION")
    print("=" * 60)
    print()
    
    # Vérifier les dépendances Python
    deps_ok = checker.check_dependencies()
    print()
    
    if not deps_ok:
        print("*** Installez d'abord les dependances manquantes ***")
        sys.exit(1)
    
    # Vérifier les services
    services_ok = await checker.check_all_services()
    
    # Code de sortie
    sys.exit(0 if services_ok else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Vérification interrompue")
        sys.exit(0)
    except Exception as e:
        print(f"\n*** Erreur lors de la verification: {e} ***")
        sys.exit(1)