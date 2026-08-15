import { useState } from "react";
import StrengthOfSchedule from "@/components/schedule/StrengthOfSchedule";
import PlayoffPlanner from "@/components/schedule/PlayoffPlanner";
import ByeWeekCalendar from "@/components/schedule/ByeWeekCalendar";

const TABS = [
  { id: "sos", label: "Strength of Schedule" },
  { id: "playoffs", label: "Playoff Planner" },
  { id: "byes", label: "Bye Weeks" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SchedulePage() {
  const [activeTab, setActiveTab] = useState<TabId>("sos");

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Schedule</h1>
        <p className="mt-1 text-surface-400">
          Strength of schedule, bye weeks, and playoff scenarios
        </p>
      </div>

      {/* ── Tabs ── */}
      <div className="flex items-center gap-1 overflow-x-auto rounded-lg bg-surface-900 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "flex-1 whitespace-nowrap rounded-md px-4 py-2.5 text-sm font-medium transition-colors",
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
      {activeTab === "sos" && <StrengthOfSchedule />}
      {activeTab === "playoffs" && <PlayoffPlanner />}
      {activeTab === "byes" && <ByeWeekCalendar />}
    </div>
  );
}
