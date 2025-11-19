import { toast } from "sonner";

enum TestType {
  RestAssured = "restassured",
  Unit = "unit",
}

interface SendRequestProps {
  testType: string;
  prompt: string;
  outputCode: string;
  setIsLoading: (isLoading: boolean) => void;
  setOutputCode: (outputCode: string) => void;
  onGenerationComplete?: (generationId: string, generatedTest: string) => void;
}

export const sendRequest = async ({
  testType,
  prompt,
  outputCode,
  setIsLoading,
  setOutputCode,
  onGenerationComplete,
}: SendRequestProps) => {
  setIsLoading(true);
  
  const isValidTestType = Object.values(TestType).includes(
    testType as TestType
  );

  if (outputCode !== "") {
    setOutputCode("");
  }

  if (!isValidTestType) {
    toast.error(`Invalid testType: ${testType}`);
    setIsLoading(false);
    return;
  }

  try {
    const api = `/api/generate-test`;

    const response = await fetch(api, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        api_code: prompt,
        testType: testType,
      }),
    });

    if (response.status !== 200) {
      toast.error("Failed to send request to the server", {
        description: `Request failed with status ${response.status}`,
      });
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();

    console.log("========== RÉPONSE DU BACKEND ==========");
    console.log("generated_test présent ?", !!data.generated_test);
    console.log("generation_id présent ?", !!data.generation_id);
    console.log("generation_id valeur :", data.generation_id);
    console.log("=======================================");

    if (!data.generated_test) {
      toast.error("No test generated", {
        description: "The server response didn't contain any generated test code",
      });
      setIsLoading(false);
      return;
    }

    const cleanCode = data.generated_test.trim();

    if (cleanCode && cleanCode.length > 0) {
      console.log("Code received successfully, length:", cleanCode.length);
      setOutputCode(cleanCode);

      if (onGenerationComplete) {
        if (data.generation_id) {
          console.log("APPEL onGenerationComplete avec:", {
            generationId: data.generation_id,
            testLength: cleanCode.length,
            timestamp: new Date().toISOString()
          });
          onGenerationComplete(data.generation_id, cleanCode);
        } else {
          console.warn("generation_id manquant");
        }
      }

      toast.success("Test generated successfully!");
    } else {
      console.error("Received empty code from response");
      toast.error("Failed to parse response");
      setOutputCode(data.generated_test);
    }

  } catch (error) {
    console.error("Error during test generation:", error);
    toast.error("Failed to generate test", {
      description: error instanceof Error ? error.message : "Unknown error",
    });
  } finally {
    setIsLoading(false);
  }
};