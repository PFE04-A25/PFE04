import { Textarea } from "./ui/textarea";

interface GenerationOutputProps {
  generatedTest?: string;
  isLoading?: boolean;
}

export function GenerationOutput({ 
  generatedTest, 
  isLoading = false 
}: GenerationOutputProps) {
  // Determine what text to display
  const displayValue = isLoading 
    ? "Generating test code..." 
    : generatedTest || "No test generated yet. Click 'Generate' to create a test.";
  
  return (
    <Textarea
      disabled
      className="h-[500px] resize-none bg-muted border-transparent shadow-none font-mono"
      value={displayValue}
      readOnly
    />
  );
}