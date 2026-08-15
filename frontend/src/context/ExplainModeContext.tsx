import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";

interface ExplainModeContextValue {
  explainMode: boolean;
  toggleExplainMode: () => void;
  setExplainMode: (value: boolean) => void;
}

const ExplainModeContext = createContext<ExplainModeContextValue | undefined>(
  undefined,
);

const STORAGE_KEY = "dwr_explain_mode";

function getInitialValue(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "true";
  } catch {
    return false;
  }
}

export function ExplainModeProvider({ children }: { children: ReactNode }) {
  const [explainMode, setExplainModeState] = useState(getInitialValue);

  const setExplainMode = useCallback((value: boolean) => {
    setExplainModeState(value);
    try {
      localStorage.setItem(STORAGE_KEY, String(value));
    } catch {
      // localStorage may be unavailable
    }
  }, []);

  const toggleExplainMode = useCallback(() => {
    setExplainMode(!explainMode);
  }, [explainMode, setExplainMode]);

  return (
    <ExplainModeContext.Provider
      value={{ explainMode, toggleExplainMode, setExplainMode }}
    >
      {children}
    </ExplainModeContext.Provider>
  );
}

export function useExplainMode(): ExplainModeContextValue {
  const context = useContext(ExplainModeContext);
  if (context === undefined) {
    throw new Error(
      "useExplainMode must be used within an ExplainModeProvider",
    );
  }
  return context;
}
