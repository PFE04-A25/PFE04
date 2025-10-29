"use client";

import { Activity, AlertTriangle, CheckCircle, Target, TrendingUp, XCircle } from 'lucide-react';
import { CoverageCharts } from './coverage-charts';

interface TestResultsDisplayProps {
  testResults: {
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
    logs?: string;
  };
}

export function TestResultsDisplay({ testResults }: TestResultsDisplayProps) {
  const { metrics } = testResults;

  const getCoverageColor = (coverage: number) => {
    if (coverage >= 90) return 'text-green-600';
    if (coverage >= 80) return 'text-blue-600';
    if (coverage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCoverageBgColor = (coverage: number) => {
    if (coverage >= 90) return 'bg-green-50 border-green-200';
    if (coverage >= 80) return 'bg-blue-50 border-blue-200';
    if (coverage >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="space-y-8">
      {/* Section des erreurs et échecs */}
      {(metrics.failures > 0 || metrics.errors > 0) && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
            Erreurs et Échecs
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {metrics.failures > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-red-800">Tests Échoués</h3>
                    <p className="text-3xl font-bold text-red-900">{metrics.failures}</p>
                  </div>
                  <XCircle className="w-8 h-8 text-red-500" />
                </div>
                <p className="text-sm text-red-700 mt-2">
                  Tests qui ont échoué lors de l'assertion
                </p>
              </div>
            )}
            
            {metrics.errors > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-orange-800">Erreurs d'Exécution</h3>
                    <p className="text-3xl font-bold text-orange-900">{metrics.errors}</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-orange-500" />
                </div>
                <p className="text-sm text-orange-700 mt-2">
                  Erreurs d'exécution ou de compilation
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Graphiques de couverture */}
      {(metrics.line_coverage > 0 || metrics.branch_coverage > 0 || metrics.instruction_coverage > 0) && (
        <CoverageCharts metrics={metrics} />
      )}

      {/* Métriques de couverture détaillées */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <Activity className="w-5 h-5 text-blue-500 mr-2" />
          Couverture de Code (JaCoCo)
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Couverture de lignes */}
          {metrics.line_coverage > 0 && (
            <div className={`border rounded-lg p-6 ${getCoverageBgColor(metrics.line_coverage)}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-700">Couverture de Lignes</h3>
                  <p className={`text-4xl font-bold ${getCoverageColor(metrics.line_coverage)}`}>
                    {metrics.line_coverage.toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className={`w-8 h-8 ${getCoverageColor(metrics.line_coverage)}`} />
              </div>
              
              {metrics.lines_total > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Lignes couvertes:</span>
                    <span className="font-medium">{metrics.lines_covered}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Total de lignes:</span>
                    <span className="font-medium">{metrics.lines_total}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div 
                      className={`h-2 rounded-full ${metrics.line_coverage >= 80 ? 'bg-green-500' : metrics.line_coverage >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${metrics.line_coverage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Couverture des branches */}
          {metrics.branch_coverage > 0 && (
            <div className={`border rounded-lg p-6 ${getCoverageBgColor(metrics.branch_coverage)}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-700">Couverture des Branches</h3>
                  <p className={`text-4xl font-bold ${getCoverageColor(metrics.branch_coverage)}`}>
                    {metrics.branch_coverage.toFixed(1)}%
                  </p>
                </div>
                <Target className={`w-8 h-8 ${getCoverageColor(metrics.branch_coverage)}`} />
              </div>
              
              {metrics.branches_total > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Branches couvertes:</span>
                    <span className="font-medium">{metrics.branches_covered}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Total branches:</span>
                    <span className="font-medium">{metrics.branches_total}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div 
                      className={`h-2 rounded-full ${metrics.branch_coverage >= 80 ? 'bg-green-500' : metrics.branch_coverage >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${metrics.branch_coverage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Couverture des instructions */}
          {metrics.instruction_coverage > 0 && (
            <div className={`border rounded-lg p-6 ${getCoverageBgColor(metrics.instruction_coverage)}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-700">Couverture des Instructions</h3>
                  <p className={`text-4xl font-bold ${getCoverageColor(metrics.instruction_coverage)}`}>
                    {metrics.instruction_coverage.toFixed(1)}%
                  </p>
                </div>
                <Activity className={`w-8 h-8 ${getCoverageColor(metrics.instruction_coverage)}`} />
              </div>
              
              {metrics.instructions_total > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Instructions couvertes:</span>
                    <span className="font-medium">{metrics.instructions_covered}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Total instructions:</span>
                    <span className="font-medium">{metrics.instructions_total}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div 
                      className={`h-2 rounded-full ${metrics.instruction_coverage >= 80 ? 'bg-green-500' : metrics.instruction_coverage >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${metrics.instruction_coverage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Analyse des endpoints */}
      {(metrics.endpoints_count > 0 || metrics.tests_per_endpoint > 0) && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <Target className="w-5 h-5 text-purple-500 mr-2" />
            Analyse des Endpoints API
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {metrics.endpoints_count > 0 && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-purple-700">Endpoints Détectés</h3>
                    <p className="text-4xl font-bold text-purple-900">{metrics.endpoints_count}</p>
                  </div>
                  <div className="p-3 bg-purple-100 rounded-full">
                    <Target className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
                <p className="text-sm text-purple-700 mt-3">
                  Nombre total d'endpoints REST trouvés dans l'API
                </p>
              </div>
            )}
            
            {metrics.tests_per_endpoint > 0 && (
              <div className={`border rounded-lg p-6 ${
                metrics.tests_per_endpoint >= 2 
                  ? 'bg-green-50 border-green-200' 
                  : metrics.tests_per_endpoint >= 1 
                  ? 'bg-yellow-50 border-yellow-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700">Tests par Endpoint</h3>
                    <p className={`text-4xl font-bold ${
                      metrics.tests_per_endpoint >= 2 
                        ? 'text-green-600' 
                        : metrics.tests_per_endpoint >= 1 
                        ? 'text-yellow-600' 
                        : 'text-red-600'
                    }`}>
                      {metrics.tests_per_endpoint.toFixed(1)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    metrics.tests_per_endpoint >= 2 
                      ? 'bg-green-100' 
                      : metrics.tests_per_endpoint >= 1 
                      ? 'bg-yellow-100' 
                      : 'bg-red-100'
                  }`}>
                    <CheckCircle className={`w-6 h-6 ${
                      metrics.tests_per_endpoint >= 2 
                        ? 'text-green-600' 
                        : metrics.tests_per_endpoint >= 1 
                        ? 'text-yellow-600' 
                        : 'text-red-600'
                    }`} />
                  </div>
                </div>
                
                <div className="mt-3">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    metrics.tests_per_endpoint >= 2 
                      ? 'bg-green-100 text-green-800' 
                      : metrics.tests_per_endpoint >= 1 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {metrics.tests_per_endpoint >= 2 
                      ? '✅ Excellent' 
                      : metrics.tests_per_endpoint >= 1 
                      ? '⚠️ Basique' 
                      : '❌ Insuffisant'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analyse de qualité globale */}
      {testResults.quality_analysis && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            ⭐ Analyse de Qualité Globale
          </h2>
          
          <div className={`p-6 rounded-lg border-2 ${
            testResults.quality_analysis.overall_score >= 85 
              ? 'bg-green-50 border-green-200' 
              : testResults.quality_analysis.overall_score >= 70 
              ? 'bg-blue-50 border-blue-200' 
              : testResults.quality_analysis.overall_score >= 50 
              ? 'bg-yellow-50 border-yellow-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Score Global de Qualité</h3>
                <p className="text-sm text-gray-600">Basé sur la couverture et la complétude des tests</p>
              </div>
              <div className="text-center">
                <p className={`text-5xl font-bold ${
                  testResults.quality_analysis.overall_score >= 85 
                    ? 'text-green-600' 
                    : testResults.quality_analysis.overall_score >= 70 
                    ? 'text-blue-600' 
                    : testResults.quality_analysis.overall_score >= 50 
                    ? 'text-yellow-600' 
                    : 'text-red-600'
                }`}>
                  {testResults.quality_analysis.overall_score.toFixed(0)}
                </p>
                <p className="text-lg font-medium text-gray-600">/100</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Qualité de Couverture</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase ${
                    testResults.quality_analysis.coverage_quality === 'excellent' 
                      ? 'bg-green-100 text-green-800' 
                      : testResults.quality_analysis.coverage_quality === 'good' 
                      ? 'bg-blue-100 text-blue-800' 
                      : testResults.quality_analysis.coverage_quality === 'fair' 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {testResults.quality_analysis.coverage_quality}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Complétude des Tests</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase ${
                    testResults.quality_analysis.test_completeness === 'comprehensive' 
                      ? 'bg-green-100 text-green-800' 
                      : testResults.quality_analysis.test_completeness === 'adequate' 
                      ? 'bg-blue-100 text-blue-800' 
                      : testResults.quality_analysis.test_completeness === 'minimal' 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {testResults.quality_analysis.test_completeness}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Recommandations */}
          {testResults.recommendations && testResults.recommendations.length > 0 && (
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-md font-semibold text-blue-900 mb-3 flex items-center">
                💡 Recommandations d'Amélioration
              </h4>
              <ul className="space-y-2">
                {testResults.recommendations.map((rec: string, index: number) => (
                  <li key={index} className="flex items-start text-sm text-blue-800">
                    <span className="flex-shrink-0 w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3"></span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Logs d'exécution */}
      {testResults.logs && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            📋 Logs d'Exécution
          </h2>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto">
            <pre className="text-sm whitespace-pre-wrap font-mono">
              {testResults.logs}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}