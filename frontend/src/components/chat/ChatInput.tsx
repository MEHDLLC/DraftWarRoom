import { useState, useRef, useCallback, useEffect } from "react";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function SendIcon({ className }: { className?: string }) {
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
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// ChatInput
// ---------------------------------------------------------------------------

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize the textarea based on content
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    // Clamp to a max height of ~6 lines
    const maxHeight = 150;
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [text, adjustHeight]);

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    // Reset height after clearing
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    });
  }, [text, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, newline on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSend = text.trim().length > 0 && !disabled;

  return (
    <div className="flex items-end gap-2 border-t border-surface-700/50 bg-surface-800/80 px-4 py-3">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Waiting for response..." : "Ask about your fantasy team..."}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-xl border border-surface-600/50 bg-surface-900 px-4 py-2.5 text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors focus:border-accent-500/50 focus:ring-1 focus:ring-accent-500/30 disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Chat message input"
      />
      <button
        onClick={handleSubmit}
        disabled={!canSend}
        className={[
          "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl transition-all",
          canSend
            ? "bg-accent-500 text-surface-900 hover:bg-accent-400 active:scale-95"
            : "cursor-not-allowed bg-surface-700 text-surface-500",
        ].join(" ")}
        aria-label="Send message"
      >
        <SendIcon className="h-4.5 w-4.5" />
      </button>
    </div>
  );
}
