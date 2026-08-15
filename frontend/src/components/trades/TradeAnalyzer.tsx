import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { playerApi, type Player, type Team } from "@/api/client";
import { useAnalyzeTrade } from "@/hooks/useTrades";
import { useLeague } from "@/context/LeagueContext";
import { useExplainMode } from "@/context/ExplainModeContext";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

// ── Search icon ────────────────────────────────────────────────────────
function SearchIcon({ className }: { className?: string }) {
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
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

// ── X icon ─────────────────────────────────────────────────────────────
function XIcon({ className }: { className?: string }) {
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
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

// ── Verdict badge ──────────────────────────────────────────────────────
function VerdictBadge({ verdict }: { verdict: string }) {
  let colorClass: string;
  let label: string;

  switch (verdict) {
    case "send":
      label = "Accept";
      colorClass = "bg-success-400/15 text-success-400 border-success-400/30";
      break;
    case "receive":
      label = "Reject";
      colorClass = "bg-danger-400/15 text-danger-400 border-danger-400/30";
      break;
    default:
      label = "Fair";
      colorClass = "bg-accent-400/15 text-accent-400 border-accent-400/30";
  }

  return (
    <span
      className={`inline-flex items-center rounded-lg border px-3 py-1.5 text-sm font-bold ${colorClass}`}
    >
      {label}
    </span>
  );
}

// ── Value comparison bar ───────────────────────────────────────────────
function ValueBar({ fairnessScore }: { fairnessScore: number }) {
  // fairnessScore: 0-100 where 50 = perfectly even
  const sendWidth = Math.max(10, Math.min(90, fairnessScore));
  const receiveWidth = 100 - sendWidth;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-surface-400">
        <span>You Give</span>
        <span>You Receive</span>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-surface-900">
        <div
          className="bg-danger-400/70 transition-all duration-300"
          style={{ width: `${sendWidth}%` }}
        />
        <div
          className="bg-success-400 transition-all duration-300"
          style={{ width: `${receiveWidth}%` }}
        />
      </div>
    </div>
  );
}

// ── Player search dropdown ─────────────────────────────────────────────
function PlayerSearchDropdown({
  selectedPlayers,
  onAdd,
  onRemove,
  label,
}: {
  selectedPlayers: Player[];
  onAdd: (player: Player) => void;
  onRemove: (playerId: string) => void;
  label: string;
}) {
  const [search, setSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const { data: allPlayers } = useQuery({
    queryKey: ["players", "all"],
    queryFn: () => playerApi.getAll({ limit: 200 }),
    staleTime: 1000 * 60 * 10,
  });

  const filteredPlayers = useMemo(() => {
    if (!allPlayers || !search.trim()) return [];
    const query = search.toLowerCase();
    const selectedIds = new Set(selectedPlayers.map((p) => p.id));
    return allPlayers
      .filter(
        (p) =>
          !selectedIds.has(p.id) &&
          (p.name.toLowerCase().includes(query) ||
            p.team.toLowerCase().includes(query) ||
            p.position.toLowerCase().includes(query))
      )
      .slice(0, 8);
  }, [allPlayers, search, selectedPlayers]);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-surface-200">{label}</h3>

      {/* Selected players */}
      {selectedPlayers.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedPlayers.map((player) => (
            <span
              key={player.id}
              className="inline-flex items-center gap-1.5 rounded-lg border border-surface-600 bg-surface-700 px-2.5 py-1 text-xs font-medium text-surface-200"
            >
              <span className="text-surface-400">{player.position}</span>
              {player.name}
              <button
                onClick={() => onRemove(player.id)}
                className="ml-0.5 rounded p-0.5 text-surface-500 transition-colors hover:text-danger-400"
                aria-label={`Remove ${player.name}`}
              >
                <XIcon className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder="Search players..."
          className="w-full rounded-lg border border-surface-600 bg-surface-900 py-2 pl-9 pr-3 text-sm text-surface-100 placeholder-surface-500 transition-colors focus:border-primary-700 focus:outline-none focus:ring-1 focus:ring-primary-700"
        />

        {/* Dropdown */}
        {isOpen && filteredPlayers.length > 0 && (
          <div className="absolute left-0 right-0 top-full z-20 mt-1 max-h-48 overflow-y-auto rounded-lg border border-surface-600 bg-surface-800 shadow-xl">
            {filteredPlayers.map((player) => (
              <button
                key={player.id}
                onMouseDown={(e) => {
                  e.preventDefault();
                  onAdd(player);
                  setSearch("");
                  setIsOpen(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-surface-200 transition-colors hover:bg-surface-700"
              >
                <span className="w-8 text-xs font-medium text-surface-400">
                  {player.position}
                </span>
                <span className="flex-1 truncate">{player.name}</span>
                <span className="text-xs text-surface-500">{player.team}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────
export default function TradeAnalyzer() {
  const { teams } = useLeague();
  const { explainMode } = useExplainMode();

  const [sendPlayers, setSendPlayers] = useState<Player[]>([]);
  const [receivePlayers, setReceivePlayers] = useState<Player[]>([]);
  const [targetTeamId, setTargetTeamId] = useState("");

  const analyzeMutation = useAnalyzeTrade();

  const canAnalyze =
    sendPlayers.length > 0 && receivePlayers.length > 0 && targetTeamId !== "";

  function handleAnalyze() {
    if (!canAnalyze) return;
    analyzeMutation.mutate({
      sendPlayerIds: sendPlayers.map((p) => p.id),
      receivePlayerIds: receivePlayers.map((p) => p.id),
      targetTeamId,
    });
  }

  function handleReset() {
    setSendPlayers([]);
    setReceivePlayers([]);
    setTargetTeamId("");
    analyzeMutation.reset();
  }

  return (
    <div className="space-y-6">
      {/* ── Target team selector ── */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-surface-300">
          Trade Partner
        </label>
        <select
          value={targetTeamId}
          onChange={(e) => setTargetTeamId(e.target.value)}
          className="w-full rounded-lg border border-surface-600 bg-surface-900 px-3 py-2 text-sm text-surface-100 focus:border-primary-700 focus:outline-none focus:ring-1 focus:ring-primary-700"
        >
          <option value="">Select a team...</option>
          {teams?.map((team: Team) => (
            <option key={team.id} value={team.id}>
              {team.name} ({team.owner})
            </option>
          ))}
        </select>
      </div>

      {/* ── Two panels ── */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* You Give */}
        <div className="rounded-xl border border-danger-400/20 bg-danger-400/5 p-4">
          <PlayerSearchDropdown
            selectedPlayers={sendPlayers}
            onAdd={(p) => setSendPlayers((prev) => [...prev, p])}
            onRemove={(id) =>
              setSendPlayers((prev) => prev.filter((p) => p.id !== id))
            }
            label="You Give"
          />
        </div>

        {/* You Receive */}
        <div className="rounded-xl border border-success-400/20 bg-success-400/5 p-4">
          <PlayerSearchDropdown
            selectedPlayers={receivePlayers}
            onAdd={(p) => setReceivePlayers((prev) => [...prev, p])}
            onRemove={(id) =>
              setReceivePlayers((prev) => prev.filter((p) => p.id !== id))
            }
            label="You Receive"
          />
        </div>
      </div>

      {/* ── Action buttons ── */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze || analyzeMutation.isPending}
          className="btn-accent"
        >
          {analyzeMutation.isPending ? (
            <span className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              Analyzing...
            </span>
          ) : (
            "Analyze Trade"
          )}
        </button>

        {(sendPlayers.length > 0 ||
          receivePlayers.length > 0 ||
          analyzeMutation.data) && (
          <button onClick={handleReset} className="btn-ghost">
            Reset
          </button>
        )}
      </div>

      {/* ── Error state ── */}
      {analyzeMutation.isError && (
        <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-4">
          <p className="text-sm text-danger-300">
            {(analyzeMutation.error as Error)?.message ??
              "Failed to analyze trade. Please try again."}
          </p>
        </div>
      )}

      {/* ── Results ── */}
      {analyzeMutation.data && (
        <div className="space-y-4 rounded-xl border border-surface-700 bg-surface-800 p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-surface-100">
              Trade Analysis
            </h3>
            <VerdictBadge verdict={analyzeMutation.data.winnerSide} />
          </div>

          <ValueBar fairnessScore={analyzeMutation.data.fairnessScore} />

          <div className="space-y-2">
            <p className="text-sm font-medium text-surface-200">
              {analyzeMutation.data.recommendation}
            </p>
            {explainMode && analyzeMutation.data.impact && (
              <div className="rounded-lg bg-primary-800/20 px-3 py-2">
                <p className="text-xs leading-relaxed text-surface-300">
                  {analyzeMutation.data.impact}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
