import { useQuery } from "@tanstack/react-query";
import { scheduleApi } from "@/api/client";

export function useStrengthOfSchedule() {
  return useQuery({
    queryKey: ["schedule", "sos"],
    queryFn: scheduleApi.getSos,
    staleTime: 1000 * 60 * 10,
    retry: 2,
  });
}

export function usePlayoffSchedule() {
  return useQuery({
    queryKey: ["schedule", "playoffs"],
    queryFn: scheduleApi.getPlayoffs,
    staleTime: 1000 * 60 * 10,
    retry: 2,
  });
}

export function useByeWeeks() {
  return useQuery({
    queryKey: ["schedule", "byes"],
    queryFn: scheduleApi.getByes,
    staleTime: 1000 * 60 * 10,
    retry: 2,
  });
}
