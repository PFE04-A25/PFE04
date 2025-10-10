"use client";
import * as React from "react";

import { CodeEditor } from "@/components/code-editor";
import { StartButton } from "@/components/generation-start-button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { sendToDB } from "@/hooks/sendToDB";
import { copyToClipboard } from "@/lib/utils";
import { AlertCircle, CheckCircle, ClipboardList, Clock, Play, XCircle } from "lucide-react";
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
  const [, setIsLoadingSendToDB] = React.useState<boolean>(false);
  
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
                
                <button 
                  onClick={() => {setTestResults(null); setExecutionStatus('idle');}}
                  className="ml-auto text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
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
