import { useState } from "react";
import { useWaiverRecommendations } from "@/hooks/useWaivers";
import WaiverPlayerCard from "./WaiverPlayerCard";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

const POSITIONS = ["All", "QB", "RB", "WR", "TE"] as const;
type PositionFilter = (typeof POSITIONS)[number];

export default function WaiverRadar() {
  const [activePosition, setActivePosition] = useState<PositionFilter>("All");

  const positionParam = activePosition === "All" ? undefined : activePosition;
  const {
    data: recommendations,
    isLoading,
    isError,
    error,
    refetch,
  } = useWaiverRecommendations(positionParam);

  return (
    <div className="space-y-4">
      {/* ── Position filter tabs ── */}
      <div className="flex items-center gap-1 overflow-x-auto rounded-lg bg-surface-900 p-1">
        {POSITIONS.map((pos) => (
          <button
            key={pos}
            onClick={() => setActivePosition(pos)}
            className={[
              "rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap",
              activePosition === pos
                ? "bg-primary-800 text-accent-400 shadow-sm"
                : "text-surface-400 hover:text-surface-200 hover:bg-surface-800",
            ].join(" ")}
          >
            {pos}
          </button>
        ))}
      </div>

      {/* ── Loading state ── */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner size="lg" label="Scanning waivers..." />
        </div>
      )}

      {/* ── Error state ── */}
      {isError && (
        <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
          <p className="text-sm text-danger-300">
            {(error as Error)?.message ?? "Failed to load waiver recommendations."}
          </p>
          <button
            onClick={() => refetch()}
            className="btn-primary mt-4"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Empty state ── */}
      {!isLoading && !isError && recommendations?.length === 0 && (
        <EmptyState
          title="No waiver recommendations"
          description="Check back later for new waiver wire picks."
        />
      )}

      {/* ── Player card grid ── */}
      {!isLoading && !isError && recommendations && recommendations.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recommendations.map((rec) => (
            <WaiverPlayerCard key={rec.player.id} recommendation={rec} />
          ))}
        </div>
      )}
    </div>
  );
}
