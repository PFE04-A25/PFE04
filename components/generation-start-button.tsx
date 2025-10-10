import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ArrowRightIcon } from "lucide-react";

interface StartButtonProps {
  action?: () => void;
  buttonText?: string;
  className?: string;
  isLoading?: boolean;
  icon?: React.ReactNode;
  disabled?: boolean;
}
export function StartButton({
  action,
  buttonText,
  className,
  isLoading,
  icon,
  disabled,
}: StartButtonProps) {
  return (
    <Button
      className={cn(`group`, className)}
      onClick={action}
      disabled={isLoading || disabled}
    >
      {icon}
      {buttonText}
      {!icon && (
        <ArrowRightIcon
          className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
          size={16}
          aria-hidden="true"
        />
      )}
    </Button>
  );
}
