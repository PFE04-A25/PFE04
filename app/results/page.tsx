"use client";

import { TestResultsDisplay } from '@/components/test-results-display';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TestExecutionResult, useTestExecutionResults } from '@/hooks/use-test-execution-results';
import { AlertCircle, ArrowLeft, BarChart3, CheckCircle, Clock, Eye, RefreshCw, Search, Trash2, XCircle } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function TestResultsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const executionId = searchParams.get('execution_id');
  
  const {
    executionResults,
    isLoading: resultsLoading,
    getResultById,
    fetchAndSaveResult,
    deleteResult,
    clearAllResults,
    getGlobalStats,
    searchResults
  } = useTestExecutionResults();

  const [selectedResult, setSelectedResult] = useState<TestExecutionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'details' | 'list'>('list');

  // Charger le résultat spécifique si execution_id est fourni
  useEffect(() => {
    const loadResult = async () => {
      setIsLoading(true);
      
      if (executionId) {
        // Mode détails - charger un résultat spécifique
        setViewMode('details');
        
        // D'abord vérifier dans le cache local
        const cachedResult = getResultById(executionId);
        if (cachedResult) {
          setSelectedResult(cachedResult);
          setIsLoading(false);
          return;
        }
        
        // Sinon récupérer depuis l'API
        try {
          const result = await fetchAndSaveResult(executionId);
          if (result) {
            setSelectedResult(result);
          } else {
            setError("Résultat introuvable");
          }
        } catch (error) {
          setError("Erreur lors du chargement du résultat");
          console.error('Erreur:', error);
        }
      } else {
        // Mode liste - afficher tous les résultats
        setViewMode('list');
        setSelectedResult(null);
      }
      
      setIsLoading(false);
    };

    if (!resultsLoading) {
      loadResult();
    }
  }, [executionId, resultsLoading, getResultById, fetchAndSaveResult]);

  const refreshResult = async () => {
    if (!executionId) return;
    
    setIsRefreshing(true);
    try {
      const result = await fetchAndSaveResult(executionId);
      if (result) {
        setSelectedResult(result);
        setError(null);
      }
    } catch (error) {
      setError("Erreur lors de l'actualisation");
    }
    setIsRefreshing(false);
  };

  const handleDeleteResult = (resultId: string) => {
    deleteResult(resultId);
    if (selectedResult?.execution_id === resultId) {
      router.push('/results');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running': return <Clock className="w-5 h-5 text-blue-500" />;
      default: return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'failed': return 'Échec';
      case 'running': return 'En cours';
      default: return 'Inconnu';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const filteredResults = searchResults(searchTerm, statusFilter);
  const stats = getGlobalStats();

  if (isLoading || resultsLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="space-y-4">
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Mode détails pour un résultat spécifique
  if (viewMode === 'details' && selectedResult) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* En-tête avec navigation */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/results')}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Retour à la liste</span>
              </Button>
              <div className="flex items-center space-x-2">
                {getStatusIcon(selectedResult.status)}
                <span className="text-xl font-semibold">
                  Résultat du test {selectedResult.execution_id.slice(0, 8)}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refreshResult}
                disabled={isRefreshing}
                className="flex items-center space-x-2"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>Actualiser</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDeleteResult(selectedResult.execution_id)}
                className="flex items-center space-x-2 text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
                <span>Supprimer</span>
              </Button>
            </div>
          </div>

          {error && (
            <Card className="mb-6 border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          <TestResultsDisplay testResults={selectedResult} />
        </div>
      </div>
    );
  }

  // Mode liste pour tous les résultats
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* En-tête */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/tests')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Historique des tests</span>
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">
              Résultats d'exécution
            </h1>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={clearAllResults}
              className="flex items-center space-x-2 text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
              <span>Tout supprimer</span>
            </Button>
          </div>
        </div>

        {/* Statistiques globales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Exécutions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-600">{stats.totalExecutions}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Taux de Succès
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-600">
                {stats.successRate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Couverture Moyenne
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-purple-600">
                {stats.avgCoverage.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Tests Réussis (Moy.)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-teal-600">
                {stats.avgTestSuccessRate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filtres de recherche */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Rechercher par ID d'exécution, logs, code..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="sm:w-48">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">Tous les statuts</option>
                  <option value="completed">Terminé</option>
                  <option value="failed">Échec</option>
                  <option value="running">En cours</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Liste des résultats */}
        {filteredResults.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Aucun résultat trouvé
                </h3>
                <p className="text-gray-500">
                  {executionResults.length === 0 
                    ? "Aucun test n'a encore été exécuté." 
                    : "Aucun résultat ne correspond à vos critères de recherche."
                  }
                </p>
                {executionResults.length === 0 && (
                  <Button
                    onClick={() => router.push('/tests')}
                    className="mt-4"
                  >
                    Voir les tests disponibles
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredResults.map((result) => (
              <Card key={result.execution_id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {getStatusIcon(result.status)}
                        <Badge className={getStatusColor(result.status)}>
                          {getStatusText(result.status)}
                        </Badge>
                        <span className="text-sm font-mono text-gray-600">
                          {result.execution_id.slice(0, 8)}...
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(result.timestamp).toLocaleString('fr-FR')}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Tests:</span>
                          <span className="ml-1 font-medium">
                            {result.metrics?.tests_run || 0}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Succès:</span>
                          <span className="ml-1 font-medium">
                            {result.metrics?.success_rate?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Couverture:</span>
                          <span className="ml-1 font-medium">
                            {result.metrics?.line_coverage?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Score:</span>
                          <span className="ml-1 font-medium">
                            {result.quality_analysis?.overall_score?.toFixed(1) || 0}/100
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => router.push(`/results?execution_id=${result.execution_id}`)}
                        className="flex items-center space-x-2"
                      >
                        <Eye className="w-4 h-4" />
                        <span>Détails</span>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteResult(result.execution_id)}
                        className="flex items-center space-x-2 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}