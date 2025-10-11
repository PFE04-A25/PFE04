"use client";

import { usePathname } from 'next/navigation';
import { AppHeader } from "./app-header";

export function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  
  // La page générateur (/) a besoin d'un comportement différent pour les panels redimensionnables
  const isGeneratorPage = pathname === '/';
  
  return (
    <main className="w-full h-screen flex flex-col">
      <AppHeader />
      <div className={`flex-grow ${isGeneratorPage ? 'overflow-hidden' : 'overflow-y-auto'}`}>
        {children}
      </div>
    </main>
  );
}
