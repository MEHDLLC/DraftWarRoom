import { useState } from "react";
import TradeAnalyzer from "@/components/trades/TradeAnalyzer";
import TradeFinder from "@/components/trades/TradeFinder";

const TABS = [
  { id: "analyze", label: "Analyze a Trade" },
  { id: "suggestions", label: "Trade Suggestions" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function TradesPage() {
  const [activeTab, setActiveTab] = useState<TabId>("analyze");

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Trades</h1>
        <p className="mt-1 text-surface-400">
          Evaluate trade scenarios and find winning deals
        </p>
      </div>

      {/* ── Tabs ── */}
      <div className="flex items-center gap-1 rounded-lg bg-surface-900 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "flex-1 rounded-md px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary-800 text-accent-400 shadow-sm"
                : "text-surface-400 hover:text-surface-200 hover:bg-surface-800",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      {activeTab === "analyze" && <TradeAnalyzer />}
      {activeTab === "suggestions" && <TradeFinder />}
    </div>
  );
}
