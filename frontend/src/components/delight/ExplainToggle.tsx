import { useExplainMode } from "@/context/ExplainModeContext";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function GraduationCapIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 9 3 12 0v-5" />
    </svg>
  );
}

function ZapIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// ExplainToggle – inline toggle for Header
// ---------------------------------------------------------------------------

export default function ExplainToggle() {
  const { explainMode, toggleExplainMode } = useExplainMode();

  return (
    <button
      onClick={toggleExplainMode}
      className={[
        "group flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all duration-200",
        explainMode
          ? "bg-accent-500/20 text-accent-400 ring-1 ring-accent-500/30"
          : "text-surface-400 hover:bg-surface-800 hover:text-surface-200",
      ].join(" ")}
      title={
        explainMode
          ? "Switch to Expert Mode"
          : "Switch to Beginner Mode"
      }
      aria-label={
        explainMode
          ? "Currently in Beginner Mode. Click to switch to Expert Mode."
          : "Currently in Expert Mode. Click to switch to Beginner Mode."
      }
      role="switch"
      aria-checked={explainMode}
    >
      {explainMode ? (
        <>
          <GraduationCapIcon className="h-4 w-4" />
          <span className="hidden sm:inline">Beginner Mode</span>
        </>
      ) : (
        <>
          <ZapIcon className="h-4 w-4" />
          <span className="hidden sm:inline">Expert Mode</span>
        </>
      )}

      {/* Toggle track visual */}
      <div
        className={[
          "relative ml-1 hidden h-4 w-7 rounded-full transition-colors sm:block",
          explainMode ? "bg-accent-500/40" : "bg-surface-600",
        ].join(" ")}
      >
        <div
          className={[
            "absolute top-0.5 h-3 w-3 rounded-full transition-all duration-200",
            explainMode
              ? "left-3.5 bg-accent-400"
              : "left-0.5 bg-surface-400",
          ].join(" ")}
        />
      </div>
    </button>
  );
}
