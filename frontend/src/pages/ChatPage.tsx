import { useRef, useEffect, useCallback } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

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

function TrashIcon({ className }: { className?: string }) {
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
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
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
  "Who are the top trending waiver adds?",
  "Evaluate a trade idea",
];

// ---------------------------------------------------------------------------
// ChatPage – full-page chat interface (mobile fallback)
// ---------------------------------------------------------------------------

export default function ChatPage() {
  const { messages, sendMessage, isStreaming, clearMessages } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col lg:h-[calc(100vh-7rem)]">
      {/* Page header */}
      <div className="flex flex-shrink-0 items-center justify-between pb-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Chat</h1>
          <p className="mt-1 text-sm text-surface-400">
            Ask your AI fantasy football assistant anything
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="btn-ghost flex items-center gap-2 text-xs"
            aria-label="Clear chat history"
          >
            <TrashIcon className="h-4 w-4" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="card flex flex-1 flex-col overflow-hidden p-0">
        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-4 py-4 sm:px-6"
          role="list"
          aria-label="Chat messages"
        >
          {isEmpty ? (
            <div className="flex h-full flex-col items-center justify-center gap-6 px-4">
              {/* Welcome state */}
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-primary-800/50">
                <SparklesIcon className="h-10 w-10 text-accent-400" />
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold text-surface-100">
                  Fantasy Football AI Assistant
                </h3>
                <p className="mx-auto mt-2 max-w-md text-sm text-surface-400">
                  Get instant advice on your lineup, waiver wire targets, trade
                  evaluations, and more. Powered by AI analysis of your league
                  data.
                </p>
              </div>

              {/* Suggested question chips */}
              <div className="flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    onClick={() => sendMessage(question)}
                    disabled={isStreaming}
                    className="rounded-full border border-surface-600/50 bg-surface-800/50 px-4 py-2.5 text-sm font-medium text-surface-300 transition-colors hover:border-accent-500/40 hover:bg-surface-800 hover:text-accent-400 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-4">
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

        {/* Input */}
        <div className="mx-auto w-full max-w-3xl">
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      </div>
    </div>
  );
}
