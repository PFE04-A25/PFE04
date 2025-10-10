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
import { defaultSourceCode } from "@/lib/utils";

export default function Home() {
  const [sourceCode, setSourceCode] = React.useState<string>(defaultSourceCode);
  const [outputCode, setOutputCode] = React.useState<string>("");
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [selectedTest, setSelectedTest] = React.useState("restassured");

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
          isLoading={isLoading}
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
            setIsLoading={setIsLoading}
            isLoading={isLoading}
          />
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
