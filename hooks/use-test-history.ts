"use client";

import { useEffect, useState } from 'react';

export interface TestHistoryItem {
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
    failures?: number;
    errors?: number;
  };
}

const STORAGE_KEY = 'test_history';

export function useTestHistory() {
  const [testHistory, setTestHistory] = useState<TestHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Charger l'historique depuis localStorage
  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem(STORAGE_KEY);
      if (savedHistory) {
        const parsedHistory = JSON.parse(savedHistory);
        setTestHistory(parsedHistory);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de l\'historique:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Sauvegarder l'historique dans localStorage
  const saveToStorage = (history: TestHistoryItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  // Ajouter un nouveau test à l'historique
  const addTestToHistory = (
    sourceCode: string,
    generatedTest: string,
    testType: string,
    description?: string
  ): string => {
    const newTest: TestHistoryItem = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      sourceCode,
      generatedTest,
      testType,
      description
    };

    const updatedHistory = [newTest, ...testHistory];
    setTestHistory(updatedHistory);
    saveToStorage(updatedHistory);
    
    return newTest.id;
  };

  // Mettre à jour les résultats d'exécution d'un test
  const updateExecutionResults = (
    testId: string,
    executionResults: TestHistoryItem['executionResults']
  ) => {
    const updatedHistory = testHistory.map(item =>
      item.id === testId
        ? { ...item, executionResults }
        : item
    );
    
    setTestHistory(updatedHistory);
    saveToStorage(updatedHistory);
  };

  // Supprimer un test de l'historique
  const deleteTestFromHistory = (testId: string) => {
    const updatedHistory = testHistory.filter(item => item.id !== testId);
    setTestHistory(updatedHistory);
    saveToStorage(updatedHistory);
  };

  // Vider tout l'historique
  const clearHistory = () => {
    setTestHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  // Rechercher dans l'historique
  const searchHistory = (searchTerm: string, testType?: string): TestHistoryItem[] => {
    let filtered = testHistory;

    if (searchTerm) {
      const lowerSearchTerm = searchTerm.toLowerCase();
      filtered = filtered.filter(item =>
        item.sourceCode.toLowerCase().includes(lowerSearchTerm) ||
        item.generatedTest.toLowerCase().includes(lowerSearchTerm) ||
        (item.description && item.description.toLowerCase().includes(lowerSearchTerm))
      );
    }

    if (testType && testType !== 'all') {
      filtered = filtered.filter(item => item.testType === testType);
    }

    return filtered;
  };

  // Obtenir les statistiques de l'historique
  const getHistoryStats = () => {
    const totalTests = testHistory.length;
    const executedTests = testHistory.filter(item => item.executionResults).length;
    const successfulTests = testHistory.filter(item => 
      item.executionResults && item.executionResults.status === 'completed'
    ).length;

    const testTypeDistribution = testHistory.reduce((acc, item) => {
      acc[item.testType] = (acc[item.testType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalTests,
      executedTests,
      successfulTests,
      testTypeDistribution,
      executionRate: totalTests > 0 ? (executedTests / totalTests) * 100 : 0,
      successRate: executedTests > 0 ? (successfulTests / executedTests) * 100 : 0
    };
  };

  // Exporter l'historique
  const exportHistory = () => {
    const dataStr = JSON.stringify(testHistory, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `test-history-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  // Importer l'historique
  const importHistory = (file: File): Promise<boolean> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target?.result as string);
          if (Array.isArray(imported)) {
            setTestHistory(imported);
            saveToStorage(imported);
            resolve(true);
          } else {
            resolve(false);
          }
        } catch (error) {
          console.error('Erreur lors de l\'importation:', error);
          resolve(false);
        }
      };
      reader.readAsText(file);
    });
  };

  return {
    testHistory,
    isLoading,
    addTestToHistory,
    updateExecutionResults,
    deleteTestFromHistory,
    clearHistory,
    searchHistory,
    getHistoryStats,
    exportHistory,
    importHistory
  };
}