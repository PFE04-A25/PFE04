"use client";

import { useEffect, useState } from 'react';

export interface TestExecutionResult {
  execution_id: string;
  timestamp: string;
  status: string;
  logs: string;
  metrics: {
    tests_run: number;
    success_rate: number;
    failures: number;
    errors: number;
    execution_time: number;
    build_success: boolean;
    line_coverage: number;
    branch_coverage: number;
    instruction_coverage: number;
    lines_covered: number;
    lines_total: number;
    branches_covered: number;
    branches_total: number;
    instructions_covered: number;
    instructions_total: number;
    endpoints_count: number;
    tests_per_endpoint: number;
  };
  quality_analysis?: {
    overall_score: number;
    coverage_quality: string;
    test_completeness: string;
  };
  recommendations?: string[];
  coverage_summary?: {
    line_coverage: string;
    branch_coverage: string;
    instruction_coverage: string;
    tests_per_endpoint: string;
    total_endpoints: number;
    total_tests: number;
  };
  start_time: string;
  end_time: string;
  // Informations du test source
  test_info?: {
    test_history_id?: string;
    source_code?: string;
    generated_test?: string;
    test_type?: string;
  };
}

const RESULTS_STORAGE_KEY = 'test_execution_results';

export function useTestExecutionResults() {
  const [executionResults, setExecutionResults] = useState<TestExecutionResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Charger les résultats depuis localStorage
  useEffect(() => {
    try {
      const savedResults = localStorage.getItem(RESULTS_STORAGE_KEY);
      if (savedResults) {
        const parsedResults = JSON.parse(savedResults);
        setExecutionResults(parsedResults);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des résultats:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Sauvegarder les résultats dans localStorage
  const saveToStorage = (results: TestExecutionResult[]) => {
    try {
      localStorage.setItem(RESULTS_STORAGE_KEY, JSON.stringify(results));
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  // Ajouter ou mettre à jour un résultat d'exécution
  const addOrUpdateResult = (result: TestExecutionResult) => {
    const updatedResults = executionResults.filter(r => r.execution_id !== result.execution_id);
    const newResults = [result, ...updatedResults];
    setExecutionResults(newResults);
    saveToStorage(newResults);
  };

  // Récupérer un résultat par execution_id
  const getResultById = (executionId: string): TestExecutionResult | null => {
    return executionResults.find(r => r.execution_id === executionId) || null;
  };

  // Supprimer un résultat
  const deleteResult = (executionId: string) => {
    const updatedResults = executionResults.filter(r => r.execution_id !== executionId);
    setExecutionResults(updatedResults);
    saveToStorage(updatedResults);
  };

  // Vider tous les résultats
  const clearAllResults = () => {
    setExecutionResults([]);
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
        r.test_info?.source_code?.toLowerCase().includes(lowerSearchTerm) ||
        r.test_info?.generated_test?.toLowerCase().includes(lowerSearchTerm)
      );
    }

    return filtered;
  };

  // Récupérer et sauvegarder un résultat depuis l'API
  const fetchAndSaveResult = async (executionId: string, testInfo?: TestExecutionResult['test_info']): Promise<TestExecutionResult | null> => {
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
      let fullResult = {
        ...basicData,
        timestamp: new Date().toISOString(),
        test_info: testInfo
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
    isLoading,
    addOrUpdateResult,
    getResultById,
    deleteResult,
    clearAllResults,
    getGlobalStats,
    searchResults,
    fetchAndSaveResult
  };
}