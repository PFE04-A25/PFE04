import { createTestCase } from "@/lib/actions/testcase.actions";
import { toast } from "sonner";

interface sendToDbProps {
  testType: string;
  prompt: string;
  testCaseGenerated: string;
  setIsLoading: (isLoading: boolean) => void;
}

export const sendToDB = async ({
  testType,
  prompt,
  testCaseGenerated,
  setIsLoading,
}: sendToDbProps) => {
  setIsLoading(true);

  try{
    const promise = () =>
      new Promise(async (resolve, reject) => {
        try {
          const result = await createTestCase({
            testType,
            sourceCode: prompt,
            testCase: testCaseGenerated,
          });
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

    await toast.promise(promise, {
      loading: "Saving to database...",
      success: () => {
        return `Test case saved successfully`;
      },
      error: (err) => `Failed to save: ${err.message}`,
    });
  } catch (error) {
    console.error("Error in sendToDB:", error);
  } finally {
    setIsLoading(false);
  }
};
