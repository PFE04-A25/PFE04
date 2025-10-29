import { ModeToggle } from "./mode-toggle";
import ModelStatusBadge from "./model-status-badge";
import { Navigation } from "./navigation";
import UserHelper from "./user-helper";

export function AppHeader() {
  return (
    <header className="w-full h-16 flex items-center justify-between border-b border-border px-4 md:px-6">
      <div className="flex items-center space-x-8">
        <h1 className="text-lg font-semibold tracking-tight">RestAuto</h1>
        <Navigation />
      </div>
      <div className="flex items-center gap-1 [&>*:first-child]:mr-2">
        <ModelStatusBadge />
        <UserHelper />
        <ModeToggle />
      </div>
    </header>
  );
}
