"use client";

import * as React from "react";
import { useEffect } from "react";
import { CodePanel } from "@/components/code-panel";
import { GenerationPanel } from "@/components/generation-panel";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { useAppContext } from "@/context/AppContext";

export default function Home() {
  // ← CHANGEMENT : Utiliser le Context au lieu du state local
  const {
    state,
    setSourceCode,
    setOutputCode,
    setSelectedTest,
    setIsGenerating
  } = useAppContext();

  const { sourceCode, outputCode, selectedTest, isGenerating } = state;

  // debugging to track state changes
  useEffect(() => {
    console.log("Output code updated:", outputCode ? `${outputCode.substring(0, 50)}...` : "empty");
  }, [outputCode]);

  // Fix the typo in the prop name
  const handleSetOutputCode = (code: string) => {
    console.log("Setting output code:", code ? `${code.substring(0, 50)}...` : "empty");
    setOutputCode(code);
  };

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="h-full w-full"
      suppressHydrationWarning
    >
      <ResizablePanel defaultSize={60}>
        <CodePanel
          selectedTest={selectedTest}
          sourceCode={sourceCode}
          setSourceCode={setSourceCode}
          outputCode={outputCode}
          setOutputCode={setOutputCode}
          isLoading={isGenerating}
        />
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={40} maxSize={55}>
        <div className="relative h-full">
          <GenerationPanel
            selectedTest={selectedTest}
            setSelectedTest={setSelectedTest}
            prompt={sourceCode}
            outputCode={outputCode}
            setOutputCode={setOutputCode}
            setIsLoading={setIsGenerating}
            isLoading={isGenerating}
          />
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}