"use client";


interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  backgroundColor?: string;
  label?: string;
  showPercentage?: boolean;
}

export function CircularProgress({
  percentage,
  size = 120,
  strokeWidth = 8,
  color = '#3B82F6',
  backgroundColor = '#E5E7EB',
  label,
  showPercentage = true
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  const getColor = (value: number) => {
    if (value >= 90) return '#10B981'; // green-500
    if (value >= 80) return '#3B82F6'; // blue-500
    if (value >= 60) return '#F59E0B'; // yellow-500
    return '#EF4444'; // red-500
  };

  const finalColor = color === '#3B82F6' ? getColor(percentage) : color;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="transform -rotate-90"
          width={size}
          height={size}
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={backgroundColor}
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={finalColor}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            {showPercentage && (
              <div className="text-2xl font-bold" style={{ color: finalColor }}>
                {percentage.toFixed(1)}%
              </div>
            )}
            {label && (
              <div className="text-xs text-gray-600 mt-1">
                {label}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface CoverageChartsProps {
  metrics: {
    line_coverage: number;
    branch_coverage: number;
    instruction_coverage: number;
    lines_covered?: number;
    lines_total?: number;
    branches_covered?: number;
    branches_total?: number;
    instructions_covered?: number;
    instructions_total?: number;
  };
}

export function CoverageCharts({ metrics }: CoverageChartsProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
        📊 Vue d'ensemble de la Couverture
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Couverture de lignes */}
        {metrics.line_coverage > 0 && (
          <div className="text-center">
            <CircularProgress
              percentage={metrics.line_coverage}
              label="Lignes"
            />
            <div className="mt-3">
              <h3 className="font-semibold text-gray-800">Couverture de Lignes</h3>
              {metrics.lines_total && metrics.lines_covered && (
                <p className="text-sm text-gray-600 mt-1">
                  {metrics.lines_covered} sur {metrics.lines_total} lignes
                </p>
              )}
            </div>
          </div>
        )}
        
        {/* Couverture des branches */}
        {metrics.branch_coverage > 0 && (
          <div className="text-center">
            <CircularProgress
              percentage={metrics.branch_coverage}
              label="Branches"
            />
            <div className="mt-3">
              <h3 className="font-semibold text-gray-800">Couverture des Branches</h3>
              {metrics.branches_total && metrics.branches_covered && (
                <p className="text-sm text-gray-600 mt-1">
                  {metrics.branches_covered} sur {metrics.branches_total} branches
                </p>
              )}
            </div>
          </div>
        )}
        
        {/* Couverture des instructions */}
        {metrics.instruction_coverage > 0 && (
          <div className="text-center">
            <CircularProgress
              percentage={metrics.instruction_coverage}
              label="Instructions"
            />
            <div className="mt-3">
              <h3 className="font-semibold text-gray-800">Couverture des Instructions</h3>
              {metrics.instructions_total && metrics.instructions_covered && (
                <p className="text-sm text-gray-600 mt-1">
                  {metrics.instructions_covered} sur {metrics.instructions_total} instructions
                </p>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Résumé global */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="text-center">
          <h4 className="text-md font-semibold text-gray-800 mb-3">Résumé Global</h4>
          <div className="flex justify-center items-center space-x-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {((metrics.line_coverage + metrics.branch_coverage + metrics.instruction_coverage) / 3).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Moyenne Globale</div>
            </div>
            
            <div className="h-12 w-px bg-gray-300"></div>
            
            <div className="text-center">
              <div className={`text-2xl font-bold ${
                Math.min(metrics.line_coverage, metrics.branch_coverage) >= 80 
                  ? 'text-green-600' 
                  : Math.min(metrics.line_coverage, metrics.branch_coverage) >= 60 
                  ? 'text-yellow-600' 
                  : 'text-red-600'
              }`}>
                {Math.min(metrics.line_coverage, metrics.branch_coverage).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Min. Critique</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}