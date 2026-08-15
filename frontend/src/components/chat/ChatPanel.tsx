import { useRef, useEffect, useCallback } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function ChatBubbleIcon({ className }: { className?: string }) {
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
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
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

function SparklesIcon({ className }: { className?: string }) {
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
      <path d="M12 3l1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Suggested questions
// ---------------------------------------------------------------------------

const SUGGESTED_QUESTIONS = [
  "Who should I start this week?",
  "Any good waiver picks?",
  "Analyze my roster",
  "Explain my matchup",
];

// ---------------------------------------------------------------------------
// ChatPanel
// ---------------------------------------------------------------------------

interface ChatPanelProps {
  isOpen: boolean;
  onToggle: () => void;
}

export default function ChatPanel({ isOpen, onToggle }: ChatPanelProps) {
  const { messages, sendMessage, isStreaming } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive or content streams in
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Handle keyboard escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onToggle();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onToggle]);

  const isEmpty = messages.length === 0;

  return (
    <>
      {/* Overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      {/* Toggle button (visible when panel is closed) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed bottom-20 right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-accent-500 text-surface-900 shadow-lg shadow-accent-500/25 transition-all hover:bg-accent-400 hover:shadow-xl hover:shadow-accent-500/30 active:scale-95 lg:bottom-6"
          aria-label="Open chat assistant"
        >
          <ChatBubbleIcon className="h-6 w-6" />
          {/* Notification dot */}
          <span className="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-surface-900 bg-success-400" />
        </button>
      )}

      {/* Slide-out panel */}
      <div
        className={[
          "fixed bottom-0 right-0 top-0 z-50 flex w-full flex-col border-l border-surface-700/50 bg-surface-900 shadow-2xl transition-transform duration-300 ease-in-out sm:w-[420px]",
          isOpen ? "translate-x-0" : "translate-x-full",
        ].join(" ")}
        role="dialog"
        aria-label="Chat assistant"
        aria-hidden={!isOpen}
      >
        {/* Panel header */}
        <div className="flex flex-shrink-0 items-center justify-between border-b border-surface-700/50 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-800">
              <SparklesIcon className="h-4 w-4 text-accent-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-surface-100">
                AI Assistant
              </h2>
              <p className="text-xs text-surface-500">
                Fantasy football expert
              </p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-surface-400 transition-colors hover:bg-surface-800 hover:text-surface-200"
            aria-label="Close chat"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Messages area */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto px-4 py-4"
          role="list"
          aria-label="Chat messages"
        >
          {isEmpty ? (
            <div className="flex h-full flex-col items-center justify-center gap-6 px-4">
              {/* Welcome state */}
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-800/50">
                <SparklesIcon className="h-8 w-8 text-accent-400" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-surface-100">
                  How can I help?
                </h3>
                <p className="mt-1 text-sm text-surface-400">
                  Ask me anything about your fantasy football team.
                </p>
              </div>

              {/* Suggested question chips */}
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    onClick={() => sendMessage(question)}
                    disabled={isStreaming}
                    className="rounded-full border border-surface-600/50 bg-surface-800/50 px-3.5 py-2 text-xs font-medium text-surface-300 transition-colors hover:border-accent-500/40 hover:bg-surface-800 hover:text-accent-400 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  isStreaming={
                    isStreaming &&
                    msg.role === "assistant" &&
                    idx === messages.length - 1
                  }
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </>
  );
}
