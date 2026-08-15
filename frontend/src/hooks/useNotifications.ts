import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationApi } from "@/api/client";

// ---------------------------------------------------------------------------
// useNotifications – fetches all notifications
// ---------------------------------------------------------------------------

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: notificationApi.getAll,
    staleTime: 1000 * 60, // 1 minute
    retry: 2,
  });
}

// ---------------------------------------------------------------------------
// useUnreadCount – fetches unread notification count, polls every 30s
// ---------------------------------------------------------------------------

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: notificationApi.getUnreadCount,
    staleTime: 1000 * 15, // 15 seconds
    refetchInterval: 1000 * 30, // poll every 30 seconds
    retry: 1,
  });
}

// ---------------------------------------------------------------------------
// useMarkRead – mutation to mark a notification as read
// ---------------------------------------------------------------------------

export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => notificationApi.markRead(id),
    onSuccess: () => {
      // Invalidate both notifications list and unread count
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
