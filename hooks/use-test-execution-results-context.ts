"use client";

import { useAppContext, TestExecutionResult } from '@/context/AppContext';

const RESULTS_STORAGE_KEY = 'test_execution_results';

export function useTestExecutionResultsContext() {
  const {
    state,
    addExecutionResult,
    updateExecutionResult,
    deleteExecutionResult: contextDeleteResult,
    clearExecutionResults,
    getExecutionResultById
  } = useAppContext();

  const { executionResults } = state;

  // Sauvegarder dans localStorage pour compatibilité
  const saveToStorage = (results: TestExecutionResult[]) => {
    try {
      localStorage.setItem(RESULTS_STORAGE_KEY, JSON.stringify(results));
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  // Ajouter ou mettre à jour un résultat d'exécution
  const addOrUpdateResult = (result: TestExecutionResult) => {
    // Vérifier si existe déjà
    const existing = getExecutionResultById(result.execution_id);

    if (existing) {
      // Mettre à jour
      updateExecutionResult(result.execution_id, result);
    } else {
      // Ajouter nouveau
      addExecutionResult(result);
    }

    // Sync localStorage
    const updatedResults = executionResults.filter(r => r.execution_id !== result.execution_id);
    const newResults = [result, ...updatedResults];
    saveToStorage(newResults);
  };

  // Récupérer un résultat par execution_id
  const getResultById = (executionId: string): TestExecutionResult | null => {
    return getExecutionResultById(executionId) || null;
  };

  // Supprimer un résultat
  const deleteResult = (executionId: string) => {
    contextDeleteResult(executionId);

    // Sync localStorage
    const updatedResults = executionResults.filter(r => r.execution_id !== executionId);
    saveToStorage(updatedResults);
  };

  // Vider tous les résultats
  const clearAllResults = () => {
    clearExecutionResults();
    localStorage.removeItem(RESULTS_STORAGE_KEY);
  };

  // Obtenir les statistiques globales
  const getGlobalStats = () => {
    const totalExecutions = executionResults.length;
    const completedExecutions = executionResults.filter(r => r.status === 'completed').length;
    const failedExecutions = executionResults.filter(r => r.status === 'failed').length;

    const avgSuccessRate = executionResults
      .filter(r => r.metrics?.success_rate !== undefined)
      .reduce((sum, r) => sum + (r.metrics?.success_rate || 0), 0) / completedExecutions || 0;

    const avgCoverage = executionResults
      .filter(r => r.metrics?.line_coverage !== undefined)
      .reduce((sum, r) => sum + (r.metrics?.line_coverage || 0), 0) / completedExecutions || 0;

    return {
      totalExecutions,
      completedExecutions,
      failedExecutions,
      successRate: completedExecutions > 0 ? (completedExecutions / totalExecutions) * 100 : 0,
      avgTestSuccessRate: avgSuccessRate,
      avgCoverage: avgCoverage
    };
  };

  // Rechercher dans les résultats
  const searchResults = (searchTerm: string, statusFilter?: string): TestExecutionResult[] => {
    let filtered = executionResults;

    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter(r => r.status === statusFilter);
    }

    if (searchTerm) {
      const lowerSearchTerm = searchTerm.toLowerCase();
      filtered = filtered.filter(r =>
        r.execution_id.toLowerCase().includes(lowerSearchTerm) ||
        r.logs?.toLowerCase().includes(lowerSearchTerm) ||
        r.source_code?.toLowerCase().includes(lowerSearchTerm) ||
        r.generated_test?.toLowerCase().includes(lowerSearchTerm)
      );
    }

    return filtered;
  };

  // Récupérer et sauvegarder un résultat depuis l'API
  const fetchAndSaveResult = async (
    executionId: string,
    testInfo?: { test_history_id?: string; source_code?: string; generated_test?: string; test_type?: string }
  ): Promise<TestExecutionResult | null> => {
    try {
      // D'abord vérifier si on a déjà ce résultat
      const existingResult = getResultById(executionId);
      if (existingResult) {
        return existingResult;
      }

      // Récupérer depuis l'API
      const response = await fetch(`http://127.0.0.1:5000/execution-status/${executionId}`);
      if (!response.ok) {
        throw new Error("Impossible de récupérer les résultats");
      }

      const basicData = await response.json();

      // Récupérer les métriques détaillées
      let fullResult: TestExecutionResult = {
        ...basicData,
        timestamp: new Date().toISOString(),
        source_code: testInfo?.source_code,
        generated_test: testInfo?.generated_test,
        test_type: testInfo?.test_type
      };

      try {
        const detailedResponse = await fetch(`http://127.0.0.1:5000/execution-metrics/${executionId}`);
        if (detailedResponse.ok) {
          const detailedData = await detailedResponse.json();
          fullResult = {
            ...fullResult,
            ...detailedData
          };
        }
      } catch (detailedError) {
        console.warn('Métriques détaillées non disponibles:', detailedError);
      }

      // Sauvegarder le résultat
      addOrUpdateResult(fullResult);

      return fullResult;

    } catch (error) {
      console.error('Erreur lors de la récupération du résultat:', error);
      return null;
    }
  };

  return {
    executionResults,
    isLoading: false,
    addOrUpdateResult,
    getResultById,
    deleteResult,
    clearAllResults,
    getGlobalStats,
    searchResults,
    fetchAndSaveResult
  };
}