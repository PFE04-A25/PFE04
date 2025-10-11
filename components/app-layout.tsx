import { AppHeader } from "./app-header";

export function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <main className="w-full min-h-screen flex flex-col">
      <AppHeader />
      <div className="flex-grow overflow-y-auto">{children}</div>
    </main>
  );
}
