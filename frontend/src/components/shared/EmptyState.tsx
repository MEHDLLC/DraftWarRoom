import { type ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

function DefaultIcon() {
  return (
    <svg
      className="h-10 w-10 text-surface-600"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
      <polyline points="13 2 13 9 20 9" />
    </svg>
  );
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={[
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-surface-700 px-6 py-16 text-center",
        className,
      ].join(" ")}
    >
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-800">
        {icon ?? <DefaultIcon />}
      </div>

      <h3 className="mb-1 text-base font-semibold text-surface-200">
        {title}
      </h3>

      {description && (
        <p className="mb-6 max-w-sm text-sm text-surface-400">{description}</p>
      )}

      {action && <div>{action}</div>}
    </div>
  );
}
