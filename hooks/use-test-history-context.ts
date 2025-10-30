"use client";

import { useAppContext, TestHistoryItem } from '@/context/AppContext';

/**
 * Hook qui combine le Context avec localStorage pour la compatibilité
 */
export function useTestHistoryContext() {
  const {
    state,
    addTestToHistory: contextAddTest,
    updateTestInHistory,
    deleteTestFromHistory: contextDeleteTest,
    clearTestHistory
  } = useAppContext();

  const { testHistory } = state;

  // Wrapper pour addTestToHistory qui retourne l'ID et sync avec localStorage
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

    // Ajouter au Context
    contextAddTest(newTest);

    // Sync avec localStorage pour compatibilité
    try {
      const updatedHistory = [newTest, ...testHistory];
      localStorage.setItem('test_history', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Erreur sync localStorage:', error);
    }

    return newTest.id;
  };

  // Wrapper pour updateExecutionResults (renommé depuis le Context)
  const updateExecutionResults = (
    testId: string,
    executionResults: TestHistoryItem['executionResults']
  ) => {
    updateTestInHistory(testId, { executionResults });

    // Sync avec localStorage
    try {
      const updatedHistory = testHistory.map(item =>
        item.id === testId ? { ...item, executionResults } : item
      );
      localStorage.setItem('test_history', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Erreur sync localStorage:', error);
    }
  };

  // Wrapper pour deleteTestFromHistory
  const deleteTestFromHistory = (testId: string) => {
    contextDeleteTest(testId);

    // Sync avec localStorage
    try {
      const updatedHistory = testHistory.filter(item => item.id !== testId);
      localStorage.setItem('test_history', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Erreur sync localStorage:', error);
    }
  };

  // Wrapper pour clearHistory
  const clearHistory = () => {
    clearTestHistory();
    localStorage.removeItem('test_history');
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
            // Charger chaque test dans le Context
            imported.forEach(test => contextAddTest(test));

            // Sync localStorage
            localStorage.setItem('test_history', JSON.stringify(imported));
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
    isLoading: false,
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