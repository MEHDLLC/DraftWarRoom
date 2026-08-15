import { useState, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { chatApi, type ChatMessage } from "@/api/client";

// ---------------------------------------------------------------------------
// useChat – manages chat state, message sending, and streaming
// ---------------------------------------------------------------------------

interface UseChatReturn {
  messages: ChatMessage[];
  sendMessage: (text: string) => void;
  isStreaming: boolean;
  cancelStream: () => void;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingContentRef = useRef("");

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isStreaming) return;

      // Add the user message
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };

      // Create a placeholder for the assistant response
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);
      streamingContentRef.current = "";

      // Set up abort controller for cancellation
      const controller = new AbortController();
      abortControllerRef.current = controller;

      chatApi.sendMessage(
        text.trim(),
        {
          onChunk: (chunk: string) => {
            streamingContentRef.current += chunk;
            const updatedContent = streamingContentRef.current;
            setMessages((prev) => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  content: updatedContent,
                };
              }
              return updated;
            });
          },
          onDone: () => {
            setIsStreaming(false);
            abortControllerRef.current = null;
          },
          onError: () => {
            setIsStreaming(false);
            abortControllerRef.current = null;
            // Update the assistant message with an error notice
            setMessages((prev) => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (
                lastIdx >= 0 &&
                updated[lastIdx].role === "assistant" &&
                !updated[lastIdx].content
              ) {
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  content:
                    "Sorry, something went wrong. Please try again.",
                };
              }
              return updated;
            });
          },
        },
        controller.signal,
      );
    },
    [isStreaming],
  );

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    abortControllerRef.current = null;
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, sendMessage, isStreaming, cancelStream, clearMessages };
}

// ---------------------------------------------------------------------------
// useChatHistory – fetches persisted chat history from the API
// ---------------------------------------------------------------------------

export function useChatHistory() {
  return useQuery({
    queryKey: ["chat", "history"],
    queryFn: chatApi.getHistory,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1,
  });
}
