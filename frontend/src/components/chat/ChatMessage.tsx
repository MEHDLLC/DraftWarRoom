import ReactMarkdown from "react-markdown";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function ClaudeIcon({ className }: { className?: string }) {
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
      <path d="M12 2a4 4 0 0 0-4 4v2H6a4 4 0 0 0-4 4v2a4 4 0 0 0 4 4h2v2a4 4 0 0 0 8 0v-2h2a4 4 0 0 0 4-4v-2a4 4 0 0 0-4-4h-2V6a4 4 0 0 0-4-4z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Typing indicator
// ---------------------------------------------------------------------------

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-2" aria-label="Typing">
      <span
        className="inline-block h-2 w-2 animate-bounce rounded-full bg-surface-400"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="inline-block h-2 w-2 animate-bounce rounded-full bg-surface-400"
        style={{ animationDelay: "150ms" }}
      />
      <span
        className="inline-block h-2 w-2 animate-bounce rounded-full bg-surface-400"
        style={{ animationDelay: "300ms" }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// ChatMessage
// ---------------------------------------------------------------------------

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function ChatMessage({
  role,
  content,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={[
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start",
      ].join(" ")}
      role="listitem"
    >
      {/* Assistant avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-800">
          <ClaudeIcon className="h-4 w-4 text-accent-400" />
        </div>
      )}

      {/* Message bubble */}
      <div
        className={[
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed sm:max-w-[70%]",
          isUser
            ? "rounded-br-md bg-accent-500 text-surface-900"
            : "rounded-bl-md border border-surface-700/50 bg-surface-700/50 text-surface-100",
        ].join(" ")}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : content ? (
          <div className="prose prose-sm prose-invert max-w-none [&_a]:text-accent-400 [&_a]:underline [&_code]:rounded [&_code]:bg-surface-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-xs [&_h1]:text-base [&_h1]:text-surface-100 [&_h2]:text-sm [&_h2]:text-surface-100 [&_h3]:text-sm [&_h3]:text-surface-200 [&_li]:text-surface-200 [&_ol]:pl-4 [&_p]:text-surface-200 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-surface-800 [&_pre]:p-3 [&_strong]:text-surface-100 [&_ul]:pl-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : isStreaming ? (
          <TypingIndicator />
        ) : null}

        {/* Show typing indicator at the end when streaming and there is content */}
        {isStreaming && content && !isUser && (
          <div className="mt-1 border-t border-surface-600/30 pt-1">
            <TypingIndicator />
          </div>
        )}
      </div>

      {/* Spacer for user messages (to match assistant avatar width) */}
      {isUser && <div className="w-8 flex-shrink-0" />}
    </div>
  );
}
