import DraftValueTracker from "@/components/draft/DraftValueTracker";

export default function DraftPage() {
  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Draft</h1>
        <p className="mt-1 text-surface-400">
          Draft board, value tracker, and pick recommendations
        </p>
      </div>

      {/* ── Main content ── */}
      <DraftValueTracker />
    </div>
  );
}
