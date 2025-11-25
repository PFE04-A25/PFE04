import { Label } from "@/components/ui/label";
import { SelectNative } from "@/components/ui/select-native";
import { useId } from "react";
interface SelectTestsProps {
  setSelectedTest: (selectedTest: string) => void;
}
export default function SelectTests({ setSelectedTest }: SelectTestsProps) {
  const id = useId();

  return (
    <div className="grid w-full items-center gap-1.5">
      <Label htmlFor={id}>
        Test Type
        <span className="text-destructive dark:text-red-600">*</span>
      </Label>
      <SelectNative
        id={id}
        defaultValue="restassured"
        onChange={(e) => setSelectedTest(e.target.value)}
      >
        <option value="" disabled>
          Please select a test type
        </option>
        <option value="restassured">REST-asssured</option>
        <option value="unit">
          Unit test
        </option>
        <option value="e2e" disabled>
          End to End (E2E) test
        </option>
        <option value="integration" disabled>
          Integration test
        </option>
      </SelectNative>
    </div>
  );
}
