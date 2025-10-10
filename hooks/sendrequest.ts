import { exctractTestCaseCode } from "@/lib/utils";
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
}

export const sendRequest = async ({
  testType,
  prompt,
  outputCode,
  setIsLoading,
  setOutputCode,
}: SendRequestProps) => {
  setIsLoading(true);
  const isValidTestType = Object.values(TestType).includes(
    testType as TestType
  );

  if (outputCode !== "") {
    setOutputCode("");
  }

  if (!isValidTestType) {
    throw new Error(
      `Invalid testType: ${testType}. Expected values are: ${Object.values(
        TestType
      ).join(", ")}`
    );
  }

  const api = `/api/${testType}`;

  const response = await fetch(api, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      api_code: prompt,
    }),
  });

  if (response.status !== 200) {
    setIsLoading(false);
    toast.error("Failed to send request to the server", {
      description: `Request failed with status ${response.status}`,
    });
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = await response.json();

  console.log("API Response received:", {
  hasGeneratedTest: !!data.generated_test,
  responseLength: data.generated_test?.length || 0
  });
  // Check if data.generated_test exists
  if (!data.generated_test) {
    toast.error("No test generated", {
      description: "The server response didn't contain any generated test code"
    });
    setIsLoading(false);
    return;
  }
  const codeFilter = exctractTestCaseCode(data.generated_test);
  if (codeFilter && codeFilter.length > 0) {
    console.log("Extracted code successfully, length:", codeFilter[0].length);
    setOutputCode(codeFilter[0]);
  } else {
    console.error("Failed to extract code from response:", data.generated_test);
    toast.error("Failed to parse response");
    setOutputCode(data.generated_test); // Fallback to using raw response
  }
  setIsLoading(false);
};
