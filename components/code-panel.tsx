"use client";
import { useRouter } from 'next/navigation';
import * as React from "react";

import { CodeEditor } from "@/components/code-editor";
import { StartButton } from "@/components/generation-start-button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { sendToDB } from "@/hooks/sendToDB";
import { useTestHistoryContext } from "@/hooks/use-test-history-context";
import { copyToClipboard } from "@/lib/utils";
import { AlertCircle, CheckCircle, ClipboardList, Clock, ExternalLink, History, Play, XCircle } from "lucide-react";
import { useTestExecutionResultsContext } from "@/hooks/use-test-execution-results-context";
interface CodePanelProps {
  sourceCode: string;
  setSourceCode: (sourceCode: string) => void;
  outputCode: string;
  setOutputCode: (outputCode: string) => void;
  isLoading: boolean;
  selectedTest: string;
}

export function CodePanel({
  selectedTest,
  sourceCode,
  setSourceCode,
  outputCode,
  setOutputCode,
  isLoading,
}: CodePanelProps) {
  const router = useRouter();
  const { addTestToHistory, updateExecutionResults } = useTestHistoryContext();
  const { addOrUpdateResult } = useTestExecutionResultsContext();
  const [, setIsLoadingSendToDB] = React.useState<boolean>(false);
  const [currentTestHistoryId, setCurrentTestHistoryId] = React.useState<string | null>(null);
  
  // États pour l'exécution des tests
  const [isExecutingTests, setIsExecutingTests] = React.useState<boolean>(false);
  const [executionId, setExecutionId] = React.useState<string | null>(null);
  const [testResults, setTestResults] = React.useState<any>(null);
  const [executionStatus, setExecutionStatus] = React.useState<string>('idle');
  
  // Polling pour récupérer les résultats
  React.useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (executionId && (executionStatus === 'started' || executionStatus === 'running')) {
      intervalId = setInterval(async () => {
        try {
          const response = await fetch(`http://127.0.0.1:5000/execution-status/${executionId}`);
          const data = await response.json();
          
          setTestResults(data);
          setExecutionStatus(data.status);
          
          // Arrêter le polling si l'exécution est terminée
          if (['completed', 'failed', 'timeout', 'error'].includes(data.status)) {
            setIsExecutingTests(false);
            clearInterval(intervalId);
            
            // Récupérer les métriques détaillées si disponibles
            try {
              const detailedResponse = await fetch(`http://127.0.0.1:5000/execution-metrics/${executionId}`);
              if (detailedResponse.ok) {
                const detailedData = await detailedResponse.json();
                // Fusionner les métriques détaillées avec les données existantes
                setTestResults((prevData: any) => ({
                  ...prevData,
                  ...data,
                  detailed_metrics: detailedData
                }));
                // Sauvegarder dans le Context des résultats
                addOrUpdateResult({
                  execution_id: executionId!,
                  timestamp: new Date().toISOString(),
                  status: data.status,
                  logs: data.logs || '',
                  metrics: detailedData.metrics || data.metrics,
                  quality_analysis: detailedData.quality_analysis,
                  recommendations: detailedData.recommendations,
                  coverage_summary: detailedData.coverage_summary,
                  start_time: data.start_time || new Date().toISOString(),
                  end_time: data.end_time || new Date().toISOString(),
                  source_code: sourceCode,
                  generated_test: outputCode,
                  test_type: selectedTest
                });
              }
            } catch (detailedError) {
              console.log('Métriques détaillées non disponibles:', detailedError);
              // Continuer avec les métriques standard
            }
          }
        } catch (error) {
          console.error('Error polling execution status:', error);
          setIsExecutingTests(false);
          clearInterval(intervalId);
        }
      }, 2000); // Poll toutes les 2 secondes
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [executionId, executionStatus]);

  // Sauvegarder automatiquement dans l'historique quand un nouveau test est généré
  React.useEffect(() => {
    if (outputCode.trim() && sourceCode.trim() && !isLoading) {
      // Vérifier si c'est un nouveau test (pas juste un changement d'état)
      const testId = addTestToHistory(
        sourceCode,
        outputCode,
        selectedTest,
        `Test généré le ${new Date().toLocaleString('fr-FR')}`
      );
      setCurrentTestHistoryId(testId);
    }
  }, [outputCode, sourceCode, selectedTest, isLoading]);

  // Mettre à jour les résultats d'exécution dans l'historique
  React.useEffect(() => {
    if (currentTestHistoryId && testResults && testResults.metrics) {
      updateExecutionResults(currentTestHistoryId, {
        execution_id: executionId || '',
        status: executionStatus,
        success_rate: testResults.metrics.success_rate,
        tests_run: testResults.metrics.tests_run,
        failures: testResults.metrics.failures,
        errors: testResults.metrics.errors
      });
    }
  }, [currentTestHistoryId, testResults, executionStatus, executionId]);
  
  // Fonction pour démarrer l'exécution des tests
  const handleExecuteTests = async () => {
    if (!outputCode.trim()) {
      alert('Aucun code de test à exécuter');
      return;
    }
    
    setIsExecutingTests(true);
    setExecutionStatus('starting');
    setTestResults(null);
    
    try {
      const response = await fetch('http://127.0.0.1:5000/execute-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_code: outputCode,
          api_code: sourceCode
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setExecutionId(data.execution_id);
        setExecutionStatus('started');
      } else {
        throw new Error(data.error || 'Failed to start test execution');
      }
    } catch (error) {
      console.error('Error starting test execution:', error);
      setIsExecutingTests(false);
      setExecutionStatus('error');
      alert('Erreur lors du démarrage des tests: ' + error);
    }
  };

  return (
    <ResizablePanelGroup direction="vertical" className="w-full h-full">
      <ResizablePanel defaultSize={70}>
        <div className="relative w-full h-full">
          <CodeEditor value={sourceCode} setValueAction={setSourceCode} />
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={30} minSize={20}>
        <div className="relative w-full h-full">
          <CodeEditor value={outputCode} setValueAction={setOutputCode} />
          {outputCode ? (
            <div className="z-[100] flex flex-nowrap gap-2 absolute right-[1.5rem] top-[1rem]">
              <div className="button-container">
                <StartButton
                  icon={<ClipboardList size={16} />}
                  action={() => copyToClipboard(outputCode)}
                />
              </div>
              <div className="button-container">
                <StartButton
                  buttonText="Send to DB"
                  className="hover:bg-green-500"
                  isLoading={isLoading}
                  action={() =>
                    sendToDB({
                      testType: selectedTest,
                      prompt: sourceCode,
                      testCaseGenerated: outputCode,
                      setIsLoading: setIsLoadingSendToDB,
                    })
                  }
                />
              </div>
              <div className="button-container">
                <StartButton
                  icon={<History size={16} />}
                  buttonText="Historique"
                  className="hover:bg-purple-500"
                  action={() => router.push('/tests')}
                />
              </div>
              <div className="button-container">
                <StartButton
                  icon={<Play size={16} />}
                  buttonText="Exécuter Tests"
                  className="hover:bg-blue-500"
                  isLoading={isExecutingTests}
                  disabled={!outputCode || isExecutingTests}
                  action={handleExecuteTests}
                />
              </div>
            </div>
          ) : (
            <div className="absolute inset-0 z-20 grid place-items-center bg-muted">
              <div className="flex flex-col items-center gap-3">
                <p className="text-lg font-semibold tracking-tight">Tests 🧪</p>
                {!isLoading ? (
                  <p className="text-sm font-light text-muted-foreground">
                    Your generated test will appear here
                  </p>
                ) : (
                  <p className="text-sm font-light text-green-400">
                    Generating test...
                  </p>
                )}
              </div>
            </div>
          )}
          
          {/* Affichage des résultats de test */}
          {(testResults || isExecutingTests) && (
            <div className="absolute bottom-4 left-4 right-4 bg-white border rounded-lg shadow-lg p-4 max-h-60 overflow-y-auto">
              <div className="flex items-center gap-2 mb-3">
                {executionStatus === 'running' || executionStatus === 'started' ? (
                  <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                ) : executionStatus === 'completed' ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : executionStatus === 'failed' || executionStatus === 'error' ? (
                  <XCircle className="w-4 h-4 text-red-500" />
                ) : executionStatus === 'timeout' ? (
                  <AlertCircle className="w-4 h-4 text-yellow-500" />
                ) : null}
                
                <h3 className="font-semibold">
                  {executionStatus === 'running' || executionStatus === 'started' 
                    ? 'Exécution des tests en cours...' 
                    : 'Résultats des tests'}
                </h3>
                
                <div className="ml-auto flex items-center gap-2">
                  {executionId && ['completed', 'failed'].includes(executionStatus) && (
                    <button 
                      onClick={() => router.push(`/results?execution_id=${executionId}`)}
                      className="flex items-center gap-1 px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Voir détails
                    </button>
                  )}
                  
                  <button 
                    onClick={() => {setTestResults(null); setExecutionStatus('idle');}}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              {testResults?.metrics && (
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-sm font-medium text-blue-700">Tests Exécutés</div>
                    <div className="text-lg font-bold text-blue-900">{testResults.metrics.tests_run || 0}</div>
                  </div>
                  
                  <div className="bg-green-50 p-2 rounded">
                    <div className="text-sm font-medium text-green-700">Taux de Réussite</div>
                    <div className="text-lg font-bold text-green-900">
                      {testResults.metrics.success_rate ? `${testResults.metrics.success_rate.toFixed(1)}%` : '0%'}
                    </div>
                  </div>
                  
                  {testResults.metrics.failures > 0 && (
                    <div className="bg-red-50 p-2 rounded">
                      <div className="text-sm font-medium text-red-700">Échecs</div>
                      <div className="text-lg font-bold text-red-900">{testResults.metrics.failures}</div>
                    </div>
                  )}
                  
                  {testResults.metrics.errors > 0 && (
                    <div className="bg-orange-50 p-2 rounded">
                      <div className="text-sm font-medium text-orange-700">Erreurs</div>
                      <div className="text-lg font-bold text-orange-900">{testResults.metrics.errors}</div>
                    </div>
                  )}
                  
                  {testResults.metrics.execution_time && (
                    <div className="bg-purple-50 p-2 rounded">
                      <div className="text-sm font-medium text-purple-700">Temps d'Exécution</div>
                      <div className="text-lg font-bold text-purple-900">
                        {testResults.metrics.execution_time.toFixed(2)}s
                      </div>
                    </div>
                  )}
                  
                  <div className={`p-2 rounded ${testResults.metrics.build_success ? 'bg-green-50' : 'bg-red-50'}`}>
                    <div className={`text-sm font-medium ${testResults.metrics.build_success ? 'text-green-700' : 'text-red-700'}`}>
                      Build Status
                    </div>
                    <div className={`text-lg font-bold ${testResults.metrics.build_success ? 'text-green-900' : 'text-red-900'}`}>
                      {testResults.metrics.build_success ? 'SUCCESS' : 'FAILED'}
                    </div>
                  </div>
                </div>
              )}

              {/* Nouvelles métriques de couverture */}
              {testResults?.metrics && (testResults.metrics.line_coverage > 0 || testResults.metrics.branch_coverage > 0 || testResults.metrics.instruction_coverage > 0) && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    📊 Métriques de Couverture
                  </h4>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    {testResults.metrics.line_coverage > 0 && (
                      <div className="bg-indigo-50 p-2 rounded">
                        <div className="text-sm font-medium text-indigo-700">Couverture de Lignes</div>
                        <div className="text-lg font-bold text-indigo-900">
                          {testResults.metrics.line_coverage.toFixed(1)}%
                        </div>
                        {testResults.metrics.lines_total > 0 && (
                          <div className="text-xs text-indigo-600">
                            {testResults.metrics.lines_covered}/{testResults.metrics.lines_total}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {testResults.metrics.branch_coverage > 0 && (
                      <div className="bg-cyan-50 p-2 rounded">
                        <div className="text-sm font-medium text-cyan-700">Couverture des Branches</div>
                        <div className="text-lg font-bold text-cyan-900">
                          {testResults.metrics.branch_coverage.toFixed(1)}%
                        </div>
                        {testResults.metrics.branches_total > 0 && (
                          <div className="text-xs text-cyan-600">
                            {testResults.metrics.branches_covered}/{testResults.metrics.branches_total}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {testResults.metrics.instruction_coverage > 0 && (
                      <div className="bg-emerald-50 p-2 rounded">
                        <div className="text-sm font-medium text-emerald-700">Couverture des Instructions</div>
                        <div className="text-lg font-bold text-emerald-900">
                          {testResults.metrics.instruction_coverage.toFixed(1)}%
                        </div>
                        {testResults.metrics.instructions_total > 0 && (
                          <div className="text-xs text-emerald-600">
                            {testResults.metrics.instructions_covered}/{testResults.metrics.instructions_total}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Métriques des endpoints */}
              {testResults?.metrics && (testResults.metrics.endpoints_count > 0 || testResults.metrics.tests_per_endpoint > 0) && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    🎯 Analyse des Endpoints
                  </h4>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    {testResults.metrics.endpoints_count > 0 && (
                      <div className="bg-teal-50 p-2 rounded">
                        <div className="text-sm font-medium text-teal-700">Endpoints Détectés</div>
                        <div className="text-lg font-bold text-teal-900">{testResults.metrics.endpoints_count}</div>
                      </div>
                    )}
                    
                    {testResults.metrics.tests_per_endpoint > 0 && (
                      <div className={`p-2 rounded ${
                        testResults.metrics.tests_per_endpoint >= 2 
                          ? 'bg-green-50' 
                          : testResults.metrics.tests_per_endpoint >= 1 
                          ? 'bg-yellow-50' 
                          : 'bg-red-50'
                      }`}>
                        <div className={`text-sm font-medium ${
                          testResults.metrics.tests_per_endpoint >= 2 
                            ? 'text-green-700' 
                            : testResults.metrics.tests_per_endpoint >= 1 
                            ? 'text-yellow-700' 
                            : 'text-red-700'
                        }`}>
                          Tests par Endpoint
                        </div>
                        <div className={`text-lg font-bold ${
                          testResults.metrics.tests_per_endpoint >= 2 
                            ? 'text-green-900' 
                            : testResults.metrics.tests_per_endpoint >= 1 
                            ? 'text-yellow-900' 
                            : 'text-red-900'
                        }`}>
                          {testResults.metrics.tests_per_endpoint.toFixed(1)}
                        </div>
                        <div className={`text-xs ${
                          testResults.metrics.tests_per_endpoint >= 2 
                            ? 'text-green-600' 
                            : testResults.metrics.tests_per_endpoint >= 1 
                            ? 'text-yellow-600' 
                            : 'text-red-600'
                        }`}>
                          {testResults.metrics.tests_per_endpoint >= 2 
                            ? '✅ Excellent' 
                            : testResults.metrics.tests_per_endpoint >= 1 
                            ? '⚠️ Basique' 
                            : '❌ Insuffisant'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Analyse de qualité détaillée */}
              {testResults?.quality_analysis && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    ⭐ Analyse de Qualité
                  </h4>
                  <div className="grid grid-cols-1 gap-3 mb-3">
                    {/* Score global */}
                    <div className={`p-3 rounded-lg border ${
                      testResults.quality_analysis.overall_score >= 85 
                        ? 'bg-green-50 border-green-200' 
                        : testResults.quality_analysis.overall_score >= 70 
                        ? 'bg-blue-50 border-blue-200' 
                        : testResults.quality_analysis.overall_score >= 50 
                        ? 'bg-yellow-50 border-yellow-200' 
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Score Global</span>
                        <span className={`text-2xl font-bold ${
                          testResults.quality_analysis.overall_score >= 85 
                            ? 'text-green-700' 
                            : testResults.quality_analysis.overall_score >= 70 
                            ? 'text-blue-700' 
                            : testResults.quality_analysis.overall_score >= 50 
                            ? 'text-yellow-700' 
                            : 'text-red-700'
                        }`}>
                          {testResults.quality_analysis.overall_score.toFixed(1)}/100
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="font-medium">Couverture: </span>
                          <span className={`uppercase ${
                            testResults.quality_analysis.coverage_quality === 'excellent' 
                              ? 'text-green-600' 
                              : testResults.quality_analysis.coverage_quality === 'good' 
                              ? 'text-blue-600' 
                              : testResults.quality_analysis.coverage_quality === 'fair' 
                              ? 'text-yellow-600' 
                              : 'text-red-600'
                          }`}>
                            {testResults.quality_analysis.coverage_quality}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Tests: </span>
                          <span className={`uppercase ${
                            testResults.quality_analysis.test_completeness === 'comprehensive' 
                              ? 'text-green-600' 
                              : testResults.quality_analysis.test_completeness === 'adequate' 
                              ? 'text-blue-600' 
                              : testResults.quality_analysis.test_completeness === 'minimal' 
                              ? 'text-yellow-600' 
                              : 'text-red-600'
                          }`}>
                            {testResults.quality_analysis.test_completeness}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Recommandations */}
                    {testResults.recommendations && testResults.recommendations.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h5 className="text-sm font-semibold text-blue-800 mb-2">💡 Recommandations</h5>
                        <ul className="text-xs text-blue-700 space-y-1">
                          {testResults.recommendations.map((rec: string, index: number) => (
                            <li key={index} className="flex items-start">
                              <span className="mr-2">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {testResults?.logs && (
                <details className="mt-3">
                  <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                    Voir les logs d'exécution
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded max-h-40 overflow-auto whitespace-pre-wrap">
                    {testResults.logs}
                  </pre>
                </details>
              )}
              
              {executionStatus === 'error' && (
                <div className="mt-3 text-sm text-red-600">
                  Une erreur est survenue lors de l'exécution des tests.
                </div>
              )}
            </div>
          )}
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}