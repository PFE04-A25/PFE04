"use client";

import { useTestExecutionResults } from '@/hooks/use-test-execution-results';
import { Calendar, Code, Copy, Eye, Play, Search, TestTube, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface TestHistoryItem {
  id: string;
  timestamp: string;
  sourceCode: string;
  generatedTest: string;
  testType: string;
  description?: string;
  executionResults?: {
    execution_id: string;
    status: string;
    success_rate?: number;
    tests_run?: number;
  };
}

export default function TestsPage() {
  const router = useRouter();
  const [testHistory, setTestHistory] = useState<TestHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTestType, setSelectedTestType] = useState('all');
  
  const { fetchAndSaveResult } = useTestExecutionResults();
  
  // Charger l'historique depuis localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('test_history');
    if (savedHistory) {
      try {
        setTestHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Erreur lors du chargement:', error);
      }
    }
  }, []);

  // Filtrer l'historique
  const filteredHistory = testHistory.filter(item => {
    const matchesSearch = !searchTerm || 
      item.sourceCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.generatedTest.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesType = selectedTestType === 'all' || item.testType === selectedTestType;
    
    return matchesSearch && matchesType;
  });

  const handleDeleteItem = (id: string) => {
    const updatedHistory = testHistory.filter(item => item.id !== id);
    setTestHistory(updatedHistory);
    localStorage.setItem('test_history', JSON.stringify(updatedHistory));
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
  };

  const handleExecuteTest = async (item: TestHistoryItem) => {
    try {
      const response = await fetch('http://127.0.0.1:5000/execute-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_code: item.generatedTest,
          api_code: item.sourceCode
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Sauvegarder les informations du test source pour les lier au résultat
        const testInfo = {
          test_history_id: item.id,
          source_code: item.sourceCode,
          generated_test: item.generatedTest,
          test_type: item.testType
        };
        
        // Immédiatement sauvegarder le résultat d'exécution avec les infos du test
        await fetchAndSaveResult(data.execution_id, testInfo);
        
        router.push(`/results?execution_id=${data.execution_id}`);
      } else {
        throw new Error(data.error || 'Failed to start test execution');
      }
    } catch (error) {
      console.error('Error executing test:', error);
      alert('Erreur lors de l\'exécution du test: ' + error);
    }
  };

  const getTestTypeColor = (testType: string) => {
    switch (testType) {
      case 'Unit Tests': return 'bg-blue-100 text-blue-800';
      case 'Integration Tests': return 'bg-green-100 text-green-800';
      case 'API Tests': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-gray-50">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b sticky top-16 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <TestTube className="w-6 h-6 text-blue-500" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Historique des Tests
                </h1>
                <p className="text-sm text-gray-500">
                  {testHistory.length} test{testHistory.length > 1 ? 's' : ''} généré{testHistory.length > 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-16">
        {/* Statistiques rapides */}
        {testHistory.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <TestTube className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Total Tests</p>
                  <p className="text-2xl font-bold text-blue-600">{testHistory.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Play className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Exécutés</p>
                  <p className="text-2xl font-bold text-green-600">
                    {testHistory.filter(item => item.executionResults).length}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Code className="w-8 h-8 text-purple-500 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Types</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {new Set(testHistory.map(item => item.testType)).size}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Calendar className="w-8 h-8 text-orange-500 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Cette semaine</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {testHistory.filter(item => {
                      const itemDate = new Date(item.timestamp);
                      const weekAgo = new Date();
                      weekAgo.setDate(weekAgo.getDate() - 7);
                      return itemDate > weekAgo;
                    }).length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtres et recherche */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Rechercher dans le code source ou les tests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={selectedTestType}
              onChange={(e) => setSelectedTestType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Tous les types</option>
              <option value="Unit Tests">Tests Unitaires</option>
              <option value="Integration Tests">Tests d'Intégration</option>
              <option value="API Tests">Tests API</option>
            </select>
          </div>
        </div>

        {/* Indicateur de nombre de résultats */}
        {filteredHistory.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              {filteredHistory.length} test{filteredHistory.length > 1 ? 's' : ''} trouvé{filteredHistory.length > 1 ? 's' : ''}
              {searchTerm || selectedTestType !== 'all' ? ' (filtré)' : ''}
            </p>
          </div>
        )}

        {/* Liste des tests */}
        {filteredHistory.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
            <TestTube className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {testHistory.length === 0 ? 'Aucun test généré' : 'Aucun résultat trouvé'}
            </h3>
            <p className="text-gray-500 mb-6">
              {testHistory.length === 0 
                ? 'Commencez par générer des tests depuis la page Générateur'
                : 'Essayez de modifier vos critères de recherche'
              }
            </p>
            {testHistory.length === 0 && (
              <button
                onClick={() => router.push('/')}
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Aller au Générateur
              </button>
            )}
          </div>
        ) : (
          <div className="grid gap-6">
            {filteredHistory.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow-sm border overflow-hidden">
                <div className="px-6 py-4 border-b bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">{formatDate(item.timestamp)}</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTestTypeColor(item.testType)}`}>
                      {item.testType}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleExecuteTest(item)}
                      className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Exécuter ce test"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                          <Code className="w-4 h-4 mr-2" />
                          Code Source
                        </h4>
                        <button
                          onClick={() => handleCopyCode(item.sourceCode)}
                          className="p-1 text-gray-500 hover:text-gray-700"
                          title="Copier le code"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-64">
                        <pre className="text-sm whitespace-pre-wrap font-mono">
                          {item.sourceCode.length > 500 
                            ? item.sourceCode.substring(0, 500) + '...' 
                            : item.sourceCode
                          }
                        </pre>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                          <TestTube className="w-4 h-4 mr-2" />
                          Tests Générés
                        </h4>
                        <button
                          onClick={() => handleCopyCode(item.generatedTest)}
                          className="p-1 text-gray-500 hover:text-gray-700"
                          title="Copier le test"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-64">
                        <pre className="text-sm whitespace-pre-wrap font-mono">
                          {item.generatedTest.length > 500 
                            ? item.generatedTest.substring(0, 500) + '...' 
                            : item.generatedTest
                          }
                        </pre>
                      </div>
                    </div>
                  </div>

                  {item.executionResults && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h5 className="text-sm font-semibold text-gray-700 mb-2">Derniers résultats</h5>
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="text-gray-600">
                          Tests: <span className="font-medium">{item.executionResults.tests_run || 0}</span>
                        </span>
                        <span className="text-gray-600">
                          Réussite: <span className="font-medium">{item.executionResults.success_rate?.toFixed(1) || 0}%</span>
                        </span>
                        <button
                          onClick={() => router.push(`/results?execution_id=${item.executionResults!.execution_id}`)}
                          className="text-blue-500 hover:text-blue-700 flex items-center"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Voir détails
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}