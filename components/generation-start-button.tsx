import { Button } from "@/components/ui/button";
import { ArrowRightIcon } from "lucide-react";

interface StartButtonProps {
  action: () => void;
  buttonText: string;
  className?: string;
}
export default function StartButton({
  action,
  buttonText,
  className,
}: StartButtonProps) {
  return (
    <Button className={`group ` + className} onClick={action}>
      {buttonText}
      <ArrowRightIcon
        className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
        size={16}
        aria-hidden="true"
      />
    </Button>
  );
}
