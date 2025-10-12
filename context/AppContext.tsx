"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { defaultSourceCode } from '@/lib/utils';

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
  };
}

export interface TestExecutionResult {
  execution_id: string;
  status: string;
  timestamp: string;
  metrics?: {
    tests_run?: number;
    success_rate?: number;
    line_coverage?: number;
  };
  quality_analysis?: {
    overall_score?: number;
  };
  logs?: string;
  source_code?: string;
  generated_test?: string;
  test_type?: string;
}

interface AppState {
  // État de la page Générateur
  sourceCode: string;
  outputCode: string;
  selectedTest: string;
  isGenerating: boolean;

  // État de la page Tests (historique)
  testHistory: TestHistoryItem[];

  // État de la page Résultats
  executionResults: TestExecutionResult[];
}

interface AppContextType {
  // État global
  state: AppState;

  // Actions pour la page Générateur
  setSourceCode: (code: string) => void;
  setOutputCode: (code: string) => void;
  setSelectedTest: (test: string) => void;
  setIsGenerating: (isGenerating: boolean) => void;

  // Actions pour la page Tests
  addTestToHistory: (test: TestHistoryItem) => void;
  updateTestInHistory: (id: string, updates: Partial<TestHistoryItem>) => void;
  deleteTestFromHistory: (id: string) => void;
  clearTestHistory: () => void;

  // Actions pour la page Résultats
  addExecutionResult: (result: TestExecutionResult) => void;
  updateExecutionResult: (id: string, updates: Partial<TestExecutionResult>) => void;
  deleteExecutionResult: (id: string) => void;
  clearExecutionResults: () => void;
  getExecutionResultById: (id: string) => TestExecutionResult | undefined;

  // Actions utilitaires
  resetAll: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const initialState: AppState = {
  sourceCode: defaultSourceCode,
  outputCode: '',
  selectedTest: 'restassured',
  isGenerating: false,
  testHistory: [],
  executionResults: [],
};

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState);

  // ========== Actions pour la page Générateur ==========
  const setSourceCode = useCallback((code: string) => {
    setState(prev => ({ ...prev, sourceCode: code }));
  }, []);

  const setOutputCode = useCallback((code: string) => {
    setState(prev => ({ ...prev, outputCode: code }));
  }, []);

  const setSelectedTest = useCallback((test: string) => {
    setState(prev => ({ ...prev, selectedTest: test }));
  }, []);

  const setIsGenerating = useCallback((isGenerating: boolean) => {
    setState(prev => ({ ...prev, isGenerating }));
  }, []);

  // ========== Actions pour la page Tests ==========
  const addTestToHistory = useCallback((test: TestHistoryItem) => {
    setState(prev => ({
      ...prev,
      testHistory: [test, ...prev.testHistory]
    }));
  }, []);

  const updateTestInHistory = useCallback((id: string, updates: Partial<TestHistoryItem>) => {
    setState(prev => ({
      ...prev,
      testHistory: prev.testHistory.map(test =>
        test.id === id ? { ...test, ...updates } : test
      )
    }));
  }, []);

  const deleteTestFromHistory = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      testHistory: prev.testHistory.filter(test => test.id !== id)
    }));
  }, []);

  const clearTestHistory = useCallback(() => {
    setState(prev => ({ ...prev, testHistory: [] }));
  }, []);

  // ========== Actions pour la page Résultats ==========
  const addExecutionResult = useCallback((result: TestExecutionResult) => {
    setState(prev => ({
      ...prev,
      executionResults: [result, ...prev.executionResults]
    }));
  }, []);

  const updateExecutionResult = useCallback((id: string, updates: Partial<TestExecutionResult>) => {
    setState(prev => ({
      ...prev,
      executionResults: prev.executionResults.map(result =>
        result.execution_id === id ? { ...result, ...updates } : result
      )
    }));
  }, []);

  const deleteExecutionResult = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      executionResults: prev.executionResults.filter(result => result.execution_id !== id)
    }));
  }, []);

  const clearExecutionResults = useCallback(() => {
    setState(prev => ({ ...prev, executionResults: [] }));
  }, []);

  const getExecutionResultById = useCallback((id: string) => {
    return state.executionResults.find(result => result.execution_id === id);
  }, [state.executionResults]);

  // ========== Actions utilitaires ==========
  const resetAll = useCallback(() => {
    setState(initialState);
  }, []);

  const value: AppContextType = {
    state,
    setSourceCode,
    setOutputCode,
    setSelectedTest,
    setIsGenerating,
    addTestToHistory,
    updateTestInHistory,
    deleteTestFromHistory,
    clearTestHistory,
    addExecutionResult,
    updateExecutionResult,
    deleteExecutionResult,
    clearExecutionResults,
    getExecutionResultById,
    resetAll,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Hook personnalisé pour utiliser le Context
export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext doit être utilisé dans un AppProvider');
  }
  return context;
}