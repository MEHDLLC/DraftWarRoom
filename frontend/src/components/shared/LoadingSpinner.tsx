interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-2",
  lg: "h-12 w-12 border-3",
};

export default function LoadingSpinner({
  size = "md",
  className = "",
  label,
}: LoadingSpinnerProps) {
  return (
    <div
      className={["flex flex-col items-center gap-3", className].join(" ")}
      role="status"
      aria-label={label ?? "Loading"}
    >
      <div
        className={[
          "animate-spin rounded-full border-primary-800 border-t-accent-400",
          sizeClasses[size],
        ].join(" ")}
      />
      {label && (
        <span className="text-sm text-surface-400">{label}</span>
      )}
      <span className="sr-only">{label ?? "Loading..."}</span>
    </div>
  );
}
