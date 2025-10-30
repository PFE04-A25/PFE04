"use client";

import { BarChart3, Home, TestTube } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';

export function Navigation() {
  const router = useRouter();
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Générateur',
      path: '/',
      icon: Home,
      description: 'Génération de tests'
    },
    {
      name: 'Tests',
      path: '/tests',
      icon: TestTube,
      description: 'Exécution de tests'
    },
    {
      name: 'Résultats',
      path: '/results',
      icon: BarChart3,
      description: 'Analyse des résultats'
    }
  ];

  return (
    <nav className="flex items-center space-x-1">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path));
        
        return (
          <button
            key={item.path}
            onClick={() => router.push(item.path)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              isActive
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800'
            }`}
            title={item.description}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{item.name}</span>
          </button>
        );
      })}
    </nav>
  );
}