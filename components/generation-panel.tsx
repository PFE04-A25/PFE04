"use client";
import { StartButton } from "@/components/generation-start-button";
import { sendRequest } from "@/hooks/sendrequest";
import { GenerationOutput } from "./generation-output";
import GenerationStatusBadge from "./generation-status-badge";
import ModelTemperatureSlider from "./model-temperature-slider";
import PromptTeaxtarea from "./prompt-textarea";
import SelectTests from "./select-test-type";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";

export interface GenerationPanelProps {
  prompt: string;
  selectedTest: string;
  outputCode: string;
  isLoading: boolean;
  setSelectedTest: (selectedTest: string) => void;
  setOutputCode: (outputCode: string) => void;
  setIsLoading: (isLoading: boolean) => void;
}

export function GenerationPanel({
  prompt,
  selectedTest,
  outputCode,
  isLoading,
  setSelectedTest,
  setIsLoading,
  setOutputCode,
}: GenerationPanelProps) {
  return (
    <div className="absolute inset-0 flex flex-col">
      <ScrollArea className="flex-grow">
        <div className="max-w-lg mx-auto space-y-6 py-8 p-4 md:p-6">
          <h2 className="text-lg font-semibold tracking-tight">
            Generation Panel
          </h2>
          <SelectTests setSelectedTest={setSelectedTest} />
          <PromptTeaxtarea />
          <ModelTemperatureSlider />
          <Separator />
          <h2 className="text-lg font-semibold tracking-tight">Output</h2>
          <GenerationOutput 
            generatedTest={outputCode} 
            isLoading={isLoading} 
          />
        </div>
      </ScrollArea>

      <div className="w-full h-16 border-t border-border flex-shrink-0">
        <div className="w-full h-full flex items-center justify-between px-4 md:px-6">
          <GenerationStatusBadge
            isLoading={isLoading}
            outputCode={outputCode}
          />
          <StartButton
            buttonText="Generate"
            isLoading={isLoading}
            action={() =>
              sendRequest({
                testType: selectedTest,
                prompt,
                outputCode,
                setIsLoading,
                setOutputCode,
              })
            }
          />
        </div>
      </div>
    </div>
  );
}
