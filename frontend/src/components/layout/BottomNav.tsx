import { NavLink } from "react-router-dom";
import { navItems } from "./AppShell";

export default function BottomNav() {
  // Show a subset of nav items on mobile to keep the bar clean
  const mobileItems = navItems.filter((item) =>
    ["/", "/lineup", "/matchup", "/waivers", "/chat"].includes(item.to),
  );

  return (
    <nav className="flex-shrink-0 border-t border-surface-800 bg-surface-900/95 backdrop-blur-sm lg:hidden">
      <div className="flex items-center justify-around">
        {mobileItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
                  isActive
                    ? "text-accent-400"
                    : "text-surface-500 active:text-surface-300",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={[
                      "h-5 w-5",
                      isActive ? "text-accent-400" : "text-surface-500",
                    ].join(" ")}
                  />
                  <span>{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 h-0.5 w-8 rounded-full bg-accent-400" />
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
